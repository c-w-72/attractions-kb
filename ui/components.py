"""
UI 组件 — 景点卡片、骨架屏、高亮、消息处理
"""

import re
import random
import streamlit as st
from engine.geo import get_nearby_attractions
from engine.external import fetch_weather, parse_weather, fetch_image, fetch_images, fetch_weather_cached
from data.persistence import load_favorites, toggle_favorite, save_chat_message
from data.cost_data import estimate_trip_cost


def _get_favorites_set() -> set:
    """缓存收藏列表到 session_state，避免重复读盘"""
    if "fav_names" not in st.session_state:
        data = load_favorites()
        st.session_state.fav_names = set(data["favorites"])
    return st.session_state.fav_names


def _invalidate_favorites():
    """收藏变更后清除缓存"""
    st.session_state.fav_names = None


def add_message(role: str, content: str, **kwargs):
    """添加消息并持久化到磁盘"""
    msg = {"role": role, "content": content, **kwargs}
    st.session_state.messages.append(msg)
    save_chat_message(msg)


def ask_question(query: str):
    """从任意页面提交问题并跳转到智能问答"""
    if query.strip():
        add_message("user", query.strip())
        st.session_state.nav_selected = "💬 智能问答"
        st.rerun()


def display_followups(followups: list):
    if not followups:
        return
    st.markdown("##### 💬 你可能还想了解：")
    cols = st.columns(2)
    for i, q in enumerate(followups):
        with cols[i % 2]:
            if st.button(q, use_container_width=True, key=f"fu_{i}_{q[:10]}"):
                ask_question(q)


def _highlight_text(text, query):
    """高亮显示匹配关键词"""
    if not text or not query:
        return text
    for kw in re.split(r'[\s,，、]+', query.strip()):
        if len(kw) < 2:
            continue
        text = re.sub(f"({re.escape(kw)})", r'<span class="highlight">\1</span>', text, flags=re.IGNORECASE)
    return text


def display_skeleton(n=3):
    """骨架屏占位"""
    html = ""
    for _ in range(n):
        html += '<div style="height:20px;background:#f0f0f0;border-radius:4px;margin:8px 0"> </div>'
    return html


def display_attraction_card(att, score=None, highlight=None):
    """完整景点卡片 — 含收藏、附近、天气、图片"""
    stars = "⭐" * int(round(att.get("rating", 0) or 0))
    fav_set = _get_favorites_set()
    fav = att["name"] in fav_set

    fav_col, title_col = st.columns([1, 20])
    with fav_col:
        fav_label = "❤️" if fav else "🤍"
        if st.button(fav_label, key=f"fav_{att['id']}", help="点击收藏/取消"):
            toggle_favorite(att["name"])
            _invalidate_favorites()
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
            <p>{_highlight_text(att.get('description', ''), highlight) if highlight else att.get('description', '')}</p>
            <p><b>✨ 特色：</b>{_highlight_text(att.get('highlights', ''), highlight) if highlight else att.get('highlights', '')}</p>
            <p><b>📅 最佳季节：</b>{att.get('best_season', '')}</p>
            <p><b>💡 提示：</b>{att.get('tips', '')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    with st.expander("🌤️ 天气 / 📍 附近景点 / 🖼️ 图片", expanded=False):
        tabs = st.tabs(["🌤️ 天气", "📍 附近景点", "🖼️ 图片"])

        with tabs[0]:
            with st.spinner("查询天气..."):
                raw_city = att.get("city", "") or att["province"]
                # 统一城市名后缀，保证缓存 key 一致
                for _suffix in ["市", "县", "区", "地区", "自治州", "盟"]:
                    if raw_city.endswith(_suffix) and len(raw_city) > 3:
                        raw_city = raw_city[:-_suffix]
                weather = fetch_weather_cached(raw_city)
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
            retriever = st.session_state.retriever
            if "nearby_cache" not in st.session_state:
                st.session_state.nearby_cache = {}
            elif len(st.session_state.nearby_cache) > 200:
                # 限制缓存上限，淘汰最早的一半
                keys = list(st.session_state.nearby_cache.keys())
                for k in keys[:100]:
                    del st.session_state.nearby_cache[k]
            cache_key = f"nearby_{att['id']}"
            if cache_key not in st.session_state.nearby_cache:
                st.session_state.nearby_cache[cache_key] = get_nearby_attractions(retriever.attractions, att, top_n=5)
            nearby = st.session_state.nearby_cache[cache_key]
            if nearby:
                for na, dist in nearby:
                    st.markdown(f"**{na['name']}** — {dist:.0f}km — {na['category']} ⭐{na.get('rating', '')}")
                    if st.button(f"查看 {na['name']}", key=f"near_{att['id']}_{na['id']}"):
                        ask_question(f"介绍一下{na['name']}")
            else:
                st.info("暂未发现附近景点（300km范围内）")

        with tabs[2]:
            if "img_cache" not in st.session_state:
                st.session_state.img_cache = {}
            elif len(st.session_state.img_cache) > 100:
                keys = list(st.session_state.img_cache.keys())
                for k in keys[:50]:
                    del st.session_state.img_cache[k]
            cache_key = f"img_{att['id']}"
            if cache_key not in st.session_state.img_cache:
                with st.spinner("搜索景点图片..."):
                    st.session_state.img_cache[cache_key] = fetch_images(att["name"], max_images=6)
            img_urls = st.session_state.img_cache[cache_key]
            if img_urls:
                # 点击放大预览
                preview_key = f"img_preview_{att['id']}"
                if preview_key in st.session_state:
                    st.image(st.session_state[preview_key], use_container_width=True)
                    if st.button("✕ 关闭预览", key=f"close_{att['id']}"):
                        del st.session_state[preview_key]
                        st.rerun()
                n = len(img_urls)
                cols = st.columns(min(n, 3))
                for i, url in enumerate(img_urls):
                    with cols[i % 3]:
                        st.markdown(f'<a href="{url}" target="_blank"><img src="{url}" '
                                    f'style="width:100%;aspect-ratio:4/3;object-fit:cover;'
                                    f'border-radius:6px;margin-bottom:4px"></a>',
                                    unsafe_allow_html=True)
                        if st.button("🔍 放大", key=f"img_{att['id']}_{i}", use_container_width=True):
                            st.session_state[preview_key] = url
                            st.rerun()
            else:
                st.info("暂未找到相关图片")


def mini_card(att, show_fav=False):
    stars = "⭐" * int(round(att.get("rating", 0) or 0))
    fav_set = _get_favorites_set()
    fav = att["name"] in fav_set
    fav_icon = " ⭐" if fav else ""

    name = att['name']
    rating = att.get('rating', '')
    province = att['province']
    city = att.get('city', '')
    ticket = att.get('ticket', '')
    highlights = att.get('highlights', '')[:80]
    line = f"**{name}{fav_icon}** {stars} {rating} — {province} {city} | 🎫 {ticket}"

    if show_fav:
        fav_label = "❤️" if fav else "🤍"
        cols = st.columns([1, 20])
        with cols[0]:
            if st.button(fav_label, key=f"mfav_{att['id']}", help="收藏/取消"):
                toggle_favorite(att["name"])
                _invalidate_favorites()
                st.rerun()
        with cols[1]:
            st.markdown(f"{line}\n\n{highlights}")
    else:
        st.markdown(f"{line}\n\n{highlights}")


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
