"""
景点去重脚本 — 合并同名/包含关系的重复条目
用法: python scripts/dedup.py [--dry-run]

合并策略:
  1. 同省且名称包含关系 → 保留短名(主体), 合并描述/亮点/提示
  2. 完全同名(跨省) → 各自保留
  3. 生成去重报告
"""

import json
import os
import re
import sys

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         "data", "attractions.json")


def load():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def merge_field(main_val, sub_val):
    """合并两个字段值，去重"""
    if not sub_val:
        return main_val
    if not main_val:
        return sub_val
    # 按分隔符合并
    combined = main_val
    for sep in ["、", "，", ",", ";", "；", "\n"]:
        parts = set()
        for v in [main_val, sub_val]:
            for p in v.split(sep):
                p = p.strip()
                if p and len(p) > 1:
                    parts.add(p)
        if parts:
            combined = sep.join(sorted(parts, key=lambda x: -len(x)))
            break
    return combined[:500] if len(combined) > 500 else combined


def is_duplicate_of(long_name: str, short_name: str) -> bool:
    """判断两个名称是否指向同一景点（包含关系）"""
    if len(short_name) < 2:
        return False
    # 子景点包含主景点名称: "华山长空栈道" 以 "华山" 开头
    # 地理前缀:              "南京中山陵" 以 "中山陵" 结尾
    return long_name.startswith(short_name) or long_name.endswith(short_name)


def main():
    dry_run = "--dry-run" in sys.argv
    attractions = load()
    removed = set()
    merged = {}

    name_map = {a["name"]: a for a in attractions}
    all_names = sorted(set(name_map.keys()), key=len)

    for a in list(attractions):
        if a["id"] in removed:
            continue
        for parent_name in all_names:
            if a["name"] == parent_name or len(parent_name) < 2:
                continue
            if is_duplicate_of(a["name"], parent_name):
                parent = name_map.get(parent_name)
                if parent and parent["id"] not in removed and parent["province"] == a["province"]:
                    merged[a["id"]] = parent["id"]
                    removed.add(a["id"])

                    parent["description"] = merge_field(parent["description"], a["description"])
                    parent["highlights"] = merge_field(parent["highlights"], a["highlights"])
                    parent["tips"] = merge_field(parent["tips"], a["tips"])
                    parent["food"] = merge_field(parent["food"], a["food"])
                    parent["culture"] = merge_field(parent["culture"], a["culture"])
                    if not parent.get("ticket") and a.get("ticket"):
                        parent["ticket"] = a["ticket"]
                    if a.get("rating", 0) > parent.get("rating", 0):
                        parent["rating"] = a["rating"]
                    if a.get("location") and not parent.get("location"):
                        parent["location"] = a["location"]
                    break

    if not removed:
        print("未发现需要去重的条目")
        return

    # 构建去重后的列表
    cleaned = [a for a in attractions if a["id"] not in removed]
    # 重新编号
    for i, a in enumerate(cleaned, 1):
        a["id"] = i

    print(f"去重报告:")
    print(f"  原数量: {len(attractions)}")
    print(f"  移除: {len(removed)}")
    print(f"  现数量: {len(cleaned)}")
    print()
    print(f"合并详情:")
    for sub_id, main_id in sorted(merged.items(), key=lambda x: x[1]):
        main_name = next(a["name"] for a in attractions if a["id"] == main_id)
        sub_name = next(a["name"] for a in attractions if a["id"] == sub_id)
        print(f"  ✓ \"{sub_name}\" → 合并到 \"{main_name}\"")

    if dry_run:
        print(f"\n💡 --dry-run 模式，未写入文件")
        return

    save(cleaned)
    print(f"\n✅ 已保存去重后的数据到 attractions.json")


if __name__ == "__main__":
    main()
