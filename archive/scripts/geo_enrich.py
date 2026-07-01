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

    # 硬编码坐标映射（覆盖所有景点城市）
    CITY_COORDS = {
        "北京": (116.397, 39.908), "上海": (121.473, 31.230), "天津": (117.200, 39.084),
        "重庆": (106.551, 29.563), "香港": (114.169, 22.319), "澳门": (113.550, 22.200),
        # 广东
        "广州": (113.264, 23.130), "深圳": (114.057, 22.543), "珠海": (113.577, 22.271),
        "佛山": (113.122, 23.021), "东莞": (113.752, 23.021), "韶关": (113.597, 24.810),
        "江门": (113.082, 22.579),
        # 浙江
        "杭州": (120.155, 30.274), "宁波": (121.544, 29.868), "温州": (120.699, 27.994),
        "嘉兴": (120.755, 30.746), "绍兴": (120.580, 30.030), "湖州": (120.086, 30.894),
        "金华": (119.647, 29.079), "舟山": (122.207, 29.985),
        # 江苏
        "南京": (118.796, 32.060), "苏州": (120.585, 31.299), "无锡": (120.312, 31.491),
        "常州": (119.974, 31.811), "扬州": (119.413, 32.394), "镇江": (119.425, 32.188),
        # 四川
        "成都": (104.066, 30.572), "乐山": (103.761, 29.582), "宜宾": (104.620, 28.770),
        "自贡": (104.773, 29.339), "德阳": (104.398, 31.128), "甘孜": (101.962, 30.050),
        "阿坝": (102.225, 31.899), "都江堰": (103.647, 30.988),
        # 福建
        "厦门": (118.089, 24.479), "福州": (119.297, 26.075), "泉州": (118.589, 24.909),
        "宁德": (119.548, 26.666), "南平": (118.178, 26.635), "三明": (117.639, 26.264),
        "龙岩": (117.017, 25.075),
        # 湖北
        "武汉": (114.305, 30.593), "宜昌": (111.286, 30.692), "十堰": (110.798, 32.629),
        "恩施": (109.488, 30.272), "神农架林区": (110.678, 31.744),
        # 湖南
        "长沙": (112.979, 28.213), "张家界": (110.479, 29.117), "衡阳": (112.572, 26.893),
        "岳阳": (113.129, 29.357), "湘潭": (112.944, 27.830), "湘西": (109.739, 28.312),
        "邵阳": (111.468, 27.239),
        # 山东
        "青岛": (120.382, 36.067), "济南": (117.000, 36.651), "烟台": (121.448, 37.464),
        "威海": (122.120, 37.513), "泰安": (117.088, 36.200), "日照": (119.507, 35.420),
        "济宁": (116.587, 35.415), "枣庄": (117.324, 34.810),
        # 河南
        "郑州": (113.625, 34.746), "洛阳": (112.454, 34.620), "开封": (114.348, 34.797),
        "安阳": (114.393, 36.098), "焦作": (113.242, 35.216),
        # 河北
        "石家庄": (114.515, 38.042), "保定": (115.465, 38.874), "唐山": (118.183, 39.650),
        "秦皇岛": (119.600, 39.935), "邯郸": (114.539, 36.625), "承德": (117.963, 40.952),
        "张家口": (114.887, 40.769),
        # 陕西
        "西安": (108.940, 34.261), "延安": (109.490, 36.585), "宝鸡": (107.237, 34.362),
        "渭南": (109.510, 34.520), "汉中": (107.023, 33.067),
        # 江西
        "南昌": (115.858, 28.683), "九江": (115.952, 29.662), "上饶": (117.943, 28.456),
        "宜春": (114.416, 27.815), "吉安": (114.993, 27.113), "赣州": (114.935, 25.832),
        "鹰潭": (117.069, 28.260), "景德镇": (117.178, 29.269),
        # 广西
        "桂林": (110.290, 25.273), "南宁": (108.366, 22.817), "北海": (109.120, 21.481),
        "柳州": (109.416, 24.326), "崇左": (107.389, 22.376), "百色": (106.618, 23.902),
        # 云南
        "昆明": (102.833, 24.880), "丽江": (100.229, 26.875), "大理": (100.229, 25.592),
        "香格里拉": (99.702, 27.826), "保山": (99.161, 25.112), "玉溪": (102.547, 24.352),
        "西双版纳": (100.797, 22.001), "红河": (103.375, 23.367),
        # 山西
        "太原": (112.549, 37.870), "大同": (113.300, 40.077), "晋中": (112.753, 37.687),
        "忻州": (112.734, 38.417), "临汾": (111.519, 36.088), "运城": (110.998, 35.015),
        "晋城": (112.851, 35.491), "长治": (113.113, 36.191), "吕梁": (111.134, 37.519),
        "朔州": (112.433, 39.332),
        # 吉林
        "长春": (125.324, 43.886), "吉林": (126.549, 43.838), "延边": (129.509, 42.891),
        "通化": (125.939, 41.728), "长白山": (128.087, 42.080),
        # 辽宁
        "沈阳": (123.432, 41.808), "大连": (121.615, 38.914), "丹东": (124.356, 40.000),
        "本溪": (123.767, 41.294), "盘锦": (122.170, 41.120), "锦州": (121.135, 41.095),
        "鞍山": (122.994, 41.108),
        # 黑龙江
        "哈尔滨": (126.535, 45.803), "牡丹江": (129.633, 44.551), "齐齐哈尔": (123.918, 47.354),
        "伊春": (128.841, 47.727), "黑河": (127.529, 50.245), "大兴安岭": (124.117, 50.410),
        # 安徽
        "黄山": (118.338, 29.715), "合肥": (117.227, 31.821), "安庆": (117.063, 30.528),
        "芜湖": (118.376, 31.327), "池州": (117.491, 30.665), "六安": (116.520, 31.735),
        # 甘肃
        "兰州": (103.834, 36.061), "天水": (105.725, 34.581), "张掖": (100.450, 38.925),
        "酒泉": (98.494, 39.733), "嘉峪关": (98.289, 39.773), "平凉": (106.665, 35.543),
        "甘南": (102.911, 34.986),
        # 贵州
        "贵阳": (106.630, 26.647), "遵义": (106.937, 27.727), "安顺": (105.946, 26.253),
        "黔东南": (107.982, 26.584), "黔南": (107.517, 26.254), "铜仁": (109.189, 27.731),
        "兴义": (104.895, 25.092),
        # 新疆
        "乌鲁木齐": (87.617, 43.793), "吐鲁番": (89.190, 42.951), "伊犁": (81.324, 43.917),
        "喀什": (75.992, 39.467), "巴音郭楞": (86.152, 41.761), "阿勒泰": (88.140, 47.848),
        "昌吉": (87.267, 44.014), "博尔塔拉": (82.066, 44.905), "独山子": (84.887, 44.328),
        # 内蒙古
        "呼和浩特": (111.750, 40.842), "呼伦贝尔": (119.760, 49.209), "鄂尔多斯": (109.781, 39.608),
        "阿拉善": (105.728, 38.833), "额济纳": (101.067, 41.958), "兴安盟": (122.038, 46.083),
        # 西藏
        "拉萨": (91.117, 29.647), "日喀则": (88.887, 29.267), "林芝": (94.362, 29.654),
        "山南": (91.773, 29.237), "阿里": (80.106, 32.501),
        # 海南
        "海口": (110.330, 20.022), "三亚": (109.512, 18.252), "保亭": (109.702, 18.639),
        # 青海
        "西宁": (101.779, 36.623), "格尔木": (94.928, 36.406), "海北": (100.901, 36.956),
        "海西": (97.371, 37.377), "玉树": (97.009, 33.004),
        # 宁夏
        "银川": (106.232, 38.486), "中卫": (105.196, 37.514), "固原": (106.285, 36.016),
        # 台湾
        "台北": (121.565, 25.033), "高雄": (120.312, 22.621), "台东": (121.150, 22.758),
        "嘉义": (120.452, 23.479),
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
