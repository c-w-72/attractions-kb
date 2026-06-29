"""
行程规划器 — 多日游路线推荐
"""

import re

# 默认行程安排模板
DAY_TEMPLATES = {
    "历史文化": {
        "time": "2-3小时",
        "note": "建议请讲解或租讲解器，了解历史背景收获更大",
    },
    "自然风光": {
        "time": "3-5小时",
        "note": "穿舒适登山鞋，带足水和零食",
    },
    "主题乐园": {
        "time": "4-6小时",
        "note": "建议工作日前往，避开周末人流高峰",
    },
    "都市风情": {
        "time": "1-2小时",
        "note": "适合拍照打卡，早晚光线最佳",
    },
    "现代建筑": {
        "time": "1-2小时",
        "note": "傍晚登顶观城市夜景效果最佳",
    },
}

MEAL_TIPS = {
    "早餐": "酒店用餐或附近早点摊，人均15-30元",
    "午餐": "景区附近简餐，人均30-60元",
    "晚餐": "当地特色餐厅，人均50-100元",
}


CHINESE_NUMERALS = {
    "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
}


def parse_itinerary_query(query: str) -> dict | None:
    """解析行程规划意图，提取目的地和天数"""
    # 归一化：将中文数字转为阿拉伯数字
    normalized = query
    for cn, num in CHINESE_NUMERALS.items():
        normalized = normalized.replace(cn, str(num))

    # 匹配 "X日游" 或 "X天" 或 "X天X晚"
    day_patterns = [
        r"(\d+)\s*日\s*游",
        r"(\d+)\s*天\s*(\d+)\s*晚",
        r"(\d+)\s*天",
        r"(\d+)\s*日",
    ]
    days = None
    for pat in day_patterns:
        m = re.search(pat, normalized)
        if m:
            days = int(m.group(1))
            break

    if days is None or days < 1:
        return None

    if days > 14:
        days = 14

    return {"days": days}


def generate_itinerary(attractions: list, query: str, province: str = None,
                       city: str = None, days: int = 3) -> dict | None:
    """生成多日行程规划"""
    # 筛选目的地景点
    candidates = []
    for a in attractions:
        if province and a["province"] != province:
            continue
        if city and a.get("city", "") != city:
            continue
        candidates.append(a)

    if not candidates:
        return None

    # 按评分排序，选出核心景点
    candidates.sort(key=lambda x: x.get("rating", 0), reverse=True)

    # 按分类分组
    by_category = {}
    for a in candidates:
        cat = a["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(a)

    # 分配景点到每天
    max_per_day = min(3, max(1, (len(candidates) + days - 1) // days))
    plan = []
    used = set()
    day_num = 1

    # 先在每天分配一个核心景点
    core_assigned = 0
    for cat in ["历史文化", "自然风光", "主题乐园", "都市风情", "现代建筑"]:
        if core_assigned >= days:
            break
        if cat in by_category:
            for a in by_category[cat]:
                if a["id"] not in used:
                    plan.append({
                        "day": core_assigned + 1,
                        "attractions": [a],
                        "theme": f"第{core_assigned + 1}天 · {' '.join(a.get('highlights','').split('、')[:2])}",
                    })
                    used.add(a["id"])
                    core_assigned += 1
                    break

    # 填充剩余景点
    remaining = [a for a in candidates if a["id"] not in used]
    idx = 0
    while idx < len(remaining) and days > 0:
        day_idx = idx % days
        if day_idx >= len(plan):
            plan.append({
                "day": day_idx + 1,
                "attractions": [],
                "theme": f"第{day_idx + 1}天 · 探索之旅",
            })
        if len(plan[day_idx]["attractions"]) < max_per_day:
            plan[day_idx]["attractions"].append(remaining[idx])
            idx += 1
        else:
            idx += 1

    # 确保每天都有至少一个景点
    for i in range(days):
        if i >= len(plan):
            plan.append({
                "day": i + 1,
                "attractions": [],
                "theme": f"第{i + 1}天 · 自由探索",
            })

    # 生成描述
    location_name = city or province or "该地区"
    lines = [f"### 🗺️ {location_name}{days}日游行程规划\n"]
    lines.append(f"基于 {len(candidates)} 个相关景点，为你规划了以下 {days} 日行程：\n")

    total_ticket = 0
    for day in plan[:days]:
        atts = day["attractions"]
        if not atts:
            continue

        lines.append(f"---\n### 📅 {day['theme']}\n")
        lines.append(f"**景点 ({len(atts)}个)：**\n")

        day_tickets = 0
        for i, a in enumerate(atts, 1):
            cat_tpl = DAY_TEMPLATES.get(a["category"], {"time": "2-3小时", "note": ""})
            lines.append(f"  **{i}. {a['name']}** — ⭐{a.get('rating', '')} | ⏱ {cat_tpl['time']} | 🎫 {a.get('ticket', '不明')}")
            lines.append(f"     📍 {a['province']} {a.get('city', '')} | 📂 {a['category']}")
            if cat_tpl["note"]:
                lines.append(f"     💡 {cat_tpl['note']}")
            lines.append("")

            ticket_str = a.get("ticket", "")
            ticket_nums = re.findall(r'(\d+)', ticket_str)
            if ticket_nums:
                day_tickets += int(ticket_nums[0])

        total_ticket += day_tickets

        lines.append("**🍽️ 餐饮建议：**")
        lines.append(f"  - 🌅 {MEAL_TIPS['早餐']}")
        lines.append(f"  - 🌞 {MEAL_TIPS['午餐']}")
        lines.append(f"  - 🌙 {MEAL_TIPS['晚餐']}")
        lines.append("")

    lines.append("---\n### 💰 费用参考\n")
    lines.append(f"- **门票总计**: 约 {total_ticket} 元（仅含上述景点门票）")
    lines.append(f"- **每日餐饮**: 约 100-250 元/人")
    lines.append(f"- **住宿预算**: 因地段和标准差异较大")

    lines.append("\n---\n")
    lines.append("💡 *提示：以上行程为自动生成建议，实际安排请结合个人偏好和实时信息调整。*")

    return {
        "itinerary": "\n".join(lines),
        "days": days,
        "attraction_count": len(candidates),
        "plan": plan[:days],
    }
