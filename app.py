"""
中国旅游景点知识库问答系统
- 五大咨询场景 + 多轮对话 + 跟进推送
- 语义检索 + 行程规划 + 附近景点
- 景点地图 + 对比 + 收藏 + 费用估算 + 天气 + 图片
"""

import streamlit as st
import random
import json
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("app")

from engine.retriever import AttractionRetriever
from engine.intent import IntentEngine
from engine.responder import Responder
from engine.itinerary import parse_itinerary_query, generate_itinerary
from engine.geo import get_nearby_attractions
from engine.external import fetch_weather, parse_weather, fetch_image
from data.cost_data import estimate_trip_cost

st.set_page_config(
    page_title="中国旅游景点知识库",
    page_icon="🏯",
    layout="wide",
)

FAVORITES_FILE = os.path.join(os.path.dirname(__file__), "data", "favorites.json")


# ===== 收藏管理 =====

def load_favorites():
    if not os.path.exists(FAVORITES_FILE):
        return {"favorites": [], "notes": {}}
    with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_favorites(data):
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def toggle_favorite(att_name: str):
    data = load_favorites()
    if att_name in data["favorites"]:
        data["favorites"].remove(att_name)
        data["notes"].pop(att_name, None)
    else:
        data["favorites"].append(att_name)
    save_favorites(data)
    return att_name in data["favorites"]


def is_favorite(att_name: str) -> bool:
    return att_name in load_favorites()["favorites"]


def save_note(att_name: str, note: str):
    data = load_favorites()
    if note:
        data["notes"][att_name] = note
    else:
        data["notes"].pop(att_name, None)
    save_favorites(data)


# ===== 初始化引擎 =====

@st.cache_resource
def init_retriever():
    # 设置 HuggingFace 镜像（国内访问）
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

    # 启动阶段1：加载数据
    progress = st.progress(0, text="📂 加载景点数据...")
    r = AttractionRetriever()
    progress.progress(30, text="🔧 构建 TF-IDF 索引...")

    # 阶段2：构建索引（语义模型懒加载，先建 TF-IDF）
    r.build_index(use_semantic=False)
    progress.progress(60, text="🧠 加载语义检索模型（首次较慢）...")

    # 阶段3：后台加载语义模型（非阻塞显示）
    try:
        r._try_build_semantic()
    except Exception:
        pass
    progress.progress(100, text="✅ 加载完成！")
    progress.empty()
    return r


def init_session():
    if "retriever" not in st.session_state:
        retriever = init_retriever()
        st.session_state.retriever = retriever
        st.session_state.intent_engine = IntentEngine(retriever)
        st.session_state.responder = Responder(retriever)
        st.session_state.messages = []
        st.session_state.followups = []

    if "welcome_shown" not in st.session_state:
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "## 🏯 你好！我是中国旅游景点助手\n\n"
                "我可以帮你查询全国各地的景点信息，覆盖五大咨询场景：\n\n"
                "| 场景 | 说明 |\n"
                "|------|------|\n"
                "| 📍 **基础信息** | 开放时间、门票价格、建议游玩时长 |\n"
                "| 🗺️ **游玩攻略** | 最佳路线、游览重点、装备建议 |\n"
                "| 🚗 **交通住宿** | 外部交通、当地交通、住宿推荐 |\n"
                "| 🎭 **民俗文化** | 历史文化、特色节庆、民俗风情 |\n"
                "| 🍜 **美食特产** | 特色美食、特产购物、美食街区 |\n\n"
                "**试试这样问我：**\n"
                "- 北京有哪些必去的景点？\n"
                "- 黄山怎么玩比较好？\n"
                "- 北京3日游有什么推荐？\n"
                "- 去鼓浪屿住哪里方便？\n"
                "- 西安有什么好吃的？"
            ),
        })
        st.session_state.welcome_shown = True


init_session()

retriever = st.session_state.retriever
intent_engine = st.session_state.intent_engine
responder = st.session_state.responder


# ===== CSS =====

