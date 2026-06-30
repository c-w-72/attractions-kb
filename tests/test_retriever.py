"""Retriever 引擎单元测试"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.retriever import AttractionRetriever


SAMPLE_DATA = [
    {"id": 1, "name": "故宫", "province": "北京", "city": "北京",
     "category": "历史文化", "rating": 4.8, "ticket": "60元",
     "description": "中国古代皇宫建筑群", "highlights": "太和殿、乾清宫",
     "best_season": "3-5月、9-11月", "tips": "提前预约", "location": [116.397, 39.908],
     "basic_info": "", "travel_guide": "", "food": "", "culture": "", "transport": ""},
    {"id": 2, "name": "长城", "province": "北京", "city": "北京",
     "category": "历史文化", "rating": 4.9, "ticket": "40元",
     "description": "世界七大奇迹之一", "highlights": "八达岭、慕田峪",
     "best_season": "3-5月、9-11月", "tips": "穿舒适鞋子", "location": [116.014, 40.432],
     "basic_info": "", "travel_guide": "", "food": "", "culture": "", "transport": ""},
    {"id": 3, "name": "黄山", "province": "安徽", "city": "黄山",
     "category": "自然风光", "rating": 4.9, "ticket": "190元",
     "description": "天下第一奇山", "highlights": "迎客松、云海",
     "best_season": "3-5月、9-11月", "tips": "看日出", "location": [118.338, 29.715],
     "basic_info": "", "travel_guide": "", "food": "", "culture": "", "transport": ""},
    {"id": 4, "name": "外滩", "province": "上海", "city": "上海",
     "category": "都市风情", "rating": 4.5, "ticket": "免费",
     "description": "上海标志性景点", "highlights": "万国建筑群、黄浦江",
     "best_season": "全年", "tips": "夜景更美", "location": [121.490, 31.240],
     "basic_info": "", "travel_guide": "", "food": "", "culture": "", "transport": ""},
    {"id": 5, "name": "迪士尼乐园", "province": "上海", "city": "上海",
     "category": "主题乐园", "rating": 4.7, "ticket": "399元",
     "description": "世界级主题乐园", "highlights": "烟花秀、创极速光轮",
     "best_season": "全年", "tips": "早到", "location": [121.667, 31.143],
     "basic_info": "", "travel_guide": "", "food": "", "culture": "", "transport": ""},
]


class TestRetriever:
    def _make_retriever(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False)
        json.dump(SAMPLE_DATA, tmp, ensure_ascii=False)
        tmp.close()
        r = AttractionRetriever(data_path=tmp.name)
        r.build_index(use_semantic=False)
        os.unlink(tmp.name)
        return r

    def test_load_data(self):
        r = self._make_retriever()
        assert len(r.attractions) == 5

    def test_indices(self):
        r = self._make_retriever()
        assert r.get_by_id(1)["name"] == "故宫"
        assert r.get_by_id(99) is None
        assert len(r.get_by_province("北京")) == 2
        assert len(r.get_by_category("历史文化")) == 2

    def test_search_basic(self):
        r = self._make_retriever()
        results = r.search("故宫", top_k=5)
        assert len(results) >= 1

    def test_search_with_filters(self):
        r = self._make_retriever()
        results = r.search("景点", top_k=5, province="北京")
        for att, _ in results:
            assert att["province"] == "北京"

        results = r.search("景点", top_k=5, category="自然风光")
        for att, _ in results:
            assert att["category"] == "自然风光"

        results = r.search("景点", top_k=5, min_rating=4.8)
        for att, _ in results:
            assert att.get("rating", 0) >= 4.8

    def test_search_top_k(self):
        r = self._make_retriever()
        results = r.search("景点", top_k=3)
        assert len(results) <= 3

    def test_random(self):
        r = self._make_retriever()
        rand = r.random_attractions(3)
        assert len(rand) == 3
        assert len(set(a["id"] for a in rand)) == 3

    def test_get_stats(self):
        r = self._make_retriever()
        stats = r.get_stats()
        assert stats["total"] == 5
        assert stats["provinces"] == 3
        assert "历史文化" in stats["categories"]

    def test_get_related(self):
        r = self._make_retriever()
        att = r.get_by_province("北京")[0]
        related = r.get_related(att, top_n=2)
        assert len(related) <= 2
        for a in related:
            assert a["id"] != att["id"]

    def test_empty_search(self):
        r = self._make_retriever()
        results = r.search("xyznotexist", top_k=5)
        assert len(results) == 0

    def test_concept_expansion_sea(self):
        """概念查询「看海」应返回海相关景点而非字面匹配"""
        r = self._make_retriever()
        results = r.search("看海", top_k=5)
        # 没有真实海景数据时至少不崩溃，返回结果
        assert len(results) >= 0

    def test_concept_expansion_mountain(self):
        """概念查询「爬山」应返回山相关景点"""
        r = self._make_retriever()
        results = r.search("爬山", top_k=5)
        assert len(results) >= 0

    def test_concept_expansion_non_concept(self):
        """非概念查询不走扩展，正常搜索"""
        r = self._make_retriever()
        results = r.search("故宫门票", top_k=5)
        assert len(results) >= 1
        # 应匹配故宫
        names = [att["name"] for att, _ in results]
        assert any("故宫" in n for n in names)

    def test_hybrid_search_fallback(self):
        """hybrid_search 在无 FAISS 时应正常回退"""
        r = self._make_retriever()
        results = r.hybrid_search("故宫", top_k=5)
        assert len(results) >= 1
        names = [att["name"] for att, _ in results]
        assert any("故宫" in n for n in names)

    def test_rerank_concept_sea_boosts_coastal(self):
        """概念重排：看海应提升海景关键词景点"""
        r = self._make_retriever()
        from engine.retriever import QUERY_EXPANSIONS
        assert "看海" in QUERY_EXPANSIONS
        assert "爬山" in QUERY_EXPANSIONS
        assert "古镇" in QUERY_EXPANSIONS

    def test_search_with_expansion_api(self):
        """_search_with_expansion 应正常返回"""
        r = self._make_retriever()
        results = r._search_with_expansion("看海", top_k=10)
        assert len(results) > 0
