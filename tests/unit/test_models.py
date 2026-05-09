"""Unit tests for data models."""
from datetime import datetime, timezone

import pytest

from notice_solver.models.notice import AttachmentRef, Notice
from notice_solver.models.asset import Asset


class TestNotice:
    def test_notice_id_derived(self):
        notice = Notice(
            source_id="97042",
            board_id="MAPP_1708240139",
            title="테스트",
            body_text="본문",
            source_url="http://example.com",
            published_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
            crawled_at=datetime(2026, 5, 9, tzinfo=timezone.utc),
        )
        assert notice.notice_id == "MAPP_1708240139-97042"

    def test_default_phase(self):
        notice = Notice(
            source_id="1",
            board_id="BOARD",
            title="t",
            body_text="b",
            source_url="u",
            published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            crawled_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        assert notice.phase == "collection"

    def test_default_empty_assets(self):
        notice = Notice(
            source_id="1",
            board_id="B",
            title="t",
            body_text="b",
            source_url="u",
            published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            crawled_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        assert notice.image_urls == []
        assert notice.attachments == []
        assert notice.github_issue_number is None

    def test_attachment_ref(self):
        ref = AttachmentRef(url="http://example.com/f.pdf", filename="f.pdf", mime_type="application/pdf")
        assert ref.filename == "f.pdf"
        assert ref.mime_type == "application/pdf"


class TestAsset:
    def test_asset_defaults(self):
        asset = Asset(
            asset_id="BOARD-1-img-001",
            parent_notice_id="BOARD-1",
            parent_issue_number=42,
            type="image",
            sequence=1,
            total_in_notice=3,
            src_url="http://example.com/img.jpg",
        )
        assert asset.ocr_status == "raw"
        assert asset.ocr_text == ""
        assert asset.ocr_confidence == 0.0
        assert asset.github_issue_number is None

    def test_asset_type_image(self):
        asset = Asset(
            asset_id="id",
            parent_notice_id="pid",
            parent_issue_number=1,
            type="image",
            sequence=1,
            total_in_notice=1,
            src_url="http://example.com/img.jpg",
        )
        assert asset.type == "image"

    def test_asset_type_attachment(self):
        asset = Asset(
            asset_id="id",
            parent_notice_id="pid",
            parent_issue_number=1,
            type="attachment",
            sequence=1,
            total_in_notice=1,
            src_url="http://example.com/file.pdf",
            filename="file.pdf",
            mime_type="application/pdf",
        )
        assert asset.type == "attachment"
        assert asset.filename == "file.pdf"
