#!/usr/bin/env python
"""Update app.py with optimizations - using raw strings"""
import os
import re

APP_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.py")

with open(APP_FILE, "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# ================================================================
# 1. Replace CSS section with dark mode version
# ================================================================
old_css_marker = "# ===== CSS ====="
old_msg_marker = "# ===== 消息处理 ====="

if old_css_marker in content and old_msg_marker in content:
    css_start = content.index(old_css_marker)
    msg_start = content.index(old_msg_marker)

    with open(APP_FILE, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    # Find the exact end of the st.markdown block (between CSS and 消息处理)
    css_block_end = msg_start
    # But we need to replace everything between CSS marker and 消息处理
    # The CSS marker is at some line, and 消息处理 is the next section
    old_block = content[css_start:msg_start]

    new_block = """# ===== 暗色模式状态 =====

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False


# ===== CSS =====

DARK_CSS = '''
    .main-header { font-size: 1.6rem; font-weight: 700; margin-bottom: 0.5rem; color: #e0e0e0; }
    .sub-header { font-size: 1.1rem; color: #aaa; margin-bottom: 1.5rem; }
    .attraction-card {
        padding: 1.2rem; border-radius: 10px; border: 1px solid #444;
        margin-bottom: 1rem; background: #1e1e1e;
    }
    .attraction-card h3 { margin-top: 0; color: #e0e0e0; }
    .tag {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: 0.8rem; margin-right: 6px; background: #333; color: #ccc;
        border: 1px solid #555;
    }
    .weather-card {
        padding: 0.8rem; border-radius: 10px; border: 1px solid #444;
        background: #1e1e1e; color: #e0e0e0; margin-bottom: 1rem;
    }
    .weather-card .temp { font-size: 2rem; font-weight: 700; color: #e0e0e0; }
    .weather-card .desc { font-size: 1rem; color: #ccc; }
    .itinerary-card {
        padding: 1rem; border-radius: 10px; border: 1px solid #444;
        background: #1e1e1e; margin-bottom: 0.8rem;
    }
    .cost-card {
        padding: 0.8rem; border-radius: 10px; border: 1px solid #444;
        background: #1e1e1e; margin-bottom: 0.5rem;
    }
    .compare-table th, .compare-table td {
        border: 1px solid #444; padding: 8px; vertical-align: top;
    }
    .compare-table th { background: #333; font-weight: 600; text-align: center; color: #e0e0e0; }
    .compare-table td { font-size: 0.9rem; }
'''

LIGHT_CSS = '''
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
    .compare-table th, .compare-table td {
        border: 1px solid #ddd; padding: 8px; vertical-align: top;
    }
    .compare-table th { background: #f0f2f6; font-weight: 600; text-align: center; color: #000; }
    .compare-table td { font-size: 0.9rem; }
'''

COMMON_CSS = '''
    .tag-rating { color: #e67e22; border-color: #f0d0a0; }
    .tag-food { color: #c62828; border-color: #e0b0b0; }
    .tag-culture { color: #6a1b9a; border-color: #c0a0d0; }
    .tag-transport { color: #00695c; border-color: #a0c0b0; }
    .tag-travel { color: #2e7d32; border-color: #a0c0a0; }
    .tag-info { color: #0d47a1; border-color: #a0b0d0; }
    .tag-fav { color: #e91e63; border-color: #e0a0b0; }
    .stButton button { font-size: 0.85rem; }
    .highlight { background: #ffe066; padding: 0 2px; border-radius: 3px; color: #000; }
    div[data-testid="stChatMessage"] { font-size: 0.95rem; line-height: 1.7; }
    div[data-testid="stChatMessageContent"] p { margin-bottom: 0.4rem; }
    div[data-testid="stChatMessageContent"] table { font-size: 0.85rem; }
    .season-badge {
        display: inline-block; padding: 4px 16px; border-radius: 20px;
        font-size: 0.95rem; font-weight: 600; margin: 8px 4px 8px 0;
    }
    .season-badge-spring { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
    .season-badge-summer { background: #fff3e0; color: #e65100; border: 1px solid #ffcc80; }
    .season-badge-autumn { background: #fce4ec; color: #c62828; border: 1px solid #ef9a9a; }
    .season-badge-winter { background: #e3f2fd; color: #0d47a1; border: 1px solid #90caf9; }
    @media (max-width: 768px) {
        .stButton button { font-size: 0.75rem; padding: 0.2rem 0.4rem; }
        .tag { font-size: 0.7rem; padding: 1px 6px; }
        .attraction-card { padding: 0.8rem; }
    }
'''

theme_css = DARK_CSS if st.session_state.dark_mode else LIGHT_CSS
st.markdown(f"<style>{theme_css}{COMMON_CSS}</style>", unsafe_allow_html=True)
"""

    content = content[:css_start] + new_block + content[msg_start:]
    changes += 1
    print("1. Dark mode CSS: OK")
else:
    print("1. Dark mode CSS: NOT FOUND")

# ================================================================
# 2. Add dark mode toggle in sidebar
# ================================================================
sidebar_target = 'stats = retriever.get_stats()'
sidebar_insert = '''
    # 暗色模式切换
    dark_toggle = st.toggle("☾ 暗色模式", value=st.session_state.dark_mode, key="dark_mode_toggle")
    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        st.rerun()

    '''
if sidebar_target in content:
    content = content.replace(sidebar_target, sidebar_insert + sidebar_target, 1)
    changes += 1
    print("2. Dark mode toggle: OK")
else:
    print("2. Dark mode toggle: NOT FOUND")

# ================================================================
# 3. Add nav items (rankings, seasonal)
# ================================================================
content = content.replace(
    '"\U0001f50d 发现": ["\U0001f50d 景点搜索", "\U0001f3b2 随机推荐"],',
    '"\U0001f50d 发现": ["\U0001f50d 景点搜索", "\U0001f3b2 随机推荐", "\U0001f3c6 热门排行"],'
)
content = content.replace(
    '"\U0001f4ca 系统": ["\U0001f4ca 数据概览"],',
    '"\U0001f4ca 系统": ["\U0001f4ca 数据概览", "\U0001f324️ 季节推荐"],'
)
changes += 1
print("3. Nav items: OK")

# ================================================================
# 4. Add seasonal page
# ================================================================
router_marker = '# ===== 页面路由 ====='
seasonal_code = '''
# ===== 页面：季节推荐 =====

def render_seasonal_page():
    st.markdown('<div class="main-header">\U0001f324️ 季节推荐</div>', unsafe_allow_html=True)

    import datetime
    month = datetime.datetime.now().month
    if 3 <= month <= 5:
        season_cn = "\U0001f338 春季（3-5月）"
        badge = "season-badge-spring"
        months = [3, 4, 5]
        next_cn = "☀️ 夏季（6-8月）"
    elif 6 <= month <= 8:
        season_cn = "☀️ 夏季（6-8月）"
        badge = "season-badge-summer"
        months = [6, 7, 8]
        next_cn = "\U0001f342 秋季（9-11月）"
    elif 9 <= month <= 11:
        season_cn = "\U0001f342 秋季（9-11月）"
        badge = "season-badge-autumn"
        months = [9, 10, 11]
        next_cn = "❄️ 冬季（12-2月）"
    else:
        season_cn = "❄️ 冬季（12-2月）"
        badge = "season-badge-winter"
        months = [12, 1, 2]
        next_cn = "\U0001f338 春季（3-5月）"

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
        matched = [a for a in retriever.attractions if match_season(a.get("best_season", ""))]
        if not matched:
            matched = retriever.attractions[:20]
        st.success(f"找到 {len(matched)} 个适合当季游览的景点")
        for att in matched[:15]:
            display_attraction_card(att)
    with tab2:
        next_matched = [a for a in retriever.attractions if match_season(a.get("best_season", ""))]
        import random
        random.shuffle(next_matched)
        st.info(f"主下个季节预热 — 推荐 {len(next_matched[:10])} 个景点")
        for att in next_matched[:10]:
            display_attraction_card(att)


'''

if router_marker in content:
    idx = content.index(router_marker)
    content = content[:idx] + seasonal_code + content[idx:]
    changes += 1
    print("4. Seasonal page: OK")

# ================================================================
# 5. Add rankings page
# ================================================================
rankings_code = '''
# ===== 页面：热门排行 =====

def render_rankings_page():
    st.markdown('<div class="main-header">\U0001f3c6 热门排行</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">基于搜索热度和评分的综合排名</div>', unsafe_allow_html=True)

    search_counts = st.session_state.get("search_counts", {})
    all_attrs = list(retriever.attractions)

    tab1, tab2, tab3 = st.tabs(["\U0001f525 搜索热度榜", "⭐ 评分榜", "\U0001f4af 综合推荐榜"])

    with tab1:
        scored = [(search_counts.get(a["name"], 0), a) for a in all_attrs]
        scored.sort(key=lambda x: x[0], reverse=True)
        top_hot = [a for c, a in scored if c > 0][:20]
        if not top_hot:
            st.info("还没有搜索数据，先去搜索景点吧！")
        else:
            for rank, att in enumerate(top_hot, 1):
                cnt = search_counts.get(att["name"], 0)
                st.markdown(f"**#{rank}** — {att['name']}（{cnt}次搜索）")
                mini_card(att)

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


'''

if router_marker in content:
    # Insert after seasonal (it was inserted before router_marker above)
    # Rankings goes right before seasonal, so insert before seasonal
    seasonal_marker = '# ===== 页面：季节推荐 ====='
    if seasonal_marker in content:
        idx = content.index(seasonal_marker)
        content = content[:idx] + rankings_code + content[idx:]
        changes += 1
        print("5. Rankings page: OK")

# ================================================================
# 6. Update page router
# ================================================================
old_router_part = '“\U0001f3b2 随机推荐”: render_random_page,'
new_router_part = old_router_part + '\n    "\U0001f3c6 热门排行": render_rankings_page,\n    "\U0001f324️ 季节推荐": render_seasonal_page,'
if old_router_part in content:
    content = content.replace(old_router_part, new_router_part)
    changes += 1
    print("6. Page router: OK")

# ================================================================
# 7. Add highlight param to display_attraction_card
# ================================================================
old_card_sig = 'def display_attraction_card(att, score=None):'
new_card_sig = 'def display_attraction_card(att, score=None, highlight=None):'
if old_card_sig in content:
    content = content.replace(old_card_sig, new_card_sig)
    changes += 1
    print("7. Card signature: OK")

# ================================================================
# 8. Add _highlight_text helper
# ================================================================
old_mini = 'def mini_card(att):'
new_helper = '''
def _highlight_text(text, query):
    """高亮显示匹配关键词"""
    if not text or not query:
        return text
    import re
    for kw in re.split(r'[\\s,,\\u3001]+', query.strip()):
        if len(kw) < 2:
            continue
        text = re.sub(f"({re.escape(kw)})", r'<span class="highlight">\\1</span>', text, flags=re.IGNORECASE)
    return text


'''
if old_mini in content:
    content = content.replace(old_mini, new_helper + old_mini)
    changes += 1
    print("8. Highlight helper: OK")

# ================================================================
# 9. Add highlighting to description in card
# ================================================================
old_desc_line = '<p>{att.get(\'description\', \'\')}</p>'
new_desc_line = '<p>{_highlight_text(att.get(\'description\', \'\'), highlight) if highlight else att.get(\'description\', \'\')}</p>'
if old_desc_line in content:
    content = content.replace(old_desc_line, new_desc_line, 1)
    changes += 1
    print("9. Description highlight: OK")

old_hl_line = '<p><b>✨ 特色：</b>{att.get(\'highlights\', \'\')}</p>'
new_hl_line = '<p><b>✨ 特色：</b>{_highlight_text(att.get(\'highlights\', \'\'), highlight) if highlight else att.get(\'highlights\', \'\')}</p>'
if old_hl_line in content:
    content = content.replace(old_hl_line, new_hl_line)
    changes += 1
    print("10. Highlights highlight: OK")

# ================================================================
# 11. Add skeleton loader
# ================================================================
if "def display_skeleton" not in content:
    skeleton_fn = '''

def display_skeleton(n=3):
    """骨架屏占位"""
    html = ""
    for _ in range(n):
        html += '<div style="height:20px;background:#f0f0f0;border-radius:4px;margin:8px 0"> </div>'
    return html


'''
    content = content.replace('# ===== 页面路由 =====', skeleton_fn + '# ===== 页面路由 =====')
    changes += 1
    print("11. Skeleton loader: OK")

# ================================================================
# 12. Add HTML export to itinerary
# ================================================================
old_export_col = 'export_col1, export_col2 = st.columns([5, 1])'
new_export_col = 'export_col1, export_col2, export_col3 = st.columns([5, 1, 1])'
if old_export_col in content:
    content = content.replace(old_export_col, new_export_col)
    changes += 1
    print("12. Export columns: OK")

# Add HTML download button after MD download
md_btn_anchor = 'mime="text/markdown",'
if md_btn_anchor in content:
    idx = content.index(md_btn_anchor) + len(md_btn_anchor)
    # Find the closing paren of the download_button call
    close_paren = content.index(")", idx)
    after_md_btn = content[close_paren + 1:]

    html_export_btn = '''
            with export_col3:
                # HTML导出（可打印为PDF）
                html_body = plan["itinerary"].replace("st.markdown(", "").replace("unsafe_allow_html=True", "").replace('"""', " ")
                html_out = '<html><head><meta charset="utf-8"><style>'
                html_out += 'body{font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px}'
                html_out += 'h1{color:#1f77b4}h2{color:#2c3e50}.day-card{border:1px solid #ddd;border-radius:8px;padding:12px;margin:10px 0}'
                html_out += '</style></head><body>'
                html_out += html_body + '</body></html>'
                st.download_button("\U0001f5a8️ HTML导出", data=html_out,
                                   file_name=f"{dest}{days}日游.html", mime="text/html",
                                   use_container_width=True)
'''
    content = content[:close_paren + 1] + html_export_btn + after_md_btn
    changes += 1
    print("13. HTML export: OK")

# ================================================================
# 14. Update image caption (task #2)
# ================================================================
old_img_caption = 'st.caption(f"来源: Wikimedia Commons · {att[\'name\']}")'
new_img_caption = 'st.caption(f"\U0001f5bc️ 图片来源: {img_url}")'
if old_img_caption in content:
    content = content.replace(old_img_caption, new_img_caption)
    changes += 1
    print("14. Image caption: OK")

with open(APP_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\nTotal changes made: {changes}")
