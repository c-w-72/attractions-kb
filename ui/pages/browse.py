"""浏览类页面：搜索、省份浏览、分类浏览、随机推荐、地图、季节推荐"""
import random
import datetime
import streamlit as st
from data.persistence import load_search_counts, save_search_counts
from ui.components import ask_question, display_attraction_card, mini_card, display_skeleton


def render_search_page():
    st.markdown('<div class="main-header">🔍 景点搜索</div>', unsafe_allow_html=True)

    if "search_history" not in st.session_state:
        st.session_state.search_history = []
    if "search_counts" not in st.session_state:
        st.session_state.search_counts = load_search_counts()

    retriever = st.session_state.retriever

    search_col, toggle_col = st.columns([5, 1])
    with search_col:
        query = st.text_input("关键词", placeholder="例如：长城、古镇、避暑、看海...",
                              label_visibility="collapsed", key="search_query_input")
    with toggle_col:
        use_hybrid = st.toggle("语义搜索", value=False,
                               help="启用语义融合检索（更精准）")

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

    if not query and st.session_state.search_history:
        history = list(dict.fromkeys(st.session_state.search_history[-8:]))
        st.markdown("##### 🔄 最近搜索")
        cols = st.columns(4)
        for i, h in enumerate(history):
            with cols[i % 4]:
                if st.button(f"🔄 {h}", key=f"hist_{i}", use_container_width=True):
                    st.session_state.search_query_input = h

    if not query and not st.session_state.search_history:
        st.markdown("##### 🔥 热门景点")
        search_counts = st.session_state.search_counts
        hot = sorted(retriever.attractions, key=lambda a: search_counts.get(a["name"], 0), reverse=True)[:6]
        hot = [a for a in hot if search_counts.get(a["name"], 0) > 0]
        if not hot:
            # 冷启动：按评分推荐
            hot = sorted(retriever.attractions, key=lambda a: a.get("rating", 0) or 0, reverse=True)[:6]
        cols = st.columns(3)
        for i, a in enumerate(hot[:6]):
            with cols[i % 3]:
                if st.button(f"🔥 {a['name']}", key=f"hot_{i}", use_container_width=True):
                    ask_question(f"介绍一下{a['name']}")

    col1, col2, col3 = st.columns(3)
    with col1:
        province_filter = st.selectbox("省份", ["全部"] + retriever.get_provinces(), label_visibility="collapsed")
    with col2:
        category_filter = st.selectbox("分类", ["全部"] + retriever.get_categories(), label_visibility="collapsed")
    with col3:
        min_rating = st.slider("评分", 0.0, 5.0, 0.0, 0.5, label_visibility="collapsed")

    if query:
        # 防抖：仅当查询词变化时才重新搜索
        if st.session_state.get("_last_query") != query:
            st.session_state._last_query = query
            st.session_state._last_results = None

        province = province_filter if province_filter != "全部" else None
        category = category_filter if category_filter != "全部" else None
        rating = min_rating if min_rating > 0 else None

        if st.session_state._last_results is None:
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

            skeleton_placeholder.empty()
            st.session_state._last_results = results
        else:
            results = st.session_state._last_results

        if results:
            if query not in st.session_state.search_history:
                st.session_state.search_history.append(query)
            for att, score in results:
                name = att["name"]
                st.session_state.search_counts[name] = st.session_state.search_counts.get(name, 0) + 1
            save_search_counts(st.session_state.search_counts)

            st.success(f"找到 {len(results)} 个相关景点")

            compact = st.toggle("📋 紧凑模式", value=True, key="search_compact_toggle")
            if compact:
                cols = st.columns(2)
                for i, (att, score) in enumerate(results):
                    with cols[i % 2]:
                        mini_card(att)
            else:
                for att, score in results:
                    display_attraction_card(att, score, highlight=query)
        else:
            pinyin_results = retriever.fuzzy_search(query, top_k=6)
            if pinyin_results:
                st.warning(f"未找到「{query}」的直接匹配，您是不是要找：")
                cols = st.columns(3)
                for i, (att, score) in enumerate(pinyin_results):
                    with cols[i % 3]:
                        if st.button(f"🔍 {att['name']}", key=f"py_{i}", use_container_width=True):
                            st.session_state.search_query_input = att["name"]
                            st.rerun()
            else:
                st.info("未找到匹配的景点，请调整搜索条件。")
    else:
        st.info("请输入关键词开始搜索。")


