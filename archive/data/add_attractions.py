#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量添加新景点到 attractions.json
使用json模块加载数据，避免引号冲突
"""
import json
import os
from collections import Counter

DATA_FILE = os.path.join(os.path.dirname(__file__), 'attractions.json')
NEW_FILE = os.path.join(os.path.dirname(__file__), 'new_attractions.json')


def main():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open(NEW_FILE, 'r', encoding='utf-8') as f:
        new_list = json.load(f)

    existing_names = {a['name'] for a in data}
    max_id = max(a['id'] for a in data)

    added = 0
    skipped = 0
    for att in new_list:
        if att['name'] in existing_names:
            print(f'Skip duplicate: {att["name"]}')
            skipped += 1
            continue
        max_id += 1
        entry = {
            'id': max_id,
            'name': att['name'],
            'province': att['province'],
            'city': att.get('city', ''),
            'category': att['category'],
            'description': att['description'],
            'highlights': att['highlights'],
            'best_season': att['best_season'],
            'tips': att.get('tips', ''),
            'rating': att['rating'],
            'ticket': att['ticket'],
            'location': [],
        }
        # Keep related_ids if present
        if 'related_ids' in att:
            entry['related_ids'] = att['related_ids']
        data.append(entry)
        existing_names.add(att['name'])
        added += 1

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    provinces = Counter(a['province'] for a in data)
    categories = Counter(a['category'] for a in data)

    print(f'\n原有: {len(data) - added} 个景点')
    print(f'新增: {added} 个景点')
    print(f'跳过: {skipped} 个重复')
    print(f'总计: {len(data)} 个景点\n')

    print('各省分布:')
    for p in sorted(provinces):
        print(f'  {p}: {provinces[p]}')

    print('\n各类别分布:')
    for c in sorted(categories):
        print(f'  {c}: {categories[c]}')


if __name__ == '__main__':
    main()
