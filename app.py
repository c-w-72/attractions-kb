"""
中国旅游景点知识库问答系统
- 五大咨询场景 + 多轮对话 + 跟进推送
- 语义检索 + 行程规划 + 附近景点
- 景点地图 + 对比 + 收藏 + 费用估算 + 天气 + 图片
"""

import os
import logging

import streamlit as st

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("app")

from engine.retriever import AttractionRetriever
from engine.intent import IntentEngine
from engine.responder import Responder
from data.persistence import load_favorites, load_chat_history, save_chat_message, clear_chat_history
from ui.styles import BASE_CSS, DARK_CSS, LIGHT_CSS, COMMON_CSS
from ui.pages import PAGE_ROUTER

st.set_page_config(
    page_title="中国旅游景点知识库",
    page_icon="🏯",
    layout="wide",
)


# ===== 初始化引擎 =====

@st.cache_resource
def init_retriever():
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

    progress = st.progress(0, text="📂 加载景点数据...")
    r = AttractionRetriever()
    r.build_index(use_semantic=False, progress_callback=lambda p, m: progress.progress(p, text=m))
    try:
        r._try_build_semantic()
    except Exception:
        pass
    progress.empty()
    return r


def init_session():
    if "retriever" not in st.session_state:
        retriever = init_retriever()
        st.session_state.retriever = retriever
        st.session_state.intent_engine = IntentEngine(retriever)
        st.session_state.responder = Responder(retriever)
        st.session_state.messages = load_chat_history()
        st.session_state.followups = []

    if "welcome_shown" not in st.session_state:
        if not st.session_state.messages:
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


# ===== 暗色模式 / LLM 模式 =====

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "llm_enabled" not in st.session_state:
    st.session_state.llm_enabled = False

theme_css = DARK_CSS if st.session_state.dark_mode else LIGHT_CSS
st.markdown(f"<style>{BASE_CSS}{theme_css}{COMMON_CSS}</style>", unsafe_allow_html=True)

# 键盘快捷键
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    // / → 聚焦搜索框 (不在输入框中时)
    if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
        e.preventDefault();
        var inputs = document.querySelectorAll('input[placeholder*="关键词"], input[placeholder*="搜索"]');
        if (inputs.length > 0) inputs[0].focus();
    }
    // ? → 显示快捷键帮助
    if (e.key === '?' && !['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
        e.preventDefault();
        alert('⌨️ 快捷键\\n/ 聚焦搜索\\n? 显示帮助');
    }
});
</script>
""", unsafe_allow_html=True)


# ===== 侧边栏 =====

with st.sidebar:
    st.markdown("## 🏯 旅游知识库")

    nav_categories = {
        "🔍 发现": ["🔍 景点搜索", "🎲 随机推荐", "🏆 热门排行"],
        "🗺️ 浏览": ["🗺️ 按省份浏览", "📂 按分类浏览", "🗺️ 景点地图", "📊 景点对比"],
        "🛠️ 规划": ["🗺️ 行程规划", "💰 费用估算", "⭐ 我的收藏"],
        "📊 系统": ["📊 数据概览", "🌤️ 季节推荐"],
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

    col1, col2 = st.columns(2)
    with col1:
        dark_toggle = st.toggle("☾ 暗色", value=st.session_state.dark_mode, key="dark_mode_toggle")
        if dark_toggle != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_toggle
            st.rerun()
    with col2:
        llm_on = st.toggle("🤖 LLM", value=st.session_state.llm_enabled, key="llm_toggle")
        if llm_on != st.session_state.llm_enabled:
            st.session_state.llm_enabled = llm_on
            st.rerun()

    from engine.llm import get_llm
    _llm = get_llm()
    if _llm is not None:
        api_name = "Claude" if hasattr(_llm, "MODEL") and "claude" in _llm.MODEL else "GPT"
        st.caption(f"🤖 LLM 回答已启用 ({api_name})" if llm_on else "🤖 LLM 回答已关闭")
    else:
        st.caption("⚠️ LLM 未配置 (设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY)")

    retriever = st.session_state.retriever
    stats = retriever.get_stats()
    if "fav_names" in st.session_state and st.session_state.fav_names is not None:
        fav_count = len(st.session_state.fav_names)
    else:
        fav_count = len(load_favorites()["favorites"])
    st.markdown(f"⭐ **已收藏**: {fav_count} 个景点")
    with st.expander("📊 数据统计", expanded=False):
        st.markdown(f"- **景点总数**: {stats['total']} 个")
        st.markdown(f"- **覆盖省份**: {stats['provinces']} 个")
        has_semantic = hasattr(retriever, "_semantic_embedder")
        st.markdown(f"- **语义检索**: {'✅ 已启用' if has_semantic else '❌ 未启用'}")
        if not has_semantic:
            if st.button("📦 安装语义检索", help="安装 sentence-transformers + faiss 以启用语义搜索", use_container_width=True):
                st.code("pip install sentence-transformers faiss-cpu", language="bash")
        for cat in stats["categories"]:
            cnt = len(retriever.get_by_category(cat))
            st.markdown(f"- {cat}: {cnt}个")

    st.markdown("---")
    st.caption("💡 问答页面支持「北京3日游」等行程规划问题")


# ===== 页面路由 =====

render_fn = PAGE_ROUTER.get(page, PAGE_ROUTER["💬 智能问答"])
render_fn()
