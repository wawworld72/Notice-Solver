from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from notice_solver.models.asset import Asset
from notice_solver.models.notice import AttachmentRef, Notice


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def mock_settings(tmp_path):
    from notice_solver.config import Settings
    return Settings(
        github_token="test-token",
        github_repo_owner="test-owner",
        github_repo_name="test-repo",
        cache_dir=tmp_path / ".cache",
        log_dir=tmp_path / "logs",
    )


@pytest.fixture
def mock_github_api():
    api = MagicMock()
    api.issues.create.return_value = {"number": 42, "body": "", "labels": []}
    api.issues.get.return_value = {"number": 42, "body": "<!-- NOTICE_META\n-->\n", "labels": []}
    api.issues.list_for_repo.return_value = []
    api.issues.list_labels_for_repo.return_value = []
    return api


@pytest.fixture
def sample_notice() -> Notice:
    return Notice(
        source_id="97042",
        board_id="MAPP_1708240139",
        title="2026 대학축제 개최 안내",
        body_text="5월 20일~22일 천안캠퍼스 대학축제.",
        source_url="https://www.hoseo.ac.kr/Home/BBSView.mbz?action=MAPP_1708240139&schIdx=97042",
        published_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        crawled_at=datetime(2026, 5, 9, 3, 0, tzinfo=timezone.utc),
        author="학생처",
        image_urls=["https://www.hoseo.ac.kr/ThumbnailPrint.do?dir=editor&savename=img1.jpg"],
        attachments=[AttachmentRef(url="https://www.hoseo.ac.kr/download/file.pdf", filename="2026축제.pdf", mime_type="application/pdf")],
    )


@pytest.fixture
def sample_asset() -> Asset:
    return Asset(
        asset_id="MAPP_1708240139-97042-img-001",
        parent_notice_id="MAPP_1708240139-97042",
        parent_issue_number=42,
        type="image",
        sequence=1,
        total_in_notice=1,
        src_url="https://www.hoseo.ac.kr/ThumbnailPrint.do?dir=editor&savename=img1.jpg",
    )


@pytest.fixture
def tmp_cache_dir(tmp_path) -> Path:
    cache = tmp_path / ".cache"
    cache.mkdir()
    return cache