st.markdown("""
<style>
    .main-header { font-size: 1.6rem; font-weight: 700; margin-bottom: 0.5rem; color: #000; }
    .sub-header { font-size: 1.1rem; color: #444; margin-bottom: 1.5rem; }
    .attraction-card {
        padding: 1.2rem; border-radius: 10px; border: 1px solid #d0d0d0;
        margin-bottom: 1rem; background: #fff;
    }
    .attraction-card h3 { margin-top: 0; color: #000; }
    .tag {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: 0.8rem; margin-right: 6px; background: #fff; color: #333;
        border: 1px solid #d0d0d0;
    }
    .tag-rating { color: #e67e22; border-color: #f0d0a0; }
    .tag-food { color: #c62828; border-color: #e0b0b0; }
    .tag-culture { color: #6a1b9a; border-color: #c0a0d0; }
    .tag-transport { color: #00695c; border-color: #a0c0b0; }
    .tag-travel { color: #2e7d32; border-color: #a0c0a0; }
    .tag-info { color: #0d47a1; border-color: #a0b0d0; }
    .tag-fav { color: #e91e63; border-color: #e0a0b0; }
    .compare-table { width: 100%; border-collapse: collapse; }
    .compare-table th, .compare-table td {
        border: 1px solid #ddd; padding: 8px; vertical-align: top;
    }
    .compare-table th { background: #f0f2f6; font-weight: 600; text-align: center; color: #000; }
    .compare-table td { font-size: 0.9rem; }
    .weather-card {
        padding: 0.8rem; border-radius: 10px; border: 1px solid #d0d0d0;
        background: #fff; color: #000; margin-bottom: 1rem;
    }
    .weather-card .temp { font-size: 2rem; font-weight: 700; color: #000; }
    .weather-card .desc { font-size: 1rem; color: #333; }
    .itinerary-card {
        padding: 1rem; border-radius: 10px; border: 1px solid #d0d0d0;
        background: #fff; margin-bottom: 0.8rem;
    }
    .cost-card {
        padding: 0.8rem; border-radius: 10px; border: 1px solid #d0d0d0;
        background: #fff; margin-bottom: 0.5rem;
    }
    .stButton button { font-size: 0.85rem; }

    /* st.chat_message 中文显示优化 */
    div[data-testid="stChatMessage"] {
        font-size: 0.95rem; line-height: 1.7;
    }
    div[data-testid="stChatMessageContent"] p {
        margin-bottom: 0.4rem;
    }
    div[data-testid="stChatMessageContent"] table {
        font-size: 0.85rem;
    }

    /* 移动端响应式 */
    @media (max-width: 768px) {
        .stButton button { font-size: 0.75rem; padding: 0.2rem 0.4rem; }
        .tag { font-size: 0.7rem; padding: 1px 6px; }
        .attraction-card { padding: 0.8rem; }
    }
</style>
""", unsafe_allow_html=True)


# ===== 消息处理 =====

def ask_question(query: str):
    """从任意页面提交问题并跳转到智能问答"""
    if query.strip():
        st.session_state.messages.append({"role": "user", "content": query.strip()})
        st.session_state.nav_selected = "💬 智能问答"
        st.rerun()


def display_followups(followups: list):
    if not followups:
        return
    st.markdown("##### 💬 你可能还想了解：")
    cols = st.columns(2)
    for i, q in enumerate(followups):
        with cols[i % 2]:
            if st.button(q, use_container_width=True, key=f"fu_{hash(q)}_{i}"):
                ask_question(q)


# ===== 侧边栏 =====

with st.sidebar:
    st.markdown("## 🏯 旅游知识库")

    # 导航菜单
    nav_categories = {
        "🔍 发现": ["🔍 景点搜索", "🎲 随机推荐"],
        "🗺️ 浏览": ["🗺️ 按省份浏览", "📂 按分类浏览", "🗺️ 景点地图", "📊 景点对比"],
        "🛠️ 规划": ["🗺️ 行程规划", "💰 费用估算", "⭐ 我的收藏"],
        "📊 系统": ["📊 数据概览"],
    }

    selected = st.session_state.get("nav_selected", "💬 智能问答")
    for group_label, items in nav_categories.items():
        st.markdown(f"**{group_label}**")
        for item in items:
            is_active = (selected == item)
            btn_type = "primary" if is_active else "secondary"
            if st.button(item, key=f"nav_{item}", use_container_width=True, type=btn_type):
                st.session_state.nav_selected = item
                st.rerun()
    page = st.session_state.get("nav_selected", "💬 智能问答")

    st.markdown("---")
    stats = retriever.get_stats()
    fav_count = len(load_favorites()["favorites"])
    st.markdown(f"⭐ **已收藏**: {fav_count} 个景点")
    with st.expander("📊 数据统计", expanded=False):
        st.markdown(f"- **景点总数**: {stats['total']} 个")
        st.markdown(f"- **覆盖省份**: {stats['provinces']} 个")
        has_semantic = hasattr(retriever, "_semantic_embedder")
        st.markdown(f"- **语义检索**: {'✅ 已启用' if has_semantic else '❌ 未启用'}")
        for cat in stats["categories"]:
            cnt = len(retriever.get_by_category(cat))
            st.markdown(f"- {cat}: {cnt}个")

    st.markdown("---")
    st.caption("💡 问答页面支持「北京3日游」等行程规划问题")


