"""geo.py 单元测试 — haversine + get_nearby_attractions"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.geo import haversine, get_nearby_attractions


SAMPLE = [
    {"id": 1, "name": "故宫", "province": "北京", "category": "历史文化",
     "location": [116.397, 39.908]},
    {"id": 2, "name": "天坛", "province": "北京", "category": "历史文化",
     "location": [116.407, 39.882]},
    {"id": 3, "name": "黄山", "province": "安徽", "category": "自然风光",
     "location": [118.338, 29.715]},
    {"id": 4, "name": "外滩", "province": "上海", "category": "都市风情",
     "location": [121.490, 31.240]},
    {"id": 5, "name": "无坐标景点", "province": "北京", "category": "其他",
     "location": None},
]


class TestHaversine:
    def test_same_point(self):
        assert haversine(116.397, 39.908, 116.397, 39.908) == 0.0

    def test_beijing_to_shanghai(self):
        # 北京→上海 约 1060km
        d = haversine(116.397, 39.908, 121.490, 31.240)
        assert 1000 < d < 1200

    def test_known_distance(self):
        d = haversine(0, 0, 0, 1)
        assert 110 < d < 112  # ~111km/度

    def test_negative_coords(self):
        d = haversine(-0.1, 51.5, 0.1, 51.5)
        assert 0 < d < 20


class TestGetNearby:
    def test_basic_nearby(self):
        nearby = get_nearby_attractions(SAMPLE, SAMPLE[0], top_n=3)
        assert len(nearby) >= 1
        # 天坛离故宫最近
        assert nearby[0][0]["id"] == 2

    def test_top_n(self):
        nearby = get_nearby_attractions(SAMPLE, SAMPLE[0], top_n=2)
        assert len(nearby) <= 2

    def test_no_location(self):
        nearby = get_nearby_attractions(SAMPLE, SAMPLE[4], top_n=3)
        assert nearby == []

    def test_max_dist(self):
        nearby = get_nearby_attractions(SAMPLE, SAMPLE[0], top_n=5, max_dist=10)
        for a, d in nearby:
            assert d <= 10
