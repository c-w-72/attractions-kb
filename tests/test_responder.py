"""
Responder 引擎单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from engine.retriever import AttractionRetriever
from engine.responder import Responder


@pytest.fixture(scope="module")
def responder():
    r = AttractionRetriever()
    r.build_index(use_semantic=False)
    return Responder(r)


class TestSingleAttraction:
    def test_basic_info(self, responder):
        entities = {
            "attraction_name": "故宫博物院",
            "scenario": "basic_info",
            "province": "北京",
        }
        result = responder.generate("介绍一下故宫博物院", entities)
        assert "故宫博物院" in result["answer"]
        assert len(result["followups"]) >= 2

    def test_travel_guide(self, responder):
        entities = {
            "attraction_name": "黄山",
            "scenario": "travel_guide",
            "province": "安徽",
        }
        result = responder.generate("黄山怎么玩", entities)
        assert "黄山" in result["answer"]

    def test_culture(self, responder):
        entities = {
            "attraction_name": "丽江古城",
            "scenario": "culture",
            "province": "云南",
        }
        result = responder.generate("丽江文化", entities)
        assert "丽江古城" in result["answer"]

    def test_food(self, responder):
        entities = {
            "attraction_name": "西安回民街",
            "scenario": "food",
            "province": "陕西",
        }
        result = responder.generate("西安美食", entities)
        assert len(result["answer"]) > 0

    def test_general(self, responder):
        entities = {"attraction_name": "九寨沟", "scenario": "general", "province": "四川"}
        result = responder.generate("九寨沟介绍", entities)
        assert "九寨沟" in result["answer"]
        assert len(result["followups"]) >= 2


class TestByProvince:
    def test_province_list(self, responder):
        entities = {"province": "四川", "scenario": "general"}
        result = responder.generate("四川有什么景点", entities)
        assert "四川" in result["answer"]
        assert len(result["answer"]) > 100

    def test_province_with_category(self, responder):
        entities = {"province": "北京", "category": "历史文化", "scenario": "general"}
        result = responder.generate("北京历史景点", entities)
        assert len(result["answer"]) > 50


class TestByCategory:
    def test_category_list(self, responder):
        entities = {"category": "自然风光", "scenario": "general"}
        result = responder.generate("自然风光景点", entities)
        assert "自然风光" in result["answer"]

    def test_category_with_season(self, responder):
        entities = {"category": "自然风光", "scenario": "general", "season": "夏季"}
        result = responder.generate("夏季自然风光", entities)
        assert len(result["answer"]) > 50


class TestFreeSearch:
    def test_search_high_match(self, responder):
        entities = {"scenario": "general"}
        result = responder.generate("天坛", entities)
        assert len(result["answer"]) > 50

    def test_search_no_result(self, responder):
        entities = {"scenario": "general"}
        result = responder.generate("zzznotexist", entities)
        assert "抱歉" in result["answer"]


class TestStreaming:
    def test_stream_basic(self, responder):
        entities = {"attraction_name": "故宫博物院", "scenario": "basic_info", "province": "北京"}
        parts = list(responder.generate_stream("故宫", entities))
        types = [p[0] for p in parts]
        assert "status" in types
        assert "content" in types
        assert "followups" in types

    def test_stream_has_content(self, responder):
        entities = {"province": "北京", "scenario": "general"}
        parts = list(responder.generate_stream("北京", entities))
        for t, c in parts:
            if t == "content":
                assert len(c) > 50

    def test_stream_no_match(self, responder):
        entities = {"scenario": "general"}
        parts = list(responder.generate_stream("zzznotexist", entities))
        found = False
        for t, c in parts:
            if t == "content" and "抱歉" in c:
                found = True
        assert found


class TestContextFollowups:
    def test_context_followups_has_name(self, responder):
        info = {"attraction_name": "故宫博物院", "scenario": "basic_info", "province": "北京", "type": "single"}
        followups = responder._generate_context_followups(info)
        assert len(followups) >= 2
        assert any("故宫" in q for q in followups)

    def test_context_followups_province(self, responder):
        info = {"province": "四川", "type": "province_list"}
        followups = responder._generate_context_followups(info)
        assert len(followups) >= 2
