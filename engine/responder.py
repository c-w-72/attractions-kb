"""
问答生成器
- 结构化场景回答
- 多轮对话上下文管理
- 动态跟进问题生成
"""

import random
import os
import streamlit as st
from engine.intent import SCENARIO_LABELS
from engine.llm import get_llm, make_prompt
from engine.retriever import QUERY_EXPANSIONS


# ===== 跟进问题模板 =====

FOLLOWUP_TEMPLATES = {
    "basic_info": [
        "去{name}玩有什么推荐路线吗？",
        "{name}附近有什么特色美食？",
        "去{name}交通方便吗？怎么到达？",
        "{name}有什么历史文化背景？",
        "{name}需要玩多长时间？",
    ],
    "travel_guide": [
        "{name}的门票多少钱？开放时间呢？",
        "去{name}住在哪里比较方便？",
        "{name}周边有什么好吃的推荐？",
        "{name}有什么文化特色？",
        "{name}适合什么季节去？",
    ],
    "transport": [
        "{name}有哪些必看的景点？",
        "去{name}玩需要多长时间？",
        "{name}附近有什么好吃的？",
        "{name}有什么历史故事？",
        "{name}的门票多少钱？",
    ],
    "culture": [
        "{name}的门票和开放时间是？",
        "去{name}有什么游玩攻略？",
        "{name}附近住哪里方便？",
        "{name}有什么特色美食？",
        "{name}的最佳旅游季节是？",
    ],
    "food": [
        "{name}的基础信息介绍一下",
        "去{name}有什么游玩攻略？",
        "{name}有什么文化特色？",
        "{name}附近交通住宿方便吗？",
        "{name}有什么必看景点？",
    ],
    "general": [
        "介绍一下{name}的门票和开放时间",
        "去{name}有什么游玩攻略？",
        "{name}有什么特色美食？",
        "{name}有什么文化历史背景？",
        "去{name}交通住宿方便吗？",
    ],
}


class ConversationContext:
    """多轮对话上下文管理"""

    def __init__(self):
        self.history = []
        self.current_attraction = None
        self.current_province = None
        self.current_category = None
        self.current_scenario = None
        self.turn_count = 0

    def update(self, entities: dict, answer_info: dict):
        self.turn_count += 1
        if entities.get("attraction_name"):
            self.current_attraction = entities["attraction_name"]
        if entities.get("province"):
            self.current_province = entities["province"]
        if entities.get("category"):
            self.current_category = entities["category"]
        if entities.get("scenario"):
            self.current_scenario = entities["scenario"]

        self.history.append({
            "turn": self.turn_count,
            "entities": entities,
            "answer_info": answer_info,
        })
        # 只保留最近6轮
        if len(self.history) > 6:
            self.history = self.history[-6:]

    def get_last_entities(self) -> dict:
        if self.history:
            return self.history[-1].get("entities", {})
        return {}

    def get_attraction(self):
        return self.current_attraction

    def get_province(self):
        return self.current_province

    def to_dict(self):
        return {
            "attraction_name": self.current_attraction,
            "province": self.current_province,
            "category": self.current_category,
            "scenario": self.current_scenario,
        }


