# 🇨🇳 中国旅游景点知识库问答系统

基于 Streamlit 的交互式旅游景点问答系统，覆盖全国 505 个景点、34 个省份，支持景点搜索、行程规划、费用估算、智能问答等功能。

## 快速开始

```bash
pip install -r requirements.txt
streamlit run app.py
```

打开 http://localhost:8501 即可使用。

## 功能概览

| 功能 | 说明 |
|------|------|
| 💬 **智能问答** | 自然语言提问，支持多轮对话 + 跟进推荐 |
| 🔍 **景点搜索** | 关键词/省份/分类/评分筛选，拼音纠错容错 |
| 🗺️ **行程规划** | 输入目的地和天数，自动生成多日行程 |
| 📊 **景点对比** | 选 2-4 个景点多维度横向对比 |
| ⭐ **我的收藏** | 收藏景点 + 批量管理 + 旅行笔记 |
| 🗺️ **景点地图** | 全国景点 folium 交互地图（MarkerCluster） |
| 💰 **费用估算** | 按省份/天数的旅行费用估算 |
| 🌤️ **季节推荐** | 基于当月推荐最佳游览景点 |
| 🏆 **热门排行** | 搜索热度 + 评分综合排名 |
| 🎲 **随机推荐** | 随机浏览景点发现新目的地 |

## LLM 智能回答

设置环境变量以启用 AI 回答（在侧边栏切换 🤖 开关）：

```bash
# 方式一：Anthropic Claude
export ANTHROPIC_API_KEY=sk-ant-...

# 方式二：OpenAI GPT
export OPENAI_API_KEY=sk-...
```

未配置时使用模板引擎回答，核心功能不受影响。

## 搜索原理

1. **字段加权 TF-IDF** — 景点名称(权重5)、亮点(3)、省份/城市(2) 等多字段分别向量化
2. **FAISS 语义索引**（可选） — 若安装 `sentence-transformers` + `faiss`，自动启用语义检索
3. **拼音纠错** — 零结果时自动拼音模糊匹配
4. **混合检索（RRF融合）** — 语义 + TF-IDF 结果排序融合

## 项目结构

```
attractions_kb/
├── app.py                 # 入口：页面配置、侧边栏、路由
├── run.bat                # 一键启动脚本（Windows）
├── requirements.txt       # 依赖清单
├── engine/                # 核心引擎
│   ├── retriever.py       # 检索引擎（TF-IDF / FAISS / 拼音）
│   ├── intent.py          # 意图识别（省份/城市/景点/场景）
│   ├── responder.py       # 问答生成（模板 + LLM）
│   ├── llm.py             # LLM 接口（Claude / OpenAI）
│   ├── monitor.py         # 性能监控（Timer / Stats）
│   ├── external.py        # 外部 API（天气 / 图片）
│   ├── geo.py             # 地理工具（haversine / 附近）
│   └── itinerary.py       # 行程规划生成
├── ui/                    # 前端组件
│   ├── styles.py          # CSS 变量主题（暗色/亮色）
│   ├── components.py      # 通用组件（卡片/收藏/天气/图片）
│   └── pages/             # 页面路由包
│       ├── qa.py          # 智能问答页
│       ├── browse.py      # 搜索/浏览/地图/季节页
│       └── tools.py       # 对比/行程/收藏/费用/排行页
├── data/                  # 数据
│   ├── attractions.json   # 505 个景点数据（含GPS坐标）
│   ├── cost_data.py       # 费用估算数据
│   └── cache/             # 索引缓存（自动生成）
└── tests/                 # 单元测试
    ├── test_retriever.py
    ├── test_responder.py
    ├── test_intent.py
    ├── test_cost.py
    ├── test_persistence.py
    ├── test_geo.py
    └── test_monitor.py
```

## 测试

```bash
pip install pytest
pytest tests/ -v
```
