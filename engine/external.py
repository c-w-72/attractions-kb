"""
外部数据获取 — 天气 + 景点图片
"""

import json
import logging
import urllib.request
import urllib.parse
import ssl

logger = logging.getLogger(__name__)


def fetch_weather(city: str) -> dict | None:
    """获取城市天气 (wttr.in, 免费无需API key)"""
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1&lang=zh"
        logger.info(f"Fetching weather for city: {city}")
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        logger.info(f"Weather fetched OK for {city}")
        return data
    except Exception as e:
        logger.warning(f"Weather fetch failed for {city}: {e}")
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


def fetch_image(attraction_name: str) -> str | None:
    """获取景点图片URL — 尝试多个图片来源"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # 1) Unsplash Source (免费, 无需key)
    try:
        logger.info(f"Fetching image for: {attraction_name}")
        encoded = urllib.parse.quote(f"{attraction_name} China travel")
        url = f"https://source.unsplash.com/800x600/?{encoded}"
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            if resp.status == 200:
                logger.info(f"Unsplash image found for {attraction_name}")
                return resp.url
    except Exception as e:
        logger.debug(f"Unsplash failed for {attraction_name}: {e}")

    # 2) 百度图片搜索
    try:
        ctx = ssl.create_default_context()
        encoded = urllib.parse.quote(attraction_name + " 景点")
        url = f"https://image.baidu.com/search/acjson?tn=resultjson_com&word={encoded}&pn=0&rn=1"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        items = data.get("data", [])
        for item in items:
            thumb = item.get("thumbURL") or item.get("middleURL")
            if thumb:
                logger.info(f"Baidu image found for {attraction_name}")
                return thumb
    except Exception as e:
        logger.debug(f"Baidu image failed for {attraction_name}: {e}")

    logger.info(f"No image found for {attraction_name}")
    return None
