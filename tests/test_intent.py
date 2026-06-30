"""Intent 引擎单元测试"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.retriever import AttractionRetriever
from engine.intent import IntentEngine


SAMPLE_DATA = [
    {"id": 1, "name": "故宫", "province": "北京", "city": "北京",
     "category": "历史文化", "rating": 4.8, "ticket": "60元",
     "description": "中国古代皇宫建筑群", "highlights": "太和殿、乾清宫",
     "best_season": "3-5月、9-11月", "tips": "提前预约",
     "basic_info": "", "travel_guide": "", "food": "", "culture": "", "transport": ""},
    {"id": 2, "name": "黄山", "province": "安徽", "city": "黄山",
     "category": "自然风光", "rating": 4.9, "ticket": "190元",
     "description": "天下第一奇山", "highlights": "迎客松、云海",
     "best_season": "3-5月、9-11月", "tips": "看日出",
     "basic_info": "", "travel_guide": "", "food": "", "culture": "", "transport": ""},
]


class TestIntentEngine:
    def _make_engine(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False)
        json.dump(SAMPLE_DATA, tmp, ensure_ascii=False)
        tmp.close()
        r = AttractionRetriever(data_path=tmp.name)
        os.unlink(tmp.name)
        return IntentEngine(r)

    def test_extract_province(self):
        e = self._make_engine()
        assert e.extract_province("北京") == "北京"
        assert e.extract_province("去安徽玩") == "安徽"
        assert e.extract_province("不知道去哪") is None

    def test_extract_city(self):
        e = self._make_engine()
        assert e.extract_city("黄山") == "黄山"
        assert e.extract_city("想去北京玩") == "北京"

    def test_extract_attraction(self):
        e = self._make_engine()
        assert e.extract_attraction("故宫") == "故宫"
        assert e.extract_attraction("介绍一下故宫") == "故宫"
        result = e.extract_attraction("不知道去哪")
        assert result is None or result == ""

    def test_concept_queries_not_mapped_to_category(self):
        """概念查询（看海/爬山/古镇等）不应被归为任何分类，应走搜索扩展"""
        e = self._make_engine()
        assert e.extract_category("看海") is None, "看海不应映射到自然风光"
        assert e.extract_category("爬山") is None, "爬山不应映射到自然风光"
        assert e.extract_category("古镇") is None, "古镇不应映射到历史文化"
        assert e.extract_category("避暑") is None, "避暑不应映射到自然风光"
        assert e.extract_category("夜景") is None, "夜景不应映射到都市风情"
        assert e.extract_category("亲子") is None, "亲子不应映射到主题乐园"

    def test_legitimate_category_queries_still_work(self):
        """常规分类查询应正常映射"""
        e = self._make_engine()
        assert e.extract_category("历史文化景点") == "历史文化"
        assert e.extract_category("自然风光推荐") == "自然风光"
        assert e.extract_category("主题乐园") == "主题乐园"
