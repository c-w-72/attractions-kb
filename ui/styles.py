"""
CSS 样式常量 — 使用 CSS 变量实现暗色/亮色切换
"""

BASE_CSS = '''
    :root {
        --main-bg: #fff; --text-color: #000; --sub-text: #444;
        --card-bg: #fff; --card-border: #d0d0d0; --card-title: #000;
        --tag-bg: #fff; --tag-text: #333; --tag-border: #d0d0d0;
        --table-border: #ddd; --table-th-bg: #f0f2f6; --table-th-text: #000;
    }

    .main-header { font-size: 1.6rem; font-weight: 700; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; margin-bottom: 1.5rem; }
    .attraction-card {
        padding: 1.2rem; border-radius: 10px; border: 1px solid var(--card-border);
        margin-bottom: 1rem; background: var(--card-bg);
    }
    .attraction-card h3 { margin-top: 0; color: var(--card-title); }
    .tag {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: 0.8rem; margin-right: 6px; background: var(--tag-bg);
        color: var(--tag-text); border: 1px solid var(--tag-border);
    }
    .weather-card {
        padding: 0.8rem; border-radius: 10px; border: 1px solid var(--card-border);
        background: var(--card-bg); color: var(--text-color); margin-bottom: 1rem;
    }
    .weather-card .temp { font-size: 2rem; font-weight: 700; color: var(--card-title); }
    .weather-card .desc { font-size: 1rem; color: var(--sub-text); }
    .itinerary-card {
        padding: 1rem; border-radius: 10px; border: 1px solid var(--card-border);
        background: var(--card-bg); margin-bottom: 0.8rem;
    }
    .cost-card {
        padding: 0.8rem; border-radius: 10px; border: 1px solid var(--card-border);
        background: var(--card-bg); margin-bottom: 0.5rem;
    }
    .compare-table th, .compare-table td {
        border: 1px solid var(--table-border); padding: 8px; vertical-align: top;
    }
    .compare-table th { background: var(--table-th-bg); font-weight: 600; text-align: center; color: var(--table-th-text); }
    .compare-table td { font-size: 0.9rem; }
'''

DARK_CSS = '''
    :root {
        --main-bg: #1e1e1e; --text-color: #e0e0e0; --sub-text: #aaa;
        --card-bg: #1e1e1e; --card-border: #444; --card-title: #e0e0e0;
        --tag-bg: #333; --tag-text: #ccc; --tag-border: #555;
        --table-border: #444; --table-th-bg: #333; --table-th-text: #e0e0e0;
    }
'''

LIGHT_CSS = '''
    :root {
        --main-bg: #fff; --text-color: #000; --sub-text: #444;
        --card-bg: #fff; --card-border: #d0d0d0; --card-title: #000;
        --tag-bg: #fff; --tag-text: #333; --tag-border: #d0d0d0;
        --table-border: #ddd; --table-th-bg: #f0f2f6; --table-th-text: #000;
    }
'''

COMMON_CSS = '''
    .main-header { color: var(--text-color); }
    .sub-header { color: var(--sub-text); }
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
        .stButton button { font-size: 0.75rem; padding: 0.2rem 0.4rem; min-height: 2.2rem; }
        .stButton button[data-testid="baseButton-primary"] { min-height: 2.5rem; }
        .stCheckbox { min-height: 2.5rem; display: flex; align-items: center; }
        .tag { font-size: 0.7rem; padding: 1px 6px; }
        .attraction-card { padding: 0.8rem; }
        .compare-table { font-size: 0.8rem; }
        .compare-table th, .compare-table td { padding: 4px; }
        section[data-testid="stSidebar"] { width: 200px !important; min-width: 200px !important; }
        section[data-testid="stSidebar"] .stButton button { font-size: 0.7rem; }
        .main-header { font-size: 1.2rem !important; }
        .sub-header { font-size: 0.95rem !important; }
        .mini-card { font-size: 0.8rem; }
    }
    .compare-wrapper::-webkit-scrollbar { height: 6px; }
    .compare-wrapper::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }
    .mini-card {
        padding: 8px 12px; border-left: 3px solid #1f77b4; margin: 4px 0;
        background: var(--card-bg); border-radius: 0 6px 6px 6px;
    }
    .mini-card b { color: var(--card-title); }
    .mini-card-text { font-size: 0.9rem; color: var(--sub-text); }
    /* 统一提示样式 */
    div[data-testid="stAlert"] { border-radius: 8px; font-size: 0.9rem; }
    div[data-testid="stAlertContainer"] { padding: 0.5rem 0; }
    .stAlert > div[data-baseweb="notification"] { border-radius: 8px !important; }
    div[data-testid="stInfo"] { border-left-color: #1f77b4 !important; }
    div[data-testid="stWarning"] { border-left-color: #e67e22 !important; }
    div[data-testid="stError"] { border-left-color: #e74c3c !important; }
    div[data-testid="stSuccess"] { border-left-color: #27ae60 !important; }
'''
