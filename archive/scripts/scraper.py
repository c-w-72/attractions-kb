"""
数据增量更新脚本 — 从 Wikimedia/Wikidata 发现新景点
用法: python scripts/scraper.py [--dry-run]

工作流程:
  1. 读取现有 attractions.json
  2. 按省份查询 Wikimedia 获取新景点候选
  3. 去重后生成基础 JSON 条目
  4. 追加到 attractions.json (--dry-run 仅预览)
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import ssl
import re
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "attractions.json")

_HEADERS = {"User-Agent": "AttractionsKB/1.0 (data enrichment script)"}
_CTX = ssl.create_default_context()
_NEXT_ID = None


def load_existing():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_attractions(attractions):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(attractions, f, ensure_ascii=False, indent=2)


def get_next_id(attractions):
    return max(a["id"] for a in attractions) + 1


def wikimedia_search(query: str, limit: int = 20) -> list:
    """搜索 Wikimedia 获取页面标题列表"""
    url = (
        "https://en.wikipedia.org/w/api.php?"
        "action=query&list=search&srsearch=" + urllib.parse.quote(query) +
        f"&srlimit={limit}&format=json&origin=*"
    )
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, context=_CTX, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [r["title"] for r in data.get("query", {}).get("search", [])]
    except Exception as e:
        print(f"  Wikimedia search error: {e}")
        return []


def wikidata_query(sparql: str) -> list:
    """通过 SPARQL 查询 Wikidata"""
    url = "https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(sparql)
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, context=_CTX, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("results", {}).get("bindings", [])
    except Exception as e:
        print(f"  Wikidata query error: {e}")
        return []


def get_attractions_by_province(province_en: str) -> list:
    """通过 Wikidata 查询某省份的景点"""
    sparql = f"""
    SELECT ?item ?itemLabel ?description WHERE {{
      ?item wdt:P31/wdt:P279* wd:Q570116;  # tourist attraction
             wdt:P131+ wd:{province_en}.      # located in
      OPTIONAL {{ ?item schema:description ?description. FILTER(LANG(?description) = "zh") }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "zh,en". }}
    }}
    LIMIT 50
    """
    return wikidata_query(sparql)


def normalize_name(name: str) -> str:
    name = re.sub(r"\s*\(.*?\)\s*", "", name).strip()
    name = re.sub(r"\s*（.*?）\s*", "", name).strip()
    return name


def is_duplicate(name: str, existing: list) -> bool:
    nl = name.lower().replace(" ", "")
    for a in existing:
        if a["name"].lower().replace(" ", "") == nl:
            return True
        # 别名检查
        if name in a.get("description", "")[:20]:
            return True
    return False


def categorize_by_keywords(name: str, desc: str = "") -> str:
    text = name + desc
    if any(k in text for k in ["乐园", "游乐园", "主题公园", "迪士尼", "欢乐谷"]):
        return "主题乐园"
    if any(k in text for k in ["博物馆", "遗址", "古迹", "古城", "寺庙", "塔", "宫", "陵", "石窟", "古镇"]):
        return "历史文化"
    if any(k in text for k in ["山", "湖", "河", "海", "岛", "瀑布", "森林", "公园", "峡谷", "草原", "沙漠", "峰", "沟"]):
        return "自然风光"
    if any(k in text for k in ["大街", "广场", "商业街", "步行街", "中心", "区"]):
        return "都市风情"
    return "历史文化"


def estimate_rating(name: str) -> float:
    """基于关键词估算评分"""
    high = ["故宫", "长城", "兵马俑", "黄山", "九寨沟", "张家界", "西湖", "桂林"]
    mid = ["国家公园", "5A", "世界遗产", "风景名胜", "博物馆"]
    for k in high:
        if k in name:
            return 4.7
    for k in mid:
        if k in name:
            return 4.3
    return 4.0


def create_entry(name: str, province: str, existing: list, desc: str = "") -> dict:
    global _NEXT_ID
    entry = {
        "id": _NEXT_ID,
        "name": name,
        "province": province,
        "city": "",
        "category": categorize_by_keywords(name, desc),
        "rating": estimate_rating(name),
        "ticket": "",
        "description": desc[:300] if desc else "",
        "highlights": "",
        "best_season": "",
        "tips": "",
        "location": None,
        "basic_info": "",
        "travel_guide": "",
        "food": "",
        "culture": "",
        "transport": "",
    }
    _NEXT_ID += 1
    return entry


def main():
    global _NEXT_ID
    dry_run = "--dry-run" in sys.argv

    attractions = load_existing()
    _NEXT_ID = get_next_id(attractions)
    existing_names = set(a["name"] for a in attractions)
    print(f"现有景点: {len(attractions)} 个")

    # 省份映射 (中文 -> 英文 Wikidata ID)
    provinces = {
        "北京": "Q956", "天津": "Q664", "上海": "Q8686", "重庆": "Q11725",
        "河北": "Q212", "山西": "Q728", "内蒙古": "Q410", "辽宁": "Q810",
        "吉林": "Q811", "黑龙江": "Q912", "江苏": "Q1695", "浙江": "Q16967",
        "安徽": "Q409", "福建": "Q417", "江西": "Q570", "山东": "Q434",
        "河南": "Q436", "湖北": "Q11728", "湖南": "Q426", "广东": "Q423",
        "广西": "Q15176", "海南": "Q422", "四川": "Q19770", "贵州": "Q47098",
        "云南": "Q424", "西藏": "Q17269", "陕西": "Q430", "甘肃": "Q42392",
        "青海": "Q458", "宁夏": "Q41748", "新疆": "Q428", "香港": "Q8646",
        "澳门": "Q14773", "台湾": "Q8650",
    }

    new_entries = []
    for cn, wid in provinces.items():
        print(f"\n查询 {cn} (Q{wid})...")
        results = get_attractions_by_province(wid)
        found = 0
        for r in results:
            label = r.get("itemLabel", {}).get("value", "")
            desc = r.get("description", {}).get("value", "") if "description" in r else ""
            name = normalize_name(label)
            if not name or len(name) < 2:
                continue
            if is_duplicate(name, attractions) or is_duplicate(name, new_entries):
                continue
            if any(k in name for k in ["Wikipedia", "Category", "List of", "Wikimedia"]):
                continue

            entry = create_entry(name, cn, attractions, desc)
            new_entries.append(entry)
            found += 1
            if found >= 3:  # 每省最多加3个，避免过度膨胀
                break
        print(f"  发现 {found} 个新景点候选")
        time.sleep(0.5)  # API 限流

    if not new_entries:
        print("\n未发现新景点")
        return

    print(f"\n共发现 {len(new_entries)} 个新景点:")
    for entry in new_entries:
        print(f"  #{entry['id']} {entry['name']} ({entry['province']}) — {entry['category']}")

    if dry_run:
        print(f"\n💡 使用 --dry-run 标志，未写入文件")
        return

    attractions.extend(new_entries)
    save_attractions(attractions)
    print(f"\n✅ 已追加 {len(new_entries)} 个新景点到 attractions.json")
    print(f"   总量: {len(attractions)} 个")


if __name__ == "__main__":
    main()
