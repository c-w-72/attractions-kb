"""工具类页面：对比、行程规划、收藏、费用估算、数据概览、热门排行"""
import html
import streamlit as st
from engine.itinerary import generate_itinerary
from data.persistence import load_favorites, toggle_favorite, save_note, batch_remove_favorites
from data.cost_data import estimate_trip_cost, COST_ESTIMATES
from ui.components import (
    ask_question, display_attraction_card, display_cost_estimate,
    mini_card, _get_favorites_set, _invalidate_favorites,
)
from engine.monitor import get_stats as get_perf_stats


def render_compare_page():
    st.markdown('<div class="main-header">📊 景点对比</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">选择2-4个景点，多维度对比</div>', unsafe_allow_html=True)

    retriever = st.session_state.retriever
    selected = st.multiselect(
        "选择要对比的景点（2-4个）",
        [a["name"] for a in retriever.attractions],
        max_selections=4,
    )
    if len(selected) < 2:
        st.info("请至少选择 2 个景点")
        return

    atts = [retriever.get_by_name(n) for n in selected]
    atts = [a for a in atts if a]

    all_fields = [
        ("省份", "province"), ("城市", "city"), ("分类", "category"),
        ("评分", "rating"), ("门票", "ticket"), ("最佳季节", "best_season"),
        ("特色亮点", "highlights"), ("简介", "description"),
        ("基础信息", "basic_info"), ("游玩攻略", "travel_guide"),
        ("交通住宿", "transport"), ("文化特色", "culture"), ("美食特产", "food"),
    ]
    selected_fields = st.multiselect(
        "选择要对比的维度",
        [f[0] for f in all_fields],
        default=[f[0] for f in all_fields],
        key="compare_fields",
    )
    fields = [(l, k) for l, k in all_fields if l in selected_fields]

    if not fields:
        st.info("请至少选择一个对比维度")
        return

    table_html = '<div class="compare-wrapper" style="overflow-x:auto;max-width:100%">'
    table_html += '<table class="compare-table"><tr><th style="width:100px">对比项</th>'
    for att in atts:
        table_html += f"<th>{att['name']}</th>"
    table_html += "</tr>"
    for label, field in fields:
        table_html += f"<tr><td><b>{label}</b></td>"
        for att in atts:
            val = att.get(field, "")
            if field == "rating":
                val = f"{'⭐' * int(round(val or 0))} {val}"
            text = str(val)
            table_html += f"<td>{text[:200]}{'<span style=\"color:#999\"> ...</span>' if len(text) > 200 else ''}</td>"
        table_html += "</tr>"
    table_html += "</table></div>"
    st.markdown(table_html, unsafe_allow_html=True)


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

        retriever = st.session_state.retriever
        intent_engine = st.session_state.intent_engine
        query = f"{dest}{days}日游"
        province = intent_engine.extract_province(dest) or dest
        city = intent_engine.extract_city(dest)

        plan = generate_itinerary(retriever.attractions, query,
                                  province=province, city=city, days=days)

        if plan:
            export_col1, export_col2, export_col3 = st.columns([5, 1, 1])
            with export_col2:
                st.download_button("📥 导出行程", data=plan["itinerary"],
                                   file_name=f"{dest}{days}日游.md", mime="text/markdown",
                                   use_container_width=True)
            with export_col3:
                body = html.escape(plan["itinerary"])
                # 基本 markdown → HTML 转换（支持 ###, **, ---, 换行）
                body = body.replace("### ", "<h3>").replace("\n", "<br>")
                body = body.replace("**", "<b>", 1)  # 不完美但比 replace() 安全
                html_out = '<html><head><meta charset="utf-8"><style>'
                html_out += 'body{font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px;line-height:1.8}'
                html_out += 'h3{color:#1f77b4}br{content:"";display:block;margin:4px 0}'
                html_out += '</style></head><body>'
                html_out += body + '</body></html>'
                st.download_button("🖨️ HTML导出", data=html_out,
                                   file_name=f"{dest}{days}日游.html", mime="text/html",
                                   use_container_width=True)

            st.markdown(plan["itinerary"], unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("##### 💰 费用估算")
            cost = estimate_trip_cost(province, days)
            display_cost_estimate(cost)

            cost_col1, cost_col2, cost_col3 = st.columns([3, 1, 6])
            with cost_col2:
                if st.button("📊 详细估算", key="iti_cost_detail", use_container_width=True):
                    st.session_state.cost_province = province
                    st.session_state.cost_days = days
                    st.session_state.nav_selected = "💰 费用估算"
                    st.rerun()

            st.markdown("---")
            for day in plan.get("plan", []):
                for a in day.get("attractions", []):
                    if st.button(f"问AI关于「{a['name']}」", key=f"iti_{a['id']}", use_container_width=True):
                        ask_question(f"介绍一下{a['name']}")
        else:
            st.warning(f"未找到 {dest} 的景点数据，试试其他目的地")


def render_favorites_page():
    st.markdown('<div class="main-header">⭐ 我的收藏</div>', unsafe_allow_html=True)
    data = load_favorites()
    favs = data["favorites"]
    notes = data["notes"]

    if not favs:
        st.info("还没有收藏景点，浏览景点时点击 ⭐ 收藏即可添加")
        return

    st.markdown(f"共收藏 **{len(favs)}** 个景点")

    # 收藏搜索
    fav_search = st.text_input("🔍 搜索收藏", placeholder="输入景点名称筛选...",
                                label_visibility="collapsed", key="fav_search_input")
    if fav_search:
        q = fav_search.lower()
        favs = [n for n in favs if q in n.lower()]
        if not favs:
            st.info(f"未找到匹配「{fav_search}」的收藏景点")
            return
        st.caption(f"找到 {len(favs)} 个匹配的收藏")

    # 排序
    retriever = st.session_state.retriever
    sort_by = st.selectbox("排序", ["默认", "名称 A-Z", "评分从高到低", "评分从低到高"],
                            key="fav_sort", label_visibility="collapsed")
    if sort_by == "名称 A-Z":
        favs = sorted(favs)
    elif sort_by == "评分从高到低":
        favs = sorted(favs, key=lambda n: (retriever.get_by_name(n) or {}).get("rating", 0) or 0, reverse=True)
    elif sort_by == "评分从低到高":
        favs = sorted(favs, key=lambda n: (retriever.get_by_name(n) or {}).get("rating", 0) or 0)

    # 批量操作栏
    if "fav_select_all" not in st.session_state:
        st.session_state.fav_select_all = False
    if "fav_selected" not in st.session_state:
        st.session_state.fav_selected = set()

    batch_col1, batch_col2, batch_col3 = st.columns([1, 1, 6])
    with batch_col1:
        page_favs = page_names  # 当前页的收藏
        all_selected = st.checkbox("全选", value=st.session_state.fav_select_all,
                                   key="fav_select_all_checkbox",
                                   help="选择/取消当前页的全部收藏")
        if all_selected != st.session_state.fav_select_all:
            st.session_state.fav_select_all = all_selected
            if all_selected:
                st.session_state.fav_selected.update(page_favs)
            else:
                st.session_state.fav_selected.difference_update(page_favs)
            st.rerun()
    with batch_col2:
        if st.button("🗑️ 批量删除", type="primary", use_container_width=True,
                     disabled=not st.session_state.fav_selected):
            if st.session_state.fav_selected:
                batch_remove_favorites(list(st.session_state.fav_selected))
                _invalidate_favorites()
                st.session_state.fav_selected = set()
                st.session_state.fav_select_all = False
                st.rerun()
    with batch_col3:
        if st.session_state.fav_selected:
            st.caption(f"已选 {len(st.session_state.fav_selected)} 项")

    retriever = st.session_state.retriever
    # 分页显示收藏，每页 20 条
    per_page = 20
    total_pages = max(1, (len(favs) + per_page - 1) // per_page)
    fp_key = "fav_page"
    if fp_key not in st.session_state:
        st.session_state[fp_key] = 1
    st.session_state[fp_key] = min(st.session_state[fp_key], total_pages)
    fp = st.session_state[fp_key]
    start_idx = (fp - 1) * per_page
    end_idx = min(start_idx + per_page, len(favs))
    page_names = favs[start_idx:end_idx]

    # 页数导航
    if total_pages > 1:
        nav_cols = st.columns([4, 1, 1, 1, 4])
        with nav_cols[1]:
            if st.button("◀", disabled=fp <= 1, use_container_width=True):
                st.session_state[fp_key] = fp - 1
                st.rerun()
        with nav_cols[2]:
            st.markdown(f"<div style='text-align:center'>{fp}/{total_pages}</div>", unsafe_allow_html=True)
        with nav_cols[3]:
            if st.button("▶", disabled=fp >= total_pages, use_container_width=True):
                st.session_state[fp_key] = fp + 1
                st.rerun()

    st.caption(f"当前页 {len(page_names)} 项" + (f"，已选 {len(st.session_state.fav_selected)} 项" if st.session_state.fav_selected else ""))

    for name in page_names:
        att = retriever.get_by_name(name)
        if not att:
            continue

        selected = name in st.session_state.fav_selected
        col_sel, col_main = st.columns([1, 20])
        with col_sel:
            checked = st.checkbox("", value=selected, key=f"sel_{name}",
                                  label_visibility="collapsed")
            if checked != selected:
                if checked:
                    st.session_state.fav_selected.add(name)
                else:
                    st.session_state.fav_selected.discard(name)
                    st.session_state.fav_select_all = False
                st.rerun()

        with col_main:
            show_note_key = f"show_note_{name}"
            note = notes.get(name, "")
            with st.expander(f"⭐ {name} — {att['province']} {att.get('city', '')}", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    new_note = st.text_area("📝 旅行笔记", value=note,
                                            placeholder="添加你的旅行笔记...",
                                            key=f"note_{name}")
                    if new_note != note:
                        save_note(name, new_note)
                with col2:
                    if st.button("🗑️ 取消收藏", key=f"unfav_{name}", use_container_width=True):
                        toggle_favorite(name)
                        _invalidate_favorites()
                        st.session_state.fav_selected.discard(name)
                        st.rerun()
                    if st.button("💬 问AI", key=f"fav_q_{name}", use_container_width=True):
                        ask_question(f"介绍一下{name}")
                if note:
                    st.markdown(f"**📝 笔记：** {note}")


def render_cost_page():
    st.markdown('<div class="main-header">💰 费用估算</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">按省份和天数的旅行费用估算参考</div>', unsafe_allow_html=True)

    provinces = list(COST_ESTIMATES.keys())
    default_province = st.session_state.pop("cost_province", "四川")
    default_days = st.session_state.pop("cost_days", 3)
    col1, col2, col3 = st.columns(3)
    with col1:
        province = st.selectbox("目的地省份", provinces,
                                 index=provinces.index(default_province) if default_province in provinces else provinces.index("四川"))
    with col2:
        days = st.number_input("旅行天数", min_value=1, max_value=30, value=default_days)
    with col3:
        people = st.number_input("人数", min_value=1, max_value=20, value=1)

    category = st.selectbox("景点类型偏好", ["全部"] + list(st.session_state.retriever.get_categories()))

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


def render_stats_page():
    st.markdown('<div class="main-header">📊 数据概览</div>', unsafe_allow_html=True)
    retriever = st.session_state.retriever
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
    st.markdown("##### 评分分布")
    rating_buckets = {i: 0 for i in range(1, 6)}
    for a in retriever.attractions:
        r = int(round(a.get("rating", 0) or 0))
        if 1 <= r <= 5:
            rating_buckets[r] += 1
    max_r = max(rating_buckets.values()) or 1
    r_cols = st.columns(5)
    for i in range(1, 6):
        cnt = rating_buckets[i]
        bar_h = int(cnt / max_r * 80)
        with r_cols[i - 1]:
            st.markdown(
                f"<div style='text-align:center;font-size:0.85rem'>"
                f"{'⭐' * i}</div>"
                f"<div style='display:flex;flex-direction:column;align-items:center;"
                f"justify-content:flex-end;height:100px'>"
                f"<div style='background:#1f77b4;width:60%;height:{bar_h}px;"
                f"border-radius:4px 4px 0 0;min-height:4px'></div></div>"
                f"<div style='text-align:center;font-size:0.8rem;color:var(--sub-text)'>{cnt}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("##### 系统信息")
    st.markdown(f"- 检索方式: {'TF-IDF + 语义融合' if has_semantic else 'TF-IDF 字段加权'}")
        st.markdown("- 意图识别: 优先级规则 + 150+别名库 + 共指消解")
        st.markdown(f"- 景点数: {stats['total']} | 覆盖 {stats['provinces']} 省")

    perf = get_perf_stats()
    if perf.counts:
        st.markdown("---")
        st.markdown("##### ⚡ 运行时性能")
        for key in sorted(perf.counts):
            n = perf.counts[key]
            total = perf.totals[key]
            avg = total / n if n else 0
            st.markdown(f"- **{key}**: {n}次 | 总计 {total:.1f}s | 平均 {avg:.2f}s | 最慢 {perf.maxes[key]:.2f}s")


def render_rankings_page():
    st.markdown('<div class="main-header">🏆 热门排行</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">基于搜索热度和评分的综合排名</div>', unsafe_allow_html=True)

    search_counts = st.session_state.get("search_counts", {})
    retriever = st.session_state.retriever
    all_attrs = list(retriever.attractions)

    tab1, tab2, tab3 = st.tabs(["🔥 搜索热度榜", "⭐ 评分榜", "💯 综合推荐榜"])

    with tab1:
        scored = [(search_counts.get(a["name"], 0), a) for a in all_attrs]
        scored.sort(key=lambda x: x[0], reverse=True)
        top_hot = [a for c, a in scored if c > 0][:20]
        if not top_hot:
            st.info("暂时还没有搜索数据，以下按评分排序推荐：")
            cold = sorted(all_attrs, key=lambda a: a.get("rating", 0) or 0, reverse=True)[:10]
            for rank, att in enumerate(cold, 1):
                stars = "⭐" * int(round(att.get("rating", 0) or 0))
                st.markdown(f"**#{rank}** — {att['name']} {stars} {att.get('rating', '')}")
                mini_card(att, show_fav=True)
        else:
            for rank, att in enumerate(top_hot, 1):
                cnt = search_counts.get(att["name"], 0)
                st.markdown(f"**#{rank}** — {att['name']}（{cnt}次搜索）")
                mini_card(att, show_fav=True)

    with tab2:
        by_rating = sorted(all_attrs, key=lambda a: a.get("rating", 0) or 0, reverse=True)[:20]
        for rank, att in enumerate(by_rating, 1):
            stars = "⭐" * int(round(att.get("rating", 0) or 0))
            st.markdown(f"**#{rank}** — {att['name']} {stars} {att.get('rating', '')}")
            mini_card(att)

    with tab3:
        max_count = max(search_counts.values()) if search_counts else 1
        scored = []
        for a in all_attrs:
            hot_score = search_counts.get(a["name"], 0) / max_count * 0.3
            rating = a.get("rating", 0) or 0
            rating_score = rating / 5.0 * 0.7
            scored.append((hot_score + rating_score, a))
        scored.sort(key=lambda x: x[0], reverse=True)
        for rank, (score, att) in enumerate(scored[:20], 1):
            pct = int(score * 100)
            st.markdown(f"**#{rank}** — {att['name']}（综合 {pct}%）")
            display_attraction_card(att)