def render_province_page():
    st.markdown('<div class="main-header">🗺️ 按省份浏览</div>', unsafe_allow_html=True)
    retriever = st.session_state.retriever
    provinces = retriever.get_provinces()
    province = st.selectbox("选择省份", provinces, key="province_selectbox")
    if province:
        st.markdown(f"### 📍 {province}（{len(retriever.get_by_province(province))}个景点）")
        for att in retriever.get_by_province(province):
            display_attraction_card(att)


def render_category_page():
    st.markdown('<div class="main-header">📂 按分类浏览</div>', unsafe_allow_html=True)
    retriever = st.session_state.retriever
    for cat in retriever.get_categories():
        cat_attrs = retriever.get_by_category(cat)
        with st.expander(f"{cat}（{len(cat_attrs)}个景点）", expanded=True):
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
        from folium.plugins import MarkerCluster
    except ImportError:
        st.error("需要安装 folium 和 streamlit-folium：`pip install folium streamlit-folium`")
        return

    retriever = st.session_state.retriever
    mapped = [a for a in retriever.attractions if a.get("location")]
    if not mapped:
        st.info("暂无可显示的景点坐标数据")
        return

    cat_colors = {
        "历史文化": "#e74c3c", "自然风光": "#27ae60",
        "主题乐园": "#f39c12", "都市风情": "#3498db", "现代建筑": "#9b59b6",
    }

    m = folium.Map(location=[34.0, 108.0], zoom_start=5, tiles="OpenStreetMap")
    marker_cluster = MarkerCluster().add_to(m)
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
        ).add_to(marker_cluster)

    st_folium(m, width=1100, height=600)

    legend_cols = st.columns(5)
    for i, (cat, color) in enumerate(cat_colors.items()):
        with legend_cols[i]:
            st.markdown(
                f'<span style="display:inline-block;width:12px;height:12px;'
                f'background:{color};border-radius:50%;margin-right:4px;"></span> {cat}',
                unsafe_allow_html=True,
            )


def render_random_page():
    st.markdown('<div class="main-header">🎲 随机推荐</div>', unsafe_allow_html=True)
    retriever = st.session_state.retriever
    col1, col2 = st.columns([1, 3])
    with col1:
        n = st.selectbox("数量", [3, 5, 8, 10], index=1)
    with col2:
        if st.button("🎲 换一批", use_container_width=True):
            st.session_state.rand_key = st.session_state.get("rand_key", 0) + 1

    for att in retriever.random_attractions(n):
        display_attraction_card(att)


def render_seasonal_page():
    st.markdown('<div class="main-header">🌤️ 季节推荐</div>', unsafe_allow_html=True)

    month = datetime.datetime.now().month
    if 3 <= month <= 5:
        season_cn = "🌸 春季（3-5月）"
        badge = "season-badge-spring"
        months = [3, 4, 5]
        next_cn = "☀️ 夏季（6-8月）"
    elif 6 <= month <= 8:
        season_cn = "☀️ 夏季（6-8月）"
        badge = "season-badge-summer"
        months = [6, 7, 8]
        next_cn = "🍂 秋季（9-11月）"
    elif 9 <= month <= 11:
        season_cn = "🍂 秋季（9-11月）"
        badge = "season-badge-autumn"
        months = [9, 10, 11]
        next_cn = "❄️ 冬季（12-2月）"
    else:
        season_cn = "❄️ 冬季（12-2月）"
        badge = "season-badge-winter"
        months = [12, 1, 2]
        next_cn = "🌸 春季（3-5月）"

    st.markdown(f'<span class="season-badge {badge}">{season_cn}</span>', unsafe_allow_html=True)

    def match_season(text):
        if not text:
            return False
        for m in months:
            if str(m) in text:
                return True
        return False

    tab1, tab2 = st.tabs([f"{season_cn} 推荐", f"{next_cn} 预告"])
    with tab1:
        retriever = st.session_state.retriever
        matched = [a for a in retriever.attractions if match_season(a.get("best_season", ""))]
        if not matched:
            matched = retriever.attractions[:20]
        st.success(f"找到 {len(matched)} 个适合当季游览的景点")
        for att in matched[:15]:
            display_attraction_card(att)
    with tab2:
        retriever = st.session_state.retriever
        next_matched = [a for a in retriever.attractions if match_season(a.get("best_season", ""))]
        random.shuffle(next_matched)
        st.info(f"主下个季节预热 — 推荐 {len(next_matched[:10])} 个景点")
        for att in next_matched[:10]:
            display_attraction_card(att)
