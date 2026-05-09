"""Unit tests for local JSON index cache."""
import json

import pytest

from notice_solver.cache.index import AssetIndex, NoticeIndex


class TestNoticeIndex:
    def test_empty_on_init(self, tmp_cache_dir):
        idx = NoticeIndex(tmp_cache_dir)
        assert not idx.exists("BOARD-123")
        assert len(idx) == 0

    def test_add_and_exists(self, tmp_cache_dir):
        idx = NoticeIndex(tmp_cache_dir)
        idx.add("BOARD-123", 42)
        assert idx.exists("BOARD-123")

    def test_add_persists(self, tmp_cache_dir):
        idx = NoticeIndex(tmp_cache_dir)
        idx.add("BOARD-123", 42)
        idx2 = NoticeIndex(tmp_cache_dir)
        assert idx2.exists("BOARD-123")
        assert idx2.get("BOARD-123") == 42

    def test_len(self, tmp_cache_dir):
        idx = NoticeIndex(tmp_cache_dir)
        idx.add("id1", 1)
        idx.add("id2", 2)
        assert len(idx) == 2

    def test_get_missing_returns_none(self, tmp_cache_dir):
        idx = NoticeIndex(tmp_cache_dir)
        assert idx.get("nonexistent") is None

    def test_json_format(self, tmp_cache_dir):
        idx = NoticeIndex(tmp_cache_dir)
        idx.add("BOARD-1", 10)
        data = json.loads((tmp_cache_dir / "notice-index.json").read_text())
        assert data["BOARD-1"] == 10

    def test_load_existing_file(self, tmp_cache_dir):
        (tmp_cache_dir / "notice-index.json").write_text('{"BOARD-99": 99}')
        idx = NoticeIndex(tmp_cache_dir)
        assert idx.exists("BOARD-99")
        assert idx.get("BOARD-99") == 99

    def test_invalid_json_falls_back_to_empty(self, tmp_cache_dir):
        (tmp_cache_dir / "notice-index.json").write_text("not valid json{")
        idx = NoticeIndex(tmp_cache_dir)
        assert len(idx) == 0


class TestAssetIndex:
    def test_separate_from_notice_index(self, tmp_cache_dir):
        notice_idx = NoticeIndex(tmp_cache_dir)
        asset_idx = AssetIndex(tmp_cache_dir)
        notice_idx.add("notice-1", 1)
        assert not asset_idx.exists("notice-1")

    def test_asset_index_path(self, tmp_cache_dir):
        idx = AssetIndex(tmp_cache_dir)
        idx.add("asset-1", 51)
        assert (tmp_cache_dir / "asset-index.json").exists()
