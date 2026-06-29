"""
费用估算和行程规划单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.cost_data import estimate_trip_cost, COST_ESTIMATES
from engine.itinerary import parse_itinerary_query


class TestCostEstimate:
    def test_basic(self):
        cost = estimate_trip_cost("四川", 3)
        assert cost["province"] == "四川"
        assert cost["days"] == 3
        assert cost["总计"][0] < cost["总计"][1]

    def test_with_category(self):
        cost = estimate_trip_cost("北京", 3, "历史文化")
        assert cost["门票"][0] >= 30

    def test_default_province(self):
        cost = estimate_trip_cost("Unknown", 3)
        assert cost["province"] == "Unknown"
        assert cost["住宿"][0] > 0

    def test_all_provinces(self):
        for prov in COST_ESTIMATES:
            cost = estimate_trip_cost(prov, 1)
            assert cost["总计"][0] > 0


class TestItineraryParse:
    def test_x_day_tour(self):
        r = parse_itinerary_query("北京三日游")
        assert r["days"] == 3

    def test_day_phrase(self):
        r = parse_itinerary_query("上海5天旅游攻略")
        assert r["days"] == 5

    def test_chinese_numeral(self):
        r = parse_itinerary_query("成都五天行程")
        assert r["days"] == 5

    def test_overflow(self):
        r = parse_itinerary_query("20日游")
        assert r["days"] == 14

    def test_no_match(self):
        r = parse_itinerary_query("故宫门票多少钱")
        assert r is None