# ===== 页面：智能问答 =====

def render_qa_page():
    st.markdown('<div class="main-header">💬 智能问答</div>', unsafe_allow_html=True)

    # 聊天历史
    for msg in st.session_state.messages:
        avatar = "🏯" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # 有未处理的用户消息 → 生成回答
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_query = st.session_state.messages[-1]["content"]

        with st.chat_message("assistant", avatar="🏯"):
            with st.spinner("🔍 思考中..."):
                # 行程规划检测
                itinerary_info = parse_itinerary_query(last_query)
                if itinerary_info:
                    ctx = responder.context.to_dict() if responder.context else None
                    entities = intent_engine.extract_all(last_query, ctx)
                    province = entities.get("province")
                    city = entities.get("city")
                    days = itinerary_info["days"]
                    plan = generate_itinerary(
                        retriever.attractions, last_query,
                        province=province, city=city, days=days,
                    )
                    if plan:
                        content = plan["itinerary"]
                        followups = [
                            f"这个行程大概要花多少钱？",
                            f"{province or city or ''}还有哪些值得去的景点？",
                            f"{province or city or ''}有什么特色美食？",
                        ]
                        st.markdown(content)
                        st.session_state.messages.append({
                            "role": "assistant", "content": content, "followups": followups,
                        })
                        st.rerun()

                # 标准问答
                ctx = responder.context.to_dict() if responder.context else None
                entities = intent_engine.extract_all(last_query, ctx)
                try:
                    result = responder.generate(last_query, entities)
                except Exception as e:
                    with open(os.path.join(os.path.dirname(__file__), "error.log"), "a") as f:
                        import traceback
                        f.write(f"generate() 异常: {e}\n{traceback.format_exc()}\n")
                    result = {"answer": "抱歉，处理问题时出现异常，请重试。", "followups": []}

            st.markdown(result["answer"])

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "followups": result.get("followups", []),
        })
        st.rerun()

    # 跟进问题
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        followups = st.session_state.messages[-1].get("followups", [])
        if followups:
            display_followups(followups)

    # 输入框
    prompt = st.chat_input("输入你的旅游问题...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # 首次进入显示示例
    if len(st.session_state.messages) <= 1:
        st.markdown("---")
        st.markdown("##### 💡 试试这些示例问题：")
        examples = [
            "北京有哪些必去的景点？",
            "黄山怎么玩比较好？",
            "北京3日游有什么推荐？",
            "西安有什么好吃的？",
            "丽江古城有什么文化特色？",
            "九寨沟门票多少钱？",
        ]
        cols = st.columns(3)
        for i, example in enumerate(examples):
            with cols[i % 3]:
                if st.button(example, use_container_width=True, key=f"ex_{i}"):
                    st.session_state.messages.append({"role": "user", "content": example})
                    st.rerun()

    # 底部操作栏
    if len(st.session_state.messages) > 1:
        st.markdown("---")
        cols = st.columns([1, 1, 6])
        with cols[0]:
            if st.button("🗑️ 清除对话", use_container_width=True):
                st.session_state.messages = []
                st.session_state.welcome_shown = False
                st.session_state.responder = Responder(retriever)
                st.rerun()
        with cols[1]:
            if st.button("🎲 换个推荐", use_container_width=True):
                rand_att = random.choice(retriever.attractions)
                st.session_state.messages.append({"role": "user", "content": f"介绍一下{rand_att['name']}"})
                st.rerun()

# ===== 页面：搜索/省份/分类/地图/对比/随机/概览 =====

def render_search_page():
    st.markdown('<div class="main-header">🔍 景点搜索</div>', unsafe_allow_html=True)

    # 搜索历史
    if "search_history" not in st.session_state:
        st.session_state.search_history = []
    if "search_counts" not in st.session_state:
        st.session_state.search_counts = {}  # count per attraction

    # 搜索栏 + 语义开关 并排
    search_col, toggle_col = st.columns([5, 1])
    with search_col:
        query = st.text_input("关键词", placeholder="例如：长城、古镇、避暑、看海...",
                              label_visibility="collapsed", key="search_query_input")
    with toggle_col:
        use_hybrid = st.toggle("语义搜索", value=False,
                               help="启用语义融合检索（更精准）")

    # 自动补全提示（基于景点名称前缀匹配）
    if query and len(query) >= 2:
        ql = query.lower()
        suggestions = [a["name"] for a in retriever.attractions
                       if ql in a["name"].lower() or any(ql in w for w in a["name"].lower().split("（")[0].split())]
        if suggestions:
            suggestions = suggestions[:6]
            st.markdown("##### 🔍 建议")
            cols = st.columns(3)
            for i, s in enumerate(suggestions):
                with cols[i % 3]:
                    if st.button(s, key=f"sug_{i}", use_container_width=True):
                        st.session_state.search_query_input = s
                        st.rerun()

    # 搜索历史标签
    if not query and st.session_state.search_history:
        history = list(dict.fromkeys(st.session_state.search_history[-8:]))  # 去重
        st.markdown("##### 🔄 最近搜索")
        cols = st.columns(4)
        for i, h in enumerate(history):
            with cols[i % 4]:
                if st.button(f"🔄 {h}", key=f"hist_{i}", use_container_width=True):
                    st.session_state.search_query_input = h

    # 热门景点（按搜索热度）
    if not query and not st.session_state.search_history:
        st.markdown("##### 🔥 热门景点")
        hot = sorted(retriever.attractions, key=lambda a: st.session_state.search_counts.get(a["name"], 0), reverse=True)[:6]
        hot = [a for a in hot if st.session_state.search_counts.get(a["name"], 0) > 0]
        if hot:
            cols = st.columns(3)
            for i, a in enumerate(hot[:6]):
                with cols[i % 3]:
                    if st.button(f"🔥 {a['name']}", key=f"hot_{i}", use_container_width=True):
                        ask_question(f"介绍一下{a['name']}")

    # 筛选器行
    col1, col2, col3 = st.columns(3)
    with col1:
        province_filter = st.selectbox("省份", ["全部"] + retriever.get_provinces(), label_visibility="collapsed")
    with col2:
        category_filter = st.selectbox("分类", ["全部"] + retriever.get_categories(), label_visibility="collapsed")
    with col3:
        min_rating = st.slider("评分", 0.0, 5.0, 0.0, 0.5, label_visibility="collapsed")

    if query:
        province = province_filter if province_filter != "全部" else None
        category = category_filter if category_filter != "全部" else None
        rating = min_rating if min_rating > 0 else None

        # 显示骨架屏
        skeleton_placeholder = st.empty()
        skeleton_html = "".join(display_skeleton(4) for _ in range(3))
        skeleton_placeholder.markdown(skeleton_html, unsafe_allow_html=True)

        if use_hybrid and hasattr(retriever, "_semantic_embedder"):
            results = retriever.hybrid_search(query, top_k=20)
            if province:
                results = [(a, s) for a, s in results if a["province"] == province]
            if category:
                results = [(a, s) for a, s in results if a["category"] == category]
        else:
            results = retriever.search(query, top_k=20, province=province,
                                       category=category, min_rating=rating)

        skeleton_placeholder.empty()  # 清除骨架

        if results:
            # 记录搜索历史和热度
            if query not in st.session_state.search_history:
                st.session_state.search_history.append(query)
            for att, score in results:
                name = att["name"]
                st.session_state.search_counts[name] = st.session_state.search_counts.get(name, 0) + 1

            st.success(f"找到 {len(results)} 个相关景点")
            for att, score in results:
                display_attraction_card(att, score)
        else:
            st.info("未找到匹配的景点，请调整搜索条件。")
    else:
        st.info("请输入关键词开始搜索。")


def render_province_page():
    st.markdown('<div class="main-header">🗺️ 按省份浏览</div>', unsafe_allow_html=True)
    provinces = retriever.get_provinces()
    province = st.selectbox("选择省份", provinces, key="province_selectbox")
    if province:
        st.markdown(f"### 📍 {province}（{len(retriever.get_by_province(province))}个景点）")
        for att in retriever.get_by_province(province):
            display_attraction_card(att)


def render_category_page():
    st.markdown('<div class="main-header">📂 按分类浏览</div>', unsafe_allow_html=True)
    for cat in retriever.get_categories():
        cat_attrs = retriever.get_by_category(cat)
        with st.expander(f"{cat}（{len(cat_attrs)}个景点）", expanded=True):
            # 网格排列 mini 卡片
            grid_cols = st.columns(2)
            for idx, att in enumerate(cat_attrs):
                with grid_cols[idx % 2]:
                    mini_card(att)


def render_map_page():
    st.markdown('<div class="main-header">🗺️ 景点地图</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">全国景点分布图 — 点击标记查看景点信息</div>', unsafe_allow_html=True)

    try:
        import folium
        from streamlit_folium import st_folium
    except ImportError:
        st.error("需要安装 folium 和 streamlit-folium：`pip install folium streamlit-folium`")
        return

    mapped = [a for a in retriever.attractions if a.get("location")]
    if not mapped:
        st.info("暂无可显示的景点坐标数据")
        return

    cat_colors = {
        "历史文化": "#e74c3c", "自然风光": "#27ae60",
        "主题乐园": "#f39c12", "都市风情": "#3498db", "现代建筑": "#9b59b6",
    }

    m = folium.Map(location=[34.0, 108.0], zoom_start=5, tiles="OpenStreetMap")
    for a in mapped:
        loc = a["location"]
        color = cat_colors.get(a["category"], "#1f77b4")
        popup_html = f"""
        <div style="min-width:220px">
            <b style="font-size:1.05rem">{a['name']}</b><br>
            <span>📍 {a['province']} {a.get('city', '')}</span><br>
            <span>📂 {a['category']} | ⭐{a.get('rating', '')}</span><br>
            <span>🎫 {a.get('ticket', '')}</span>
        </div>
        """
        folium.Marker(
            location=[loc[1], loc[0]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=a["name"],
            icon=folium.Icon(color=color[1:] if color.startswith("#") else "blue", icon="info-sign"),
        ).add_to(m)

    st_folium(m, width=1100, height=600)

    legend_cols = st.columns(5)
    for i, (cat, color) in enumerate(cat_colors.items()):
        with legend_cols[i]:
            st.markdown(
                f'<span style="display:inline-block;width:12px;height:12px;'
                f'background:{color};border-radius:50%;margin-right:4px;"></span> {cat}',
                unsafe_allow_html=True,
            )


def render_compare_page():
    st.markdown('<div class="main-header">📊 景点对比</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">选择2-4个景点，多维度对比</div>', unsafe_allow_html=True)

    selected = st.multiselect(
        "选择要对比的景点（2-4个）",
        [a["name"] for a in retriever.attractions],
        max_selections=4,
    )
    if len(selected) < 2:
        st.info("请至少选择 2 个景点")
        return

    atts = [next(a for a in retriever.attractions if a["name"] == n) for n in selected]

    fields = [
        ("省份", "province"), ("城市", "city"), ("分类", "category"),
        ("评分", "rating"), ("门票", "ticket"), ("最佳季节", "best_season"),
        ("特色亮点", "highlights"), ("简介", "description"),
        ("基础信息", "basic_info"), ("游玩攻略", "travel_guide"),
        ("交通住宿", "transport"), ("文化特色", "culture"), ("美食特产", "food"),
    ]

    html = '<table class="compare-table"><tr><th style="width:100px">对比项</th>'
    for att in atts:
        html += f"<th>{att['name']}</th>"
    html += "</tr>"
    for label, field in fields:
        html += f"<tr><td><b>{label}</b></td>"
        for att in atts:
            val = att.get(field, "")
            if field == "rating":
                val = f"{'⭐' * int(round(val or 0))} {val}"
            html += f"<td>{str(val)[:200]}</td>"
        html += "</tr>"
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)


def render_random_page():
    st.markdown('<div class="main-header">🎲 随机推荐</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 3])
    with col1:
        n = st.selectbox("数量", [3, 5, 8, 10], index=1)
    with col2:
        if st.button("🎲 换一批", use_container_width=True):
            st.session_state.rand_key = st.session_state.get("rand_key", 0) + 1

    for att in retriever.random_attractions(n):
        display_attraction_card(att)


def render_stats_page():
    st.markdown('<div class="main-header">📊 数据概览</div>', unsafe_allow_html=True)
    stats = retriever.get_stats()

    col1, col2, col3 = st.columns(3)
    col1.metric("景点总数", stats["total"])
    col2.metric("覆盖省份", stats["provinces"])
    col3.metric("分类数", len(stats["categories"]))

    has_semantic = hasattr(retriever, "_semantic_embedder")
    col1, col2 = st.columns(2)
    with col1:
        col1.metric("语义检索", "✅ 已启用" if has_semantic else "❌ 未启用")
    with col2:
        mapped = sum(1 for a in retriever.attractions if a.get("location"))
        col2.metric("GPS 坐标", f"{mapped} 个景点")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("##### 各省份景点数量")
        counts = [(p, len(retriever.get_by_province(p))) for p in retriever.get_provinces()]
        counts.sort(key=lambda x: x[1], reverse=True)
        for p, c in counts:
            bar = int(c / max(x[1] for x in counts) * 100)
            st.markdown(
                f"<div style='display:flex;align-items:center;margin:3px 0'>"
                f"<span style='width:70px;font-size:0.85rem'>{p}</span>"
                f"<div style='background:#1f77b4;width:{bar}%;height:20px;border-radius:3px;"
                f"color:white;padding-left:5px;font-size:0.8rem'>{c}</div></div>",
                unsafe_allow_html=True,
            )
    with col_b:
        st.markdown("##### 分类分布")
        for cat in stats["categories"]:
            st.markdown(f"- **{cat}**: {len(retriever.get_by_category(cat))} 个")

        st.markdown("---")
        st.markdown("##### 系统信息")
        st.markdown(f"- 检索方式: {'TF-IDF + 语义融合' if has_semantic else 'TF-IDF 字段加权'}")
        st.markdown("- 意图识别: 优先级规则 + 150+别名库 + 共指消解")
        st.markdown(f"- 景点数: {stats['total']} | 手工润色: 30+")


# ===== 新页面：行程规划 =====

def render_itinerary_page():
    st.markdown('<div class="main-header">🗺️ 行程规划</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">输入目的地和天数，自动生成多日行程</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        dest = st.text_input("目的地", placeholder="例如：北京、四川、杭州", label_visibility="collapsed")
    with col2:
        days = st.number_input("天数", min_value=1, max_value=14, value=3, label_visibility="collapsed")
    with col3:
        generate_btn = st.button("生成行程", use_container_width=True, type="primary")

    if generate_btn:
        if not dest:
            st.warning("请输入目的地")
            return

        query = f"{dest}{days}日游"
        province = intent_engine.extract_province(dest) or dest
        city = intent_engine.extract_city(dest)

        plan = generate_itinerary(retriever.attractions, query,
                                  province=province, city=city, days=days)

        if plan:
            # 导出按钮
            export_col1, export_col2 = st.columns([5, 1])
            with export_col2:
                md_content = plan["itinerary"].replace("unsafe_allow_html=True", "").replace("st.markdown(", "")
                st.download_button("📥 导出行程", data=plan["itinerary"],
                                   file_name=f"{dest}{days}日游.md", mime="text/markdown",
                                   use_container_width=True)
            st.markdown(plan["itinerary"], unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("##### 💰 费用估算")
            cost = estimate_trip_cost(province, days)
            display_cost_estimate(cost)

            st.markdown("---")
            for day in plan.get("plan", []):
                for a in day.get("attractions", []):
                    if st.button(f"问AI关于「{a['name']}」", key=f"iti_{a['id']}", use_container_width=True):
                        ask_question(f"介绍一下{a['name']}")
        else:
            st.warning(f"未找到 {dest} 的景点数据，试试其他目的地")


# ===== 新页面：我的收藏 =====

def render_favorites_page():
    st.markdown('<div class="main-header">⭐ 我的收藏</div>', unsafe_allow_html=True)
    data = load_favorites()
    favs = data["favorites"]
    notes = data["notes"]

    if not favs:
        st.info("还没有收藏景点，浏览景点时点击 ⭐ 收藏即可添加")
        return

    st.markdown(f"共收藏 **{len(favs)}** 个景点\n")

    for name in favs:
        att = None
        for a in retriever.attractions:
            if a["name"] == name:
                att = a
                break
        if not att:
            continue

        with st.expander(f"⭐ {name} — {att['province']} {att.get('city', '')}", expanded=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                note = notes.get(name, "")
                new_note = st.text_area("📝 旅行笔记", value=note,
                                        placeholder="添加你的旅行笔记...",
                                        key=f"note_{name}")
                if new_note != note:
                    save_note(name, new_note)

            with col2:
                if st.button("🗑️ 取消收藏", key=f"unfav_{name}", use_container_width=True):
                    toggle_favorite(name)
                    st.rerun()
                if st.button("💬 问AI", key=f"fav_q_{name}", use_container_width=True):
                    ask_question(f"介绍一下{name}")

            if note:
                st.markdown(f"**📝 笔记：** {note}")


# ===== 新页面：费用估算 =====

def render_cost_page():
    st.markdown('<div class="main-header">💰 费用估算</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">按省份和天数的旅行费用估算参考</div>', unsafe_allow_html=True)

    from data.cost_data import COST_ESTIMATES

    provinces = list(COST_ESTIMATES.keys())
    col1, col2, col3 = st.columns(3)
    with col1:
        province = st.selectbox("目的地省份", provinces, index=provinces.index("四川"))
    with col2:
        days = st.number_input("旅行天数", min_value=1, max_value=30, value=3)
    with col3:
        people = st.number_input("人数", min_value=1, max_value=20, value=1)

    category = st.selectbox("景点类型偏好", ["全部"] + list(retriever.get_categories()))

    cost = estimate_trip_cost(province, days,
                              category if category != "全部" else None)
    display_cost_estimate(cost, people)

    st.markdown("---")
    st.markdown("##### 📋 费用构成说明")
    st.markdown("""
    - **住宿**: 经济型酒店/连锁快捷酒店价格区间
    - **餐饮**: 日常三餐（小吃/简餐/特色餐厅）
    - **交通**: 市内公共交通（公交/地铁/打车混合估算）
    - **门票**: 景点门票按分类估算（不含索道/观光车等额外项目）
    - *以上为估算参考，实际费用因季节/标准/消费习惯而异*
    """)


def display_cost_estimate(cost: dict, people: int = 1):
    """显示费用估算卡片"""
    st.markdown(f"##### 💰 {cost['province']} {cost['days']}日游 费用估算（{people}人）")

    cats = [
        ("🏨 住宿", "住宿", "元"),
        ("🍽️ 餐饮", "餐饮", "元"),
        ("🚌 交通", "交通", "元"),
        ("🎫 门票", "门票", "元"),
    ]

    cols = st.columns(4)
    for i, (label, key, unit) in enumerate(cats):
        lo, hi = cost[key]
        with cols[i]:
            st.markdown(
                f'<div class="cost-card">'
                f'<b>{label}</b><br>'
                f'<span style="font-size:1.3rem;font-weight:700">'
                f'{lo * people}-{hi * people}{unit}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    total_lo, total_hi = cost["总计"]
    st.markdown(
        f'<div style="padding:1rem;border-radius:10px;background:#fff;color:#000;'
        f'text-align:center;margin:0.5rem 0;border:2px solid #333">'
        f'<span style="font-size:0.9rem">预计总花费</span><br>'
        f'<span style="font-size:2rem;font-weight:700">{total_lo * people} - {total_hi * people} 元</span>'
        f'<br><span style="font-size:0.8rem;color:#555">人均 {total_lo} - {total_hi} 元</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ===== 辅助组件 =====

def display_attraction_card(att, score=None):
    """完整景点卡片 — 含收藏、附近、天气、图片"""
    stars = "⭐" * int(round(att.get("rating", 0) or 0))
    fav = is_favorite(att["name"])

    # 收藏按钮
    fav_col, title_col = st.columns([1, 20])
    with fav_col:
        fav_label = "❤️" if fav else "🤍"
        if st.button(fav_label, key=f"fav_{att['id']}", help="点击收藏/取消"):
            toggle_favorite(att["name"])
            st.rerun()
    with title_col:
        st.markdown(f"### {att['name']}")

    st.markdown(
        f"""
        <div class="attraction-card">
            <div style="margin-bottom:6px">
                <span class="tag">📍 {att['province']} {att.get('city', '')}</span>
                <span class="tag">📂 {att['category']}</span>
                <span class="tag tag-rating">{stars} {att.get('rating', '')}</span>
                <span class="tag">🎫 {att.get('ticket', '')}</span>
                {f'<span class="tag">匹配度: {score:.2f}</span>' if score else ''}
                {'<span class="tag tag-fav">⭐ 已收藏</span>' if fav else ''}
            </div>
            <p>{att.get('description', '')}</p>
            <p><b>✨ 特色：</b>{att.get('highlights', '')}</p>
            <p><b>📅 最佳季节：</b>{att.get('best_season', '')}</p>
            <p><b>💡 提示：</b>{att.get('tips', '')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 场景快捷按钮
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("📍 基础信息", key=f"bi_{att['id']}", use_container_width=True):
            ask_question(f"介绍一下{att['name']}的基本信息")
    with col2:
        if st.button("🗺️ 游玩攻略", key=f"tg_{att['id']}", use_container_width=True):
            ask_question(f"{att['name']}怎么玩？有什么攻略？")
    with col3:
        if st.button("🚗 交通住宿", key=f"tr_{att['id']}", use_container_width=True):
            ask_question(f"去{att['name']}交通方便吗？住哪里好？")
    with col4:
        if st.button("🎭 民俗文化", key=f"cu_{att['id']}", use_container_width=True):
            ask_question(f"{att['name']}有什么文化特色？")
    with col5:
        if st.button("🍜 美食特产", key=f"fo_{att['id']}", use_container_width=True):
            ask_question(f"{att['name']}有什么好吃的？")

    # 天气 + 附近景点 + 图片（折叠）
    with st.expander("🌤️ 天气 / 📍 附近景点 / 🖼️ 图片", expanded=False):
        tabs = st.tabs(["🌤️ 天气", "📍 附近景点", "🖼️ 图片"])

        with tabs[0]:
            with st.spinner("查询天气..."):
                city = att.get("city", "") or att["province"]
                weather_data = fetch_weather(city)
                weather = parse_weather(weather_data)
            if weather:
                st.markdown(
                    f'<div class="weather-card">'
                    f'<div class="temp">{weather["temp"]}°C</div>'
                    f'<div class="desc">{weather["desc"]}</div>'
                    f'<div>体感 {weather["feels"]}°C | 湿度 {weather["humidity"]}% | 风速 {weather["wind"]}km/h</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if weather["forecast"]:
                    fc_cols = st.columns(3)
                    for i, day in enumerate(weather["forecast"]):
                        with fc_cols[i]:
                            st.markdown(f"**{day['date']}**  {day['lo']}-{day['hi']}°C {day['desc']}")
            else:
                st.info("暂未获取到天气信息")

        with tabs[1]:
            nearby = get_nearby_attractions(retriever.attractions, att, top_n=5)
            if nearby:
                for na, dist in nearby:
                    st.markdown(f"**{na['name']}** — {dist:.0f}km — {na['category']} ⭐{na.get('rating', '')}")
                    if st.button(f"查看 {na['name']}", key=f"near_{att['id']}_{na['id']}"):
                        ask_question(f"介绍一下{na['name']}")
            else:
                st.info("暂未发现附近景点（300km范围内）")

        with tabs[2]:
            with st.spinner("搜索景点图片..."):
                img_url = fetch_image(att["name"])
            if img_url:
                st.markdown(f'<img src="{img_url}" style="max-width:100%;border-radius:8px">',
                            unsafe_allow_html=True)
                st.caption(f"来源: Wikimedia Commons · {att['name']}")
            else:
                st.info("暂未找到相关图片")


def mini_card(att):
    stars = "⭐" * int(round(att.get("rating", 0) or 0))
    fav = is_favorite(att["name"])
    fav_icon = " ⭐" if fav else ""
    st.markdown(
        f"""
        <div style="padding:8px 12px;border-left:3px solid #1f77b4;margin:4px 0;
                    background:#fff;border-radius:0 6px 6px 0">
            <b>{att['name']}{fav_icon}</b> {stars} {att.get('rating', '')} —
            {att['province']} {att.get('city', '')} | 🎫 {att.get('ticket', '')}
            <br><span style="font-size:0.9rem;color:#666">{att.get('highlights', '')[:80]}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===== 页面路由 =====

PAGE_ROUTER = {
    "💬 智能问答": render_qa_page,
    "🔍 景点搜索": render_search_page,
    "🗺️ 按省份浏览": render_province_page,
    "📂 按分类浏览": render_category_page,
    "🗺️ 景点地图": render_map_page,
    "📊 景点对比": render_compare_page,
    "🗺️ 行程规划": render_itinerary_page,
    "⭐ 我的收藏": render_favorites_page,
    "💰 费用估算": render_cost_page,
    "🎲 随机推荐": render_random_page,
    "📊 数据概览": render_stats_page,
}

render_fn = PAGE_ROUTER.get(page, render_qa_page)
render_fn()
