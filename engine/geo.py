"""
地理工具 — 距离计算 + 附近景点推荐
"""

import math

EARTH_RADIUS_KM = 6371.0


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """计算两个经纬度点之间的距离（公里）"""
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def get_nearby_attractions(attractions: list, att: dict, top_n: int = 5, max_dist: float = 300) -> list:
    """获取附近景点（按距离排序）"""
    loc = att.get("location")
    if not loc:
        return []

    lon1, lat1 = loc[0], loc[1]
    scored = []
    for a in attractions:
        aloc = a.get("location")
        if not aloc or a["id"] == att["id"]:
            continue
        dist = haversine(lon1, lat1, aloc[0], aloc[1])
        if dist <= max_dist:
            scored.append((a, dist))

    scored.sort(key=lambda x: x[1])
    return scored[:top_n]
