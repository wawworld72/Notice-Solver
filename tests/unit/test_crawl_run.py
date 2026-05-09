"""Unit tests for CrawlRun model (US6)."""
import json
from datetime import datetime, timezone

import pytest

from notice_solver.models.crawl_run import CrawlRun


class TestCrawlRun:
    def test_report_format(self):
        run = CrawlRun(run_id="20260509-030000", pipeline="collect")
        run.processed = 5
        run.skipped = 120
        run.failed = 0
        run.started_at = datetime(2026, 5, 9, 3, 0, 0, tzinfo=timezone.utc)
        run.finished_at = datetime(2026, 5, 9, 3, 0, 32, tzinfo=timezone.utc)
        report = run.report()
        assert "5" in report
        assert "120" in report
        assert "32" in report

    def test_to_json_serialization(self):
        run = CrawlRun(run_id="20260509-030000", pipeline="collect", board_id="BOARD")
        run.processed = 3
        run.finished_at = datetime(2026, 5, 9, tzinfo=timezone.utc)
        data = run.to_json()
        assert data["run_id"] == "20260509-030000"
        assert data["pipeline"] == "collect"
        assert data["processed"] == 3
        assert data["finished_at"] is not None

    def test_save_creates_json_file(self, tmp_cache_dir):
        run = CrawlRun(run_id="test-run-id", pipeline="collect")
        run.processed = 10
        run.finished_at = datetime.now(timezone.utc)
        run.save(tmp_cache_dir)
        path = tmp_cache_dir / "runs" / "test-run-id.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["run_id"] == "test-run-id"
        assert data["processed"] == 10

    def test_load_latest_returns_most_recent(self, tmp_cache_dir):
        run1 = CrawlRun(run_id="20260501-000000", pipeline="collect")
        run1.processed = 5
        run1.finished_at = datetime(2026, 5, 1, tzinfo=timezone.utc)
        run1.save(tmp_cache_dir)

        run2 = CrawlRun(run_id="20260509-000000", pipeline="collect")
        run2.processed = 10
        run2.finished_at = datetime(2026, 5, 9, tzinfo=timezone.utc)
        run2.save(tmp_cache_dir)

        latest = CrawlRun.load_latest(tmp_cache_dir, "collect")
        assert latest is not None
        assert latest.processed == 10

    def test_load_latest_filters_by_pipeline(self, tmp_cache_dir):
        run_collect = CrawlRun(run_id="20260509-000001", pipeline="collect")
        run_collect.finished_at = datetime.now(timezone.utc)
        run_collect.save(tmp_cache_dir)

        run_ocr = CrawlRun(run_id="20260509-000002", pipeline="ocr")
        run_ocr.processed = 50
        run_ocr.finished_at = datetime.now(timezone.utc)
        run_ocr.save(tmp_cache_dir)

        latest_ocr = CrawlRun.load_latest(tmp_cache_dir, "ocr")
        assert latest_ocr is not None
        assert latest_ocr.pipeline == "ocr"
        assert latest_ocr.processed == 50

    def test_load_latest_no_runs_returns_none(self, tmp_cache_dir):
        result = CrawlRun.load_latest(tmp_cache_dir, "collect")
        assert result is None
