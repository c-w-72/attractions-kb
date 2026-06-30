"""persistence.py 单元测试 — 收藏 + 聊天记录"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.persistence import (
    load_favorites, save_favorites, toggle_favorite, save_note,
    load_chat_history, save_chat_message, clear_chat_history,
    load_search_counts, save_search_counts,
)
from data import persistence as pkg


class TestFavorites:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        json.dump({"favorites": [], "notes": {}}, self.tmp)
        self.tmp.close()
        pkg.FAVORITES_FILE = self.tmp.name

    def teardown_method(self):
        os.unlink(self.tmp.name)

    def test_load_empty(self):
        data = load_favorites()
        assert data == {"favorites": [], "notes": {}}

    def test_toggle_add(self):
        toggle_favorite("故宫")
        data = load_favorites()
        assert "故宫" in data["favorites"]

    def test_toggle_remove(self):
        toggle_favorite("故宫")
        toggle_favorite("故宫")
        data = load_favorites()
        assert "故宫" not in data["favorites"]

    def test_toggle_return(self):
        result = toggle_favorite("黄山")
        assert result is True
        result = toggle_favorite("黄山")
        assert result is False

    def test_save_note(self):
        toggle_favorite("故宫")
        save_note("故宫", "值得再去")
        data = load_favorites()
        assert data["notes"]["故宫"] == "值得再去"

    def test_save_empty_note_removes(self):
        toggle_favorite("故宫")
        save_note("故宫", "笔记")
        save_note("故宫", "")
        data = load_favorites()
        assert "故宫" not in data["notes"]


class TestChatHistory:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        json.dump([], self.tmp)
        self.tmp.close()
        pkg.CHAT_HISTORY_FILE = self.tmp.name

    def teardown_method(self):
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_save_and_load(self):
        save_chat_message({"role": "user", "content": "你好"})
        save_chat_message({"role": "assistant", "content": "你好！"})
        history = load_chat_history()
        assert len(history) == 2

    def test_clear(self):
        save_chat_message({"role": "user", "content": "test"})
        clear_chat_history()
        assert load_chat_history() == []

    def test_missing_file(self):
        os.unlink(self.tmp.name)
        assert load_chat_history() == []

    def test_corrupted_file(self):
        with open(self.tmp.name, "w", encoding="utf-8") as f:
            f.write("not json")
        assert load_chat_history() == []
