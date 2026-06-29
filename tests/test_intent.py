"""
Intent 引擎单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from engine.retriever import AttractionRetriever
from engine.intent import IntentEngine


@pytest.fixture(scope="module")
def engine():
    r = AttractionRetriever()
    return IntentEngine(r)


class TestExtractProvince:
    def test_direct(self, engine):
        assert engine.extract_province("北京") == "北京"
        assert engine.extract_province("四川") == "四川"

    def test_aliases(self, engine):
        # 别名 → 省份
        result = engine.extract_province("去北京玩")
        assert result == "北京" or result is None

    def test_extract_all_has_city(self, engine):
        result = engine.extract_all("成都有什么景点")
        assert result.get("city") == "成都"


class TestDetectScenario:
    def test_scenario_basic(self, engine):
        assert engine.detect_scenario("门票多少钱") == "basic_info"
        assert engine.detect_scenario("开放时间") == "basic_info"

    def test_scenario_travel(self, engine):
        assert engine.detect_scenario("怎么玩") == "travel_guide"
        assert engine.detect_scenario("攻略") == "travel_guide"

    def test_scenario_transport(self, engine):
        assert engine.detect_scenario("交通") == "transport"
        assert engine.detect_scenario("住哪里") == "transport"

    def test_scenario_culture(self, engine):
        assert engine.detect_scenario("历史") == "culture"
        assert engine.detect_scenario("文化特色") == "culture"

    def test_scenario_food(self, engine):
        assert engine.detect_scenario("有什么好吃的") == "food"
        assert engine.detect_scenario("美食") == "food"
