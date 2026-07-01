"""
外部数据获取 — 天气 + 景点图片
支持 TTL 缓存 (5分钟) + 文件持久化
"""

import json
import logging
import os
import time
import urllib.request
import urllib.parse
import ssl
logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
_CTX = ssl.create_default_context()

# TTL 缓存 (内存)
_cache = {}
CACHE_TTL = 300  # 5 分钟

# 文件缓存持久化
IMAGE_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cache")
IMAGE_CACHE_FILE = os.path.join(IMAGE_CACHE_DIR, "image_cache.json")
IMAGE_CACHE_TTL = 86400 * 7  # 7 天


def _load_image_cache() -> dict:
    """从磁盘加载图片 URL 缓存（含 TTL 检查）"""
    try:
        if os.path.exists(IMAGE_CACHE_FILE):
            with open(IMAGE_CACHE_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                now = time.time()
                cleaned = {}
                for k, v in raw.items():
                    if isinstance(v, dict) and "t" in v:
                        if now - v["t"] < IMAGE_CACHE_TTL:
                            cleaned[k] = v
                    elif isinstance(v, list):
                        pass  # 旧格式，舍弃
                return cleaned
    except Exception as e:
        logger.warning("图片缓存加载失败: %s", e)
    return {}


def _save_image_cache(cache: dict):
    """保存图片 URL 缓存到磁盘"""
    try:
        os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)
        if len(cache) > 200:
            cache = dict(list(cache.items())[-200:])
        with open(IMAGE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    except Exception as e:
        logger.warning("图片缓存保存失败: %s", e)


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
    """获取城市天气 (wttr.in, 免费无需API key, 失败重试1次)"""
    for attempt in range(2):
        try:
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1&lang=zh"
            logger.info("Fetching weather for city: %s (attempt %d)", city, attempt + 1)
            req = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(req, context=_CTX, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            logger.info("Weather fetched OK for %s", city)
            return data
        except Exception as e:
            logger.warning("Weather fetch failed for %s (attempt %d): %s", city, attempt + 1, e)
            if attempt == 0:
                continue
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
    """获取多张景点图片URL (带内存+文件缓存)"""
    cache_key = f"images_{attraction_name}"
    # 内存缓存
    urls = _cache.get(cache_key, (0, None))[1]
    if urls is not None:
        elapsed = time.time() - _cache[cache_key][0]
        if elapsed < CACHE_TTL:
            return urls[:max_images]

    # 文件缓存 (跨会话，含 TTL)
    file_cache = _load_image_cache()
    if cache_key in file_cache:
        entry = file_cache[cache_key]
        if isinstance(entry, dict) and "urls" in entry:
            urls = entry["urls"]
            _cache[cache_key] = (time.time(), urls)
            return urls[:max_images]

    urls = _fetch_wikimedia(attraction_name)
    if urls:
        _cache[cache_key] = (time.time(), urls)
        file_cache[cache_key] = {"urls": urls, "t": time.time()}
        _save_image_cache(file_cache)
        return urls[:max_images]

    return []
