"""页面包 — 将渲染函数拆分为独立模块"""
import streamlit as st
from .qa import render_qa_page
from .browse import render_search_page, render_province_page, render_category_page
from .browse import render_random_page, render_map_page, render_seasonal_page
from .tools import render_compare_page, render_itinerary_page, render_favorites_page
from .tools import render_cost_page, render_stats_page, render_rankings_page

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
    "🏆 热门排行": render_rankings_page,
    "🌤️ 季节推荐": render_seasonal_page,
}
