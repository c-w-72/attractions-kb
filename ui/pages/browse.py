"""浏览类页面：搜索、省份浏览、分类浏览、随机推荐、地图、季节推荐"""
import random
import datetime
import streamlit as st
from data.persistence import load_search_counts, save_search_counts, load_search_history, save_search_history
from ui.components import ask_question, display_attraction_card, mini_card, display_skeleton


def render_search_page():
    st.markdown('<div class="main-header">🔍 景点搜索</div>', unsafe_allow_html=True)

    if "search_history" not in st.session_state:
        st.session_state.search_history = load_search_history()
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
            sug_cols = st.columns(len(suggestions))
            for i, s in enumerate(suggestions):
                with sug_cols[i]:
                    if st.button(s, key=f"sug_{i}", use_container_width=True):
                        st.session_state.search_query_input = s
                        st.rerun()

    if not query and st.session_state.search_history:
        history = list(dict.fromkeys(st.session_state.search_history[-8:]))
        st.markdown("##### 🔄 最近搜索")
        hist_cols = st.columns(min(4, len(history)))
        for i, h in enumerate(history):
            with hist_cols[i % min(4, len(history))]:
                if st.button(f"🔄 {h}", key=f"hist_{i}", use_container_width=True):
                    st.session_state.search_query_input = h

        # 搜索热词标签云
        search_counts = st.session_state.search_counts
        hot_terms = sorted(search_counts.items(), key=lambda x: x[1], reverse=True)[:12]
        if hot_terms and hot_terms[0][1] > 0:
            st.markdown("##### 🔥 搜索热词")
            tag_cols = st.columns(4)
            for i, (term, cnt) in enumerate(hot_terms):
                with tag_cols[i % 4]:
                    if st.button(f"🔥 {term}", key=f"hotword_{i}", use_container_width=True):
                        st.session_state.search_query_input = term
                        st.rerun()

    if not query and not st.session_state.search_history:
        st.markdown("##### 🔥 热门景点")
        search_counts = st.session_state.search_counts
        hot = sorted(retriever.attractions, key=lambda a: search_counts.get(a["name"], 0), reverse=True)[:8]
        hot = [a for a in hot if search_counts.get(a["name"], 0) > 0]
        if not hot:
            # 冷启动：按评分推荐
            hot = sorted(retriever.attractions, key=lambda a: a.get("rating", 0) or 0, reverse=True)[:8]
        cols = st.columns(4)
        for i, a in enumerate(hot[:8]):
            with cols[i % 4]:
                if st.button(f"🔥 {a['name']}", key=f"hot_{i}", use_container_width=True):
                    ask_question(f"介绍一下{a['name']}")

        st.markdown("##### 📂 快速浏览")
        cat_cols = st.columns(len(retriever.get_categories()))
        for i, cat in enumerate(retriever.get_categories()):
            with cat_cols[i]:
                if st.button(f"{cat}", key=f"cat_{cat}", use_container_width=True):
                    ask_question(f"{cat}有哪些推荐景点？")

    col1, col2, col3 = st.columns(3)
    with col1:
        province_filter = st.selectbox("省份", ["全部"] + retriever.get_provinces(), label_visibility="collapsed")
    with col2:
        category_filter = st.selectbox("分类", ["全部"] + retriever.get_categories(), label_visibility="collapsed")
    with col3:
        min_rating = st.slider("评分", 0.0, 5.0, 0.0, 0.5, label_visibility="collapsed")

    if query:
        # 防抖：仅当查询词或筛选条件变化时才重新搜索（缓存 5 分钟过期）
        SEARCH_CACHE_TTL = 300
        search_key = (query, province_filter, category_filter, min_rating, use_hybrid)
        now = datetime.datetime.now()
        last_time = st.session_state.get("_last_search_time")
        if (st.session_state.get("_last_search_key") != search_key
                or last_time is None or (now - last_time).total_seconds() > SEARCH_CACHE_TTL):
            st.session_state._last_search_key = search_key
            st.session_state._last_results = None
            st.session_state._last_search_time = now

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
            if st.session_state.get("_last_counted_query") != query:
                st.session_state._last_counted_query = query
                if query not in st.session_state.search_history:
                    st.session_state.search_history.append(query)
                    save_search_history(st.session_state.search_history)
                for att, score in results:
                    name = att["name"]
                    st.session_state.search_counts[name] = st.session_state.search_counts.get(name, 0) + 1
                # 每 5 次搜索写一次磁盘，避免频繁 I/O
                if "search_count_io" not in st.session_state:
                    st.session_state.search_count_io = 0
                st.session_state.search_count_io += 1
                if st.session_state.search_count_io % 5 == 0:
                    save_search_counts(st.session_state.search_counts)

            st.success(f"找到 {len(results)} 个相关景点")

            # 导出搜索结果
            export_text = "\n".join(
                f"{i+1}. {a['name']}（{a['province']} {a.get('city','')} | {a['category']} | ⭐{a.get('rating','')} | 🎫{a.get('ticket','')}）\n   📝 {a.get('description','')[:100]}"
                for i, (a, s) in enumerate(results)
            )
            st.download_button("📥 导出结果", data=export_text,
                               file_name=f"搜索结果_{query}.txt", mime="text/plain",
                               use_container_width=False)

            per_page = st.selectbox("每页显示", [10, 20, 50], index=1, key="search_per_page")
            total_pages = max(1, (len(results) + per_page - 1) // per_page)
            page_key = "search_page"
            if page_key not in st.session_state:
                st.session_state[page_key] = 1
            st.session_state[page_key] = min(st.session_state[page_key], total_pages)
            current_page = st.session_state[page_key]

            if total_pages > 1:
                nav_cols = st.columns([4, 1, 1, 1, 4])
                with nav_cols[1]:
                    if st.button("◀ 上一页", disabled=current_page <= 1, use_container_width=True):
                        st.session_state[page_key] = current_page - 1
                        st.rerun()
                with nav_cols[2]:
                    st.markdown(f"<div style='text-align:center;padding:4px 0'>{current_page}/{total_pages}</div>",
                                unsafe_allow_html=True)
                with nav_cols[3]:
                    if st.button("下一页 ▶", disabled=current_page >= total_pages, use_container_width=True):
                        st.session_state[page_key] = current_page + 1
                        st.rerun()
                # 翻页后自动滚动到结果区域
                st.markdown(
                    '<div id="search-top"></div>'
                    '<script>'
                    'var el=document.getElementById("search-top");'
                    'if(el)el.scrollIntoView({behavior:"smooth",block:"start"});'
                    '</script>',
                    unsafe_allow_html=True,
                )

            start_idx = (current_page - 1) * per_page
            end_idx = min(start_idx + per_page, len(results))
            page_results = results[start_idx:end_idx]

            compact = st.toggle("📋 紧凑模式", value=True, key="search_compact_toggle")
            if compact:
                cols = st.columns(2)
                for i, (att, score) in enumerate(page_results):
                    with cols[i % 2]:
                        mini_card(att, show_fav=True)
            else:
                for att, score in page_results:
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
                # 基于筛选条件推荐替代景点
                alt = retriever.attractions
                if province:
                    alt = [a for a in alt if a["province"] == province]
                elif category:
                    alt = [a for a in alt if a["category"] == category]
                if alt:
                    alt = sorted(alt, key=lambda a: a.get("rating", 0) or 0, reverse=True)[:4]
                    st.markdown("##### 💡 你可能感兴趣的景点")
                    alt_cols = st.columns(2)
                    for i, a in enumerate(alt):
                        with alt_cols[i % 2]:
                            mini_card(a, show_fav=True)
    else:
        st.info("请输入关键词开始搜索。")


def render_province_page():
    st.markdown('<div class="main-header">🗺️ 按省份浏览</div>', unsafe_allow_html=True)
    retriever = st.session_state.retriever
    provinces = retriever.get_provinces()
    province = st.selectbox("选择省份", provinces, key="province_selectbox")
    if province:
        atts = retriever.get_by_province(province)
        st.markdown(f"### 📍 {province}（{len(atts)}个景点）")

        search_within = st.text_input("🔍 在省内搜索", placeholder="输入关键词筛选景点...",
                                      label_visibility="collapsed", key="prov_search")
        if search_within:
            ql = search_within.lower()
            atts = [a for a in atts if ql in a["name"].lower() or
                    ql in a.get("description", "").lower() or
                    ql in a.get("highlights", "").lower()]
            if not atts:
                st.info(f"在 {province} 内未找到匹配「{search_within}」的景点")
                return
            st.caption(f"找到 {len(atts)} 个匹配景点")

        cols = st.columns(2)
        for i, att in enumerate(atts):
            with cols[i % 2]:
                mini_card(att, show_fav=True)


def render_category_page():
    st.markdown('<div class="main-header">📂 按分类浏览</div>', unsafe_allow_html=True)
    retriever = st.session_state.retriever
    for cat in retriever.get_categories():
        cat_attrs = retriever.get_by_category(cat)
        with st.expander(f"{cat}（{len(cat_attrs)}个景点）", expanded=True):
            grid_cols = st.columns(2)
            for idx, att in enumerate(cat_attrs):
                with grid_cols[idx % 2]:
                    mini_card(att, show_fav=True)


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

    map_province = st.selectbox("筛选省份", ["全部"] + retriever.get_provinces(), key="map_province")
    map_category = st.selectbox("筛选分类", ["全部"] + retriever.get_categories(), key="map_category")

    filtered = mapped
    if map_province != "全部":
        filtered = [a for a in filtered if a["province"] == map_province]
    if map_category != "全部":
        filtered = [a for a in filtered if a["category"] == map_category]

    st.caption(f"显示 {len(filtered)} / {len(mapped)} 个景点（拖动/缩放地图查看）")

    cat_colors = {
        "历史文化": "#e74c3c", "自然风光": "#27ae60",
        "主题乐园": "#f39c12", "都市风情": "#3498db", "现代建筑": "#9b59b6",
    }

    saved_center = st.session_state.get("map_center", [34.0, 108.0])
    saved_zoom = st.session_state.get("map_zoom", 5)
    m = folium.Map(location=saved_center, zoom_start=saved_zoom, tiles="OpenStreetMap")
    marker_cluster = MarkerCluster().add_to(m)
    for a in filtered:
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

    map_data = st_folium(m, width=1100, height=600, key="attraction_map")

    # 保存地图中心/缩放级别，切换页面后恢复
    if map_data and map_data.get("center"):
        st.session_state.map_center = [map_data["center"]["lat"], map_data["center"]["lng"]]
    if map_data and map_data.get("zoom"):
        st.session_state.map_zoom = map_data["zoom"]

    # 点击标记后显示操作按钮
    if map_data and map_data.get("last_object_clicked"):
        lat, lon = map_data["last_object_clicked"]
        # 查找被点击的景点
        clicked_att = None
        for a in mapped:
            if a.get("location") and abs(a["location"][1] - lat) < 0.01 and abs(a["location"][0] - lon) < 0.01:
                clicked_att = a
                break
        if clicked_att:
            st.markdown(f"**📍 当前选中：{clicked_att['name']}**")
            col_a, col_b = st.columns([1, 6])
            with col_a:
                if st.button("🔍 查看详情", key="map_view_detail", use_container_width=True):
                    ask_question(f"介绍一下{clicked_att['name']}")
            with col_b:
                st.caption(f"{clicked_att['province']} {clicked_att.get('city','')} | {clicked_att['category']}")

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
        if st.button("🎲 换一批", key="rand_refresh", use_container_width=True):
            st.session_state.rand_key = st.session_state.get("rand_key", 0) + 1
            st.rerun()

    # 用 rand_key 变化触发重新随机
    _ = st.session_state.get("rand_key", 0)

    rand_atts = retriever.random_attractions(n)
    for i, att in enumerate(rand_atts):
        if i % 2 == 0:
            cols = st.columns(2)
        with cols[i % 2]:
            mini_card(att, show_fav=True)


def render_seasonal_page():
    st.markdown('<div class="main-header">🌤️ 季节推荐</div>', unsafe_allow_html=True)

    month = datetime.datetime.now().month
    if 3 <= month <= 5:
        season_cn = "🌸 春季（3-5月）"
        badge = "season-badge-spring"
        months = [3, 4, 5]
        next_months = [6, 7, 8]
        next_cn = "☀️ 夏季（6-8月）"
    elif 6 <= month <= 8:
        season_cn = "☀️ 夏季（6-8月）"
        badge = "season-badge-summer"
        months = [6, 7, 8]
        next_months = [9, 10, 11]
        next_cn = "🍂 秋季（9-11月）"
    elif 9 <= month <= 11:
        season_cn = "🍂 秋季（9-11月）"
        badge = "season-badge-autumn"
        months = [9, 10, 11]
        next_months = [12, 1, 2]
        next_cn = "❄️ 冬季（12-2月）"
    else:
        season_cn = "❄️ 冬季（12-2月）"
        badge = "season-badge-winter"
        months = [12, 1, 2]
        next_months = [3, 4, 5]
        next_cn = "🌸 春季（3-5月）"

    st.markdown(f'<span class="season-badge {badge}">{season_cn}</span>', unsafe_allow_html=True)

    def match_season(text):
        if not text:
            return False
        for m in months:
            if f"{m}月" in text:
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
        next_matched = [a for a in retriever.attractions
                        if a.get("best_season") and any(str(m) in a["best_season"] for m in next_months)]
        random.shuffle(next_matched)
        st.info(f"🌤️ 下个季节预热 — 推荐 {len(next_matched[:10])} 个景点")
        for att in next_matched[:10]:
            display_attraction_card(att)
