"""monitor.py 单元测试 — Timer, Stats, timed"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.monitor import Timer, Stats, timed, get_stats


class TestStats:
    def test_record(self):
        stats = Stats()
        stats.record("search", 0.5)
        stats.record("search", 1.5)
        assert stats.counts["search"] == 2
        assert stats.totals["search"] == 2.0
        assert stats.maxes["search"] == 1.5

    def test_summary_empty(self):
        stats = Stats()
        s = stats.summary()
        assert s == ""

    def test_summary(self):
        stats = Stats()
        stats.record("test", 0.1)
        s = stats.summary()
        assert "test" in s
        assert "n=1" in s


class TestTimer:
    def test_basic(self):
        with Timer("test_timer"):
            time.sleep(0.01)
        stats = get_stats()
        assert stats.counts["test_timer"] == 1

    def test_multiple(self):
        for _ in range(3):
            with Timer("multi"):
                pass
        stats = get_stats()
        assert stats.counts["multi"] >= 3  # other tests may also record


class TestTimedDecorator:
    def test_decorator(self):
        @timed("my_func")
        def foo():
            return 42

        result = foo()
        assert result == 42

    def test_no_key(self):
        @timed()
        def bar():
            return "ok"

        assert bar() == "ok"
