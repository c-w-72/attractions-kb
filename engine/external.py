"""
外部数据获取 — 天气 + 景点图片
支持 TTL 缓存 (5分钟)
"""

import json
import logging
import time
import urllib.request
import urllib.parse
import ssl
logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
_CTX = ssl.create_default_context()

# TTL 缓存
_cache = {}
CACHE_TTL = 300  # 5 分钟


def _cached(key: str, fetch_fn, *args, **kwargs):
    """带 TTL 的缓存包装"""
    now = time.time()
    if key in _cache:
        ts, result = _cache[key]
        if now - ts < CACHE_TTL:
            logger.debug("Cache hit: %s", key)
            return result
    result = fetch_fn(*args, **kwargs)
    _cache[key] = (now, result)
    return result


def fetch_weather(city: str) -> dict | None:
    """获取城市天气 (wttr.in, 免费无需API key)"""
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1&lang=zh"
        logger.info("Fetching weather for city: %s", city)
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, context=_CTX, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        logger.info("Weather fetched OK for %s", city)
        return data
    except Exception as e:
        logger.warning("Weather fetch failed for %s: %s", city, e)
        return None


def parse_weather(data: dict) -> dict | None:
    """解析天气 API 返回数据为摘要"""
    if not data or "current_condition" not in data:
        return None
    cc = data["current_condition"][0]
    forecast = data.get("weather", [])[:3]

    days = []
    for w in forecast:
        days.append({
            "date": w.get("date", ""),
            "hi": w.get("maxtempC", ""),
            "lo": w.get("mintempC", ""),
            "desc": (w.get("hourly", [{}])[0].get("lang_zh", [{}])[0] or {}).get("value", ""),
        })

    return {
        "temp": cc.get("temp_C", ""),
        "feels": cc.get("FeelsLikeC", ""),
        "humidity": cc.get("humidity", ""),
        "desc": cc.get("lang_zh", [{}])[0].get("value", "") if cc.get("lang_zh") else "",
        "wind": cc.get("windspeedKmph", ""),
        "forecast": days,
    }


def fetch_weather_cached(city: str) -> dict | None:
    """带缓存的天气查询"""
    data = _cached(f"weather_{city}", fetch_weather, city)
    return parse_weather(data)


def _fetch_wikimedia(attraction_name: str) -> list:
    """从 Wikimedia Commons 获取景点图片列表"""
    urls = []
    try:
        encoded = urllib.parse.quote(attraction_name)
        url = (
            "https://commons.wikimedia.org/w/api.php?"
            "action=query&generator=search&gsrnamespace=6&"
            f"gsrsearch={encoded}&gsrlimit=10&"
            "prop=imageinfo&iiprop=url&format=json&origin=*"
        )
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, context=_CTX, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        for pid in sorted(pages.keys())[:5]:
            info = pages[pid].get("imageinfo", [])
            if info:
                img_url = info[0].get("url", "")
                if img_url and img_url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    urls.append(img_url)
    except Exception as e:
        logger.debug("Wikimedia failed for %s: %s", attraction_name, e)
    return urls


def fetch_image(attraction_name: str) -> str | None:
    """获取单张景点图片 (兼容旧接口)"""
    urls = fetch_images(attraction_name)
    return urls[0] if urls else None


def fetch_images(attraction_name: str, max_images: int = 5) -> list:
    """获取多张景点图片URL (带缓存)"""
    cache_key = f"images_{attraction_name}"
    urls = _cache.get(cache_key, (0, None))[1]
    if urls is not None:
        elapsed = time.time() - _cache[cache_key][0]
        if elapsed < CACHE_TTL:
            return urls[:max_images]

    urls = _fetch_wikimedia(attraction_name)
    if urls:
        _cache[cache_key] = (time.time(), urls)
        return urls[:max_images]

    return []
