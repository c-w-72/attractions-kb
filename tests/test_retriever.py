"""
Retriever 引擎单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from engine.retriever import AttractionRetriever


@pytest.fixture(scope="module")
def retriever():
    r = AttractionRetriever()
    r.build_index(use_semantic=False)
    return r


class TestIndices:
    def test_province_index(self, retriever):
        assert len(retriever._province_index) >= 30
        assert "北京" in retriever._province_index
        assert len(retriever._province_index["北京"]) >= 3

    def test_category_index(self, retriever):
        assert len(retriever._category_index) >= 5
        for cat in ["历史文化", "自然风光", "主题乐园"]:
            assert cat in retriever._category_index

    def test_name_index(self, retriever):
        assert "故宫博物院" in retriever._name_index
        assert retriever._name_index["故宫博物院"]["province"] == "北京"

    def test_id_index(self, retriever):
        for aid in [1, 2, 3]:
            assert aid in retriever._id_index


class TestSearch:
    def test_basic_search(self, retriever):
        results = retriever.search("北京", top_k=5)
        assert len(results) >= 3
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)

    def test_search_with_filters(self, retriever):
        results = retriever.search("北京", top_k=5, province="北京")
        assert all(r[0]["province"] == "北京" for r in results)

    def test_search_category_filter(self, retriever):
        results = retriever.search("自然", top_k=5, category="自然风光")
        assert all(r[0]["category"] == "自然风光" for r in results)

    def test_search_min_rating(self, retriever):
        results = retriever.search("景点", top_k=10, min_rating=4.0)
        assert all(r[0].get("rating", 0) >= 4.0 for r in results)

    def test_no_results(self, retriever):
        results = retriever.search("zzznotexist", top_k=5)
        assert len(results) == 0

    def test_cache_works(self, retriever):
        info_before = retriever._cached_search.cache_info()
        retriever.search("北京", top_k=5)
        retriever.search("北京", top_k=5)
        info_after = retriever._cached_search.cache_info()
        assert info_after.hits > info_before.hits


class TestFuzzySearch:
    def test_pinyin_beijing(self, retriever):
        results = retriever.fuzzy_search("beijing", top_k=3)
        assert len(results) >= 2
        for a, s in results:
            assert a["province"] == "北京"

    def test_pinyin_huangshan(self, retriever):
        results = retriever.fuzzy_search("huangshan", top_k=3)
        assert len(results) >= 1

    def test_pinyin_province(self, retriever):
        results = retriever.fuzzy_search("sichuan", top_k=3)
        assert len(results) >= 2
        assert all(a["province"] == "四川" for a, s in results)

    def test_partial_name(self, retriever):
        results = retriever.fuzzy_search("长城", top_k=3)
        assert len(results) >= 1


class TestGetBy:
    def test_get_by_province(self, retriever):
        atts = retriever.get_by_province("四川")
        assert len(atts) >= 3
        assert all(a["province"] == "四川" for a in atts)

    def test_get_by_category(self, retriever):
        atts = retriever.get_by_category("自然风光")
        assert len(atts) >= 5

    def test_get_by_id(self, retriever):
        att = retriever.get_by_id(1)
        assert att is not None
        assert att["id"] == 1

    def test_get_by_id_nonexistent(self, retriever):
        assert retriever.get_by_id(99999) is None


class TestRelated:
    def test_get_related(self, retriever):
        att = retriever.get_by_id(1)
        if att:
            related = retriever.get_related(att, top_n=4)
            assert len(related) <= 4
            assert all(r["id"] != att["id"] for r in related)

    def test_random(self, retriever):
        rand = retriever.random_attractions(5)
        assert len(rand) == 5
        # 检查不重复
        assert len(set(a["id"] for a in rand)) == 5


class TestStats:
    def test_get_provinces(self, retriever):
        provinces = retriever.get_provinces()
        assert len(provinces) >= 30
        assert "北京" in provinces

    def test_get_categories(self, retriever):
        cats = retriever.get_categories()
        assert len(cats) >= 5

    def test_get_stats(self, retriever):
        stats = retriever.get_stats()
        assert stats["total"] >= 180
        assert stats["provinces"] >= 30
        assert len(stats["categories"]) >= 5
