"""智能问答页面"""
import logging
import random
import streamlit as st
from engine.responder import Responder
from engine.itinerary import parse_itinerary_query, generate_itinerary
from data.persistence import clear_chat_history
from ui.components import add_message, display_followups

logger = logging.getLogger("ui.qa")


def render_qa_page():
    st.markdown('<div class="main-header">💬 智能问答</div>', unsafe_allow_html=True)

    msgs = st.session_state.messages
    max_visible = 30
    if len(msgs) > max_visible:
        with st.expander(f"📜 查看更早的消息（共 {len(msgs)} 条）", expanded=False):
            for msg in msgs[:-max_visible]:
                avatar = "🏯" if msg["role"] == "assistant" else "👤"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])
        for msg in msgs[-max_visible:]:
            avatar = "🏯" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
    else:
        for msg in msgs:
            avatar = "🏯" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_query = st.session_state.messages[-1]["content"]

        with st.chat_message("assistant", avatar="🏯"):
            with st.spinner("🔍 思考中..."):
                itinerary_info = parse_itinerary_query(last_query)
                if itinerary_info:
                    retriever = st.session_state.retriever
                    responder = st.session_state.responder
                    intent_engine = st.session_state.intent_engine
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
                        add_message("assistant", content, followups=followups)
                        st.rerun()

                retriever = st.session_state.retriever
                responder = st.session_state.responder
                intent_engine = st.session_state.intent_engine
                ctx = responder.context.to_dict() if responder.context else None
                entities = intent_engine.extract_all(last_query, ctx)
                try:
                    result = responder.generate(last_query, entities)
                except Exception:
                    logger.exception("generate() failed")
                    result = {"answer": "抱歉，处理问题时出现异常，请重试。", "followups": []}

            st.markdown(result["answer"])

        add_message("assistant", result["answer"], followups=result.get("followups", []))
        st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        followups = st.session_state.messages[-1].get("followups", [])
        if followups:
            display_followups(followups)

    prompt = st.chat_input("输入你的旅游问题...")
    if prompt:
        add_message("user", prompt)
        # 不立即 rerun — 让当前渲染流程一并处理回答生成，减少一次重绘

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
                    add_message("user", example)
                    st.rerun()

    if len(st.session_state.messages) > 1:
        st.markdown("---")
        cols = st.columns([1, 1, 1, 5])
        with cols[0]:
            if st.button("🗑️ 清除对话", use_container_width=True):
                st.session_state.messages = []
                st.session_state.welcome_shown = False
                st.session_state.responder = Responder(st.session_state.retriever)
                clear_chat_history()
                st.rerun()
        with cols[1]:
            if st.button("🎲 换个推荐", use_container_width=True):
                rand_att = random.choice(st.session_state.retriever.attractions)
                add_message("user", f"介绍一下{rand_att['name']}")
                st.rerun()
        with cols[2]:
            export_md = "\n\n".join(
                f"**{'🏯 助手' if m['role'] == 'assistant' else '👤 我'}**\n\n{m['content']}"
                for m in st.session_state.messages
            )
            st.download_button("📤 导出对话", data=export_md,
                               file_name="旅游问答记录.md", mime="text/markdown",
                               use_container_width=True)
