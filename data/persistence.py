"""
数据持久化 — 收藏管理 + 对话历史
"""

import json
import os

FAVORITES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "favorites.json")
CHAT_HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chat_history.json")
SEARCH_COUNTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "search_counts.json")
SEARCH_HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "search_history.json")


# ===== 收藏管理 =====

def load_favorites():
    if not os.path.exists(FAVORITES_FILE):
        return {"favorites": [], "notes": {}}
    with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_favorites(data):
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def toggle_favorite(att_name: str):
    data = load_favorites()
    if att_name in data["favorites"]:
        data["favorites"].remove(att_name)
        data["notes"].pop(att_name, None)
    else:
        data["favorites"].append(att_name)
    save_favorites(data)
    return att_name in data["favorites"]


# ===== 搜索计数持久化 =====


def load_search_counts() -> dict:
    """从磁盘加载搜索计数"""
    if os.path.exists(SEARCH_COUNTS_FILE):
        try:
            with open(SEARCH_COUNTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_search_counts(counts: dict):
    """保存搜索计数到磁盘"""
    try:
        os.makedirs(os.path.dirname(SEARCH_COUNTS_FILE), exist_ok=True)
        with open(SEARCH_COUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(counts, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ===== 搜索历史持久化 =====


def load_search_history() -> list:
    """从磁盘加载搜索历史"""
    if os.path.exists(SEARCH_HISTORY_FILE):
        try:
            with open(SEARCH_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_search_history(history: list):
    """保存搜索历史到磁盘（保留最近 50 条）"""
    try:
        os.makedirs(os.path.dirname(SEARCH_HISTORY_FILE), exist_ok=True)
        with open(SEARCH_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[-50:], f, ensure_ascii=False)
    except Exception:
        pass


def batch_remove_favorites(names: list):
    """批量移除收藏景点"""
    data = load_favorites()
    for n in names:
        if n in data["favorites"]:
            data["favorites"].remove(n)
        data["notes"].pop(n, None)
    save_favorites(data)


def save_note(att_name: str, note: str):
    data = load_favorites()
    if note:
        data["notes"][att_name] = note
    else:
        data["notes"].pop(att_name, None)
    save_favorites(data)


# ===== 对话历史持久化 =====

def load_chat_history():
    if not os.path.exists(CHAT_HISTORY_FILE):
        return []
    try:
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_chat_message(msg: dict):
    history = load_chat_history()
    history.append(msg)
    if len(history) > 100:
        history = history[-100:]
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def clear_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)
