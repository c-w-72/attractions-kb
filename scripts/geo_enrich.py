"""
GPS 坐标补全脚本 — 高德/百度地图 API
用法: python scripts/geo_enrich.py [--provider amap|baidu]
需要设置环境变量 AMAP_KEY 或 BAIDU_KEY

批量查询缺乏 GPS 坐标的景点 → 写入 data/attractions.json
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         "data", "attractions.json")


def load_attractions():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_attractions(attractions):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(attractions, f, ensure_ascii=False, indent=2)


def query_amap(name: str, city: str = "") -> tuple | None:
    """高德地图地理编码"""
    key = os.environ.get("AMAP_KEY")
    if not key:
        return None
    params = {"key": key, "address": name, "city": city}
    url = f"https://restapi.amap.com/v3/geocode/geo?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("status") == "1" and data.get("geocodes"):
            loc = data["geocodes"][0]["location"]  # "lng,lat"
            lng, lat = loc.split(",")
            return (float(lng), float(lat))
    except Exception as e:
        print(f"  AMAP error: {e}")
    return None


def query_baidu(name: str, city: str = "") -> tuple | None:
    """百度地图地理编码"""
    key = os.environ.get("BAIDU_KEY")
    if not key:
        return None
    params = {"ak": key, "address": name, "city": city, "output": "json"}
    url = f"https://api.map.baidu.com/geocoding/v3/?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("status") == 0 and data.get("result"):
            loc = data["result"]["location"]
            return (float(loc["lng"]), float(loc["lat"]))
    except Exception as e:
        print(f"  Baidu error: {e}")
    return None


def main():
    provider = os.environ.get("GEO_PROVIDER", "amap")
    if provider == "amap":
        query_fn = query_amap
        print("Using AMap geocoding")
    else:
        query_fn = query_baidu
        print("Using Baidu geocoding")

    key = os.environ.get("AMAP_KEY" if provider == "amap" else "BAIDU_KEY")
    if not key:
        print("WARNING: No API key set. Set AMAP_KEY or BAIDU_KEY env var.")
        print("Will generate estimated coordinates for attractions without GPS.")

    attractions = load_attractions()
    needs_gps = [a for a in attractions if not a.get("location")]
    print(f"Total: {len(attractions)}, Missing GPS: {len(needs_gps)}")

    # 硬编码坐标映射（常用城市中心点）
    CITY_COORDS = {
        "北京": (116.397, 39.908),
        "上海": (121.473, 31.230),
        "广州": (113.264, 23.130),
        "深圳": (114.057, 22.543),
        "成都": (104.066, 30.572),
        "杭州": (120.155, 30.274),
        "西安": (108.940, 34.261),
        "重庆": (106.551, 29.563),
        "武汉": (114.305, 30.593),
        "南京": (118.796, 32.060),
        "长沙": (112.979, 28.213),
        "昆明": (102.833, 24.880),
        "桂林": (110.290, 25.273),
        "丽江": (100.229, 26.875),
        "拉萨": (91.117, 29.647),
        "乌鲁木齐": (87.617, 43.793),
        "哈尔滨": (126.535, 45.803),
        "厦门": (118.089, 24.479),
        "青岛": (120.382, 36.067),
    }

    updated = 0
    for att in needs_gps:
        name = att["name"]
        city = att.get("city", "")
        province = att["province"]

        print(f"  {name} ({province} {city})...", end="")
        result = None

        # 尝试 API 查询
        if key:
            result = query_fn(name, city or province)
            if result:
                print(f" API: {result[0]:.4f}, {result[1]:.4f}")
            else:
                # 用省份中心点
                if province in CITY_COORDS:
                    result = CITY_COORDS[province]
                    print(f" fallback province: {result[0]:.4f}, {result[1]:.4f}")
                elif city in CITY_COORDS:
                    result = CITY_COORDS[city]
                    print(f" fallback city: {result[0]:.4f}, {result[1]:.4f}")
                else:
                    print(" SKIP (no fallback)")
            time.sleep(0.3)  # API 限流
        else:
            # 无 API key，用硬编码
            if city in CITY_COORDS:
                result = CITY_COORDS[city]
                print(f" hardcoded city: {result[0]:.4f}, {result[1]:.4f}")
            elif province in CITY_COORDS:
                result = CITY_COORDS[province]
                print(f" hardcoded province: {result[0]:.4f}, {result[1]:.4f}")
            else:
                print(" SKIP")

        if result:
            att["location"] = [result[0], result[1]]
            updated += 1

    save_attractions(attractions)
    print(f"\nDone. Updated {updated}/{len(needs_gps)} attractions with GPS.")
    print(f"Total with GPS: {sum(1 for a in attractions if a.get('location'))}/{len(attractions)}")


if __name__ == "__main__":
    main()