class Responder:
    """问答生成器"""

    def __init__(self, retriever):
        self.retriever = retriever
        self.context = ConversationContext()
        self.llm = get_llm()

    @property
    def use_llm(self) -> bool:
        return self.llm is not None and st.session_state.get("llm_enabled", False)

    def _llm_answer(self, query: str, entities: dict) -> dict:
        """LLM 生成回答（含跟进问题）"""
        # 动态检索相关景点上下文，而非固定传前 N 个
        results = self.retriever.search(query, top_k=8)
        relevant = [att for att, _ in results] if results else self.retriever.attractions[:5]
        messages = make_prompt(query, entities, relevant)
        result = self.llm.chat(messages)
        if result:
            answer_info = {"type": "llm", "attraction_name": entities.get("attraction_name")}
            followups = self._generate_context_followups(answer_info)
            self.context.update(entities, answer_info)
            return {"answer": result, "answer_info": answer_info, "followups": followups, "context": self.context.to_dict()}

        # LLM 失败时回退（单次消费 generator，避免上下文重复更新）
        answer_info = {}
        followups = []
        content_parts = []
        for chunk_type, chunk_content in self.generate_stream(query, entities):
            if chunk_type == "content":
                content_parts.append(chunk_content)
            elif chunk_type == "followups":
                followups = chunk_content
            elif chunk_type == "answer_info":
                answer_info = chunk_content

        return {
            "answer": "\n\n".join(content_parts) if content_parts else "暂无匹配信息",
            "answer_info": answer_info,
            "followups": followups,
            "context": self.context.to_dict(),
        }

    def generate_stream(self, query: str, entities: dict):
        """生成回答（流式，逐段 yield）"""
        yield ("status", "🔍 正在分析你的问题...")
        try:
            yield from self._generate_stream_inner(query, entities)
        except Exception as e:
            logger.exception("generate_stream 异常: %s", e)
            yield ("content", "### 😅 抱歉\n处理你的问题时出现异常，请稍后重试或换个问法。")
            yield ("followups", [])
            yield ("answer_info", {})

    def _generate_stream_inner(self, query: str, entities: dict):
        """生成回答内部逻辑（实际处理）"""
        scenario = entities.get("scenario", "general")
        att_name = entities.get("attraction_name")
        province = entities.get("province")
        category = entities.get("category")
        season = entities.get("season")

        att = self.retriever.get_by_name(att_name) if att_name else None

        answer_parts = []
        answer_info = {}

        if att:
            answer_info["type"] = "single"
            answer_info["attraction_id"] = att["id"]
            answer_info["attraction_name"] = att["name"]
            answer_info["province"] = att["province"]
            answer_info["category"] = att["category"]

            yield ("status", f"📖 正在整理 {att['name']} 的信息...")

            label, css = SCENARIO_LABELS.get(scenario, SCENARIO_LABELS["general"])
            answer_parts.append(f"### {att['name']}")
            answer_parts.append(self._format_short(att))
            answer_parts.append("")
            answer_parts.append(f'<span class="scenario-badge {css}">{label}</span>')

            content = self._get_scenario_content(att, scenario, season)
            answer_parts.append(content)
            answer_info["scenario"] = scenario

            yield ("content", "\n\n".join(answer_parts))

        elif category and not province:
            answer_info["type"] = "category_list"
            answer_info["category"] = category
            candidates = self.retriever.get_by_category(category)
            yield ("status", f"📂 正在查找 {category} 类景点...")

            if season:
                candidates = [a for a in candidates
                              if season in a.get("best_season", "")]
                answer_parts.append(f"### 🌤️ 适合{season}的{category}景点推荐\n")
            else:
                answer_parts.append(f"### 📂 {category}景点推荐\n")

            candidates.sort(key=lambda x: x.get("rating", 0), reverse=True)
            for i, a in enumerate(candidates[:6], 1):
                answer_parts.append(self._format_list_item(i, a))
                answer_parts.append("")

            answer_info["province"] = candidates[0]["province"] if candidates else None
            answer_info["category"] = category
            yield ("content", "\n\n".join(answer_parts))

        elif province:
            answer_info["type"] = "province_list"
            answer_info["province"] = province
            candidates = self.retriever.get_by_province(province)
            yield ("status", f"🗺️ 正在查找 {province} 的景点...")

            if category:
                candidates = [a for a in candidates if a["category"] == category]
            if season:
                candidates = [a for a in candidates
                              if season in a.get("best_season", "")]

            candidates.sort(key=lambda x: x.get("rating", 0), reverse=True)
            answer_parts.append(f"### 🗺️ {province}景点推荐\n")

            for i, a in enumerate(candidates[:6], 1):
                answer_parts.append(self._format_list_item(i, a))
                answer_parts.append("")

            yield ("content", "\n\n".join(answer_parts))

        else:
            yield ("status", "🔎 正在检索相关景点...")
            results = self.retriever.search(query, top_k=8)

            # 概念查询（看海/爬山/避暑等）→ 直接显示推荐列表
            is_concept = query.strip().lower() in QUERY_EXPANSIONS

            if results and results[0][1] > 0.12 and not is_concept:
                top_att = results[0][0]
                answer_info["type"] = "single"
                answer_info["attraction_id"] = top_att["id"]
                answer_info["attraction_name"] = top_att["name"]
                answer_info["province"] = top_att["province"]
                answer_info["category"] = top_att["category"]

                label, css = SCENARIO_LABELS.get(scenario, SCENARIO_LABELS["general"])
                answer_parts.append(f"### {top_att['name']}")
                answer_parts.append(self._format_short(top_att))
                answer_parts.append("")
                answer_parts.append(f'<span class="scenario-badge {css}">{label}</span>')
                answer_parts.append(self._get_scenario_content(top_att, scenario, season))
                answer_info["scenario"] = scenario
                yield ("content", "\n\n".join(answer_parts))
            elif results:
                answer_info["type"] = "search_list"
                answer_info["top_names"] = [a["name"] for a, _ in results[:4]]
                if is_concept:
                    answer_parts.append(f"### 🎯 「{query}」相关景点推荐\n")
                else:
                    answer_parts.append("### 🏞️ 为你推荐以下景点\n")
                for i, (a, s) in enumerate(results[:8], 1):
                    answer_parts.append(self._format_list_item(i, a))
                    answer_parts.append("")
                yield ("content", "\n\n".join(answer_parts))
            else:
                answer_info["type"] = "no_result"
                # 尝试拼音纠错兜底
                fuzzy = self.retriever.fuzzy_search(query, top_k=3)
                if fuzzy:
                    yield ("status", "💡 未找到直接匹配，试试这些景点：")
                    answer_parts.append("### 💡 你可能想找的是：\n")
                    for i, (a, s) in enumerate(fuzzy, 1):
                        answer_parts.append(
                            f"**{i}. {a['name']}** — {a['province']} {a.get('city', '')}\n"
                            f"📝 {a.get('description', '')[:120]}"
                        )
                        answer_parts.append("")
                    yield ("content", "\n\n".join(answer_parts))
                else:
                    answer_parts.append("### 😅 抱歉")
                    answer_parts.append("没有找到匹配的景点信息，请换个关键词试试。\n")
                    answer_parts.append("💡 **试试这些关键词：**")
                    answer_parts.append("- 景点名称：故宫、黄山、九寨沟、丽江...")
                    answer_parts.append("- 省份/城市：北京有什么好玩的、成都美食...")
                    answer_parts.append("- 场景：避暑、爬山、看海、古镇、美食...")
                    yield ("content", "\n\n".join(answer_parts))

        # 生成跟进问题
        followups = self._generate_context_followups(answer_info)
        yield ("followups", followups)
        yield ("answer_info", answer_info)

        # 更新上下文
        self.context.update(entities, answer_info)

    def answer(self, query: str, entities: dict) -> dict:
        """生成完整回答（非流式），返回 {"content": str, "followups": list}"""
        content_parts = []
        followups = []
        for chunk_type, chunk_content in self.generate_stream(query, entities):
            if chunk_type == "content":
                content_parts.append(chunk_content)
            elif chunk_type == "followups":
                followups = chunk_content
        return {
            "content": "\n\n".join(content_parts) if content_parts else "暂无匹配信息",
            "followups": followups,
        }

    def generate(self, query: str, entities: dict) -> dict:
        """生成回答（非流式，兼容旧接口）"""
        if self.use_llm:
            return self._llm_answer(query, entities)

        content_parts = []
        answer_info = {}
        followups = []
        for chunk_type, chunk_content in self.generate_stream(query, entities):
            if chunk_type == "content":
                content_parts.append(chunk_content)
            elif chunk_type == "followups":
                followups = chunk_content
            elif chunk_type == "answer_info":
                answer_info = chunk_content

        return {
            "answer": "\n\n".join(content_parts) if content_parts else "暂无匹配信息",
            "answer_info": answer_info,
            "followups": followups,
            "context": self.context.to_dict(),
        }

    def _get_scenario_content(self, att: dict, scenario: str, season: str = None) -> str:
        """获取场景内容"""
        content = att.get(scenario, "")

        if scenario == "general" or not content:
            parts = []
            parts.append(f"📝 {att.get('description', '')[:200]}")
            if att.get("basic_info"):
                parts.append("")
                parts.append("**📍 基础信息**")
                parts.append(att["basic_info"][:200])
            if att.get("travel_guide"):
                parts.append("")
                parts.append(f"**🗺️ 游玩攻略**")
                guide = att["travel_guide"]
                if season:
                    season_lines = [l for l in guide.split("\n") if season in l]
                    if season_lines:
                        guide = "\n".join(season_lines)
                parts.append(guide[:200])
            if att.get("culture"):
                parts.append("")
                parts.append(f"**🎭 文化特色**")
                parts.append(att["culture"][:250])
            if att.get("food"):
                parts.append("")
                parts.append(f"**🍜 美食推荐**")
                parts.append(att["food"])
            if att.get("transport"):
                parts.append("")
                parts.append(f"**🚗 交通住宿**")
                parts.append(att["transport"])
            return "\n".join(parts)

        if season:
            lines = content.split("\n")
            season_lines = [l for l in lines if season in l or "季节" in l]
            if season_lines:
                content = "\n".join(season_lines)

        return content

    def _generate_context_followups(self, info: dict) -> list:
        """上下文感知的跟进问题生成"""
        name = info.get("attraction_name")
        province = info.get("province")
        category = info.get("category")
        scenario = info.get("scenario", "general")
        qtype = info.get("type")

        questions = []
        ctx = self.context

        if name:
            # 基于当前景点的跟进
            templates = FOLLOWUP_TEMPLATES.get(scenario, FOLLOWUP_TEMPLATES["general"])
            for t in templates:
                q = t.replace("{name}", name)
                if q not in questions:
                    questions.append(q)

            # 添加上下文关联景点推荐（如果之前问过其他景点，做对比）
            prev_att = None
            for h in reversed(ctx.history):
                en = h.get("entities", {})
                if en.get("attraction_name") and en["attraction_name"] != name:
                    prev_att = en["attraction_name"]
                    break
            if prev_att:
                questions.append(f"{name}和{prev_att}哪个更值得去？")

            # 关联景点推荐
            att = self.retriever.get_by_name(name)
            if att:
                related = self.retriever.get_related(att, top_n=3)
                for r in related[:2]:
                    questions.append(f"{r['name']}有什么好玩的？")

            random.shuffle(questions)
            questions = questions[:4]

        elif province:
            # 基于省份的跟进，结合历史对话
            prev_cat = ctx.current_category
            if prev_cat:
                questions = [
                    f"{province}有哪些{prev_cat}景点？",
                    f"去{province}旅游有什么美食推荐？",
                    f"{province}有什么特色文化？",
                    f"{province}的最佳旅游季节是什么时候？",
                ]
            else:
                questions = [
                    f"{province}最值得去的景点是哪个？",
                    f"去{province}旅游有什么美食推荐？",
                    f"{province}有什么特色文化？",
                    f"{province}的最佳旅游季节是什么时候？",
                ]

        elif category:
            cat_followups = {
                "自然风光": ["适合爬山看日出的景点推荐", "夏季避暑去哪里比较好？"],
                "历史文化": ["有哪些免费的历史文化景点？", "带孩子去的历史文化景点推荐"],
                "主题乐园": ["适合亲子的主题乐园", "主题乐园一日游攻略"],
                "都市风情": ["适合拍照的城市地标", "城市夜景观赏推荐"],
                "现代建筑": ["有哪些现代建筑值得看？", "城市观光推荐"],
            }
            questions = cat_followups.get(category, [])
            # 结合省份上下文
            prev_prov = ctx.current_province
            if prev_prov:
                questions.append(f"{prev_prov}有哪些推荐景点？")
            else:
                questions.append("推荐几个评分最高的景点")
            questions.append("有哪些免费的景点推荐？")

        elif qtype == "search_list":
            # 从历史中获取搜索结果的景点名，生成具体跟进问题
            top_names = []
            for h in reversed(ctx.history):
                ai = h.get("answer_info", {})
                if ai.get("type") == "search_list" and ai.get("top_names"):
                    top_names = ai["top_names"]
                    break
            if top_names:
                questions = [f"{n}有什么好玩的？" for n in top_names[:3]]
                questions.append("这些景点哪个最值得去？")
            else:
                questions = [
                    "这些景点有哪些必去的？",
                    "推荐评分最高的景点",
                    "有哪些免费景点？",
                    "适合带孩子去的景点推荐",
                ]

        return questions[:4]

    def get_related_questions(self, att_name: str, scenario: str = None) -> list:
        """获取关联景点推荐问题"""
        att = self.retriever.get_by_name(att_name)
        if not att:
            return []

        related = self.retriever.get_related(att, top_n=3)
        questions = []
        for r in related:
            questions.append(f"{r['name']}有什么好玩的？")
        return questions

    @staticmethod
    def _format_short(att: dict) -> str:
        stars = "⭐" * int(round(att.get("rating", 0) or 0))
        return (
            f"📍 {att['province']} {att.get('city', '')} | "
            f"📂 {att['category']} | "
            f"{stars} {att.get('rating', '')} | "
            f"🎫 {att.get('ticket', '')}"
        )

    @staticmethod
    def _format_list_item(i: int, att: dict) -> str:
        stars = "⭐" * int(round(att.get("rating", 0) or 0))
        return (
            f"**{i}. {att['name']}** {stars} {att.get('rating', '')}\n"
            f"📍 {att['province']} {att.get('city', '')} | "
            f"📂 {att['category']} | 🎫 {att.get('ticket', '')}\n"
            f"📝 {att.get('description', '')[:120]}..."
        )
