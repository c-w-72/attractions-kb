"""
性能监控 - 计时器 + 统计摘要
"""

import logging
import time
from collections import defaultdict
from functools import wraps

logger = logging.getLogger(__name__)


class Stats:
    """轻量统计累加器"""
    def __init__(self):
        self.counts = defaultdict(int)
        self.totals = defaultdict(float)
        self.maxes = defaultdict(float)

    def record(self, key: str, elapsed: float):
        self.counts[key] += 1
        self.totals[key] += elapsed
        if elapsed > self.maxes[key]:
            self.maxes[key] = elapsed

    def summary(self) -> str:
        lines = []
        for key in sorted(self.counts):
            n = self.counts[key]
            total = self.totals[key]
            avg = total / n if n else 0
            lines.append(f"  {key}: n={n}, total={total:.2f}s, avg={avg:.3f}s, max={self.maxes[key]:.3f}s")
        return "\n".join(lines)


_stats = Stats()


def get_stats() -> Stats:
    return _stats


class Timer:
    """上下文管理器计时器"""

    def __init__(self, key: str):
        self.key = key

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        elapsed = time.perf_counter() - self.start
        _stats.record(self.key, elapsed)
        if elapsed > 1.0:
            logger.warning("SLOW [%s]: %.2fs", self.key, elapsed)
        logger.debug("[perf] %s: %.3fs", self.key, elapsed)


def timed(key: str = None):
    """装饰器: 自动计时"""
    def decorator(fn):
        k = key or fn.__name__
        @wraps(fn)
        def wrapper(*args, **kwargs):
            with Timer(k):
                return fn(*args, **kwargs)
        return wrapper
    return decorator
