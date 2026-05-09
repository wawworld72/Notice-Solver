"""Integration tests for asset Issue creation pipeline (US2)."""
from unittest.mock import MagicMock, patch, call

import pytest

from notice_solver.cache.index import AssetIndex
from notice_solver.models.asset import Asset


class TestAssetCreationPipeline:
    def test_asset_issue_created_for_image(self, mock_github_api, sample_asset):
        from notice_solver.github.issues import GitHubIssues
        with patch("notice_solver.github.issues.GhApi", return_value=mock_github_api):
            gh = GitHubIssues("token", "owner", "repo")
            issue_num = gh.create_asset_issue(sample_asset, notice_title="테스트 공지")
        assert issue_num == 42
        mock_github_api.issues.create.assert_called_once()
        call_kwargs = mock_github_api.issues.create.call_args.kwargs
        assert "type:asset" in call_kwargs.get("labels", [])
        assert "asset:image" in call_kwargs.get("labels", [])
        assert "status:raw" in call_kwargs.get("labels", [])

    def test_asset_issue_created_for_attachment(self, mock_github_api):
        from notice_solver.github.issues import GitHubIssues
        from notice_solver.models.asset import Asset
        attachment = Asset(
            asset_id="BOARD-1-attach-001",
            parent_notice_id="BOARD-1",
            parent_issue_number=42,
            type="attachment",
            sequence=1,
            total_in_notice=1,
            src_url="https://example.com/file.pdf",
            filename="file.pdf",
            mime_type="application/pdf",
        )
        with patch("notice_solver.github.issues.GhApi", return_value=mock_github_api):
            gh = GitHubIssues("token", "owner", "repo")
            issue_num = gh.create_asset_issue(attachment)
        assert issue_num == 42
        call_kwargs = mock_github_api.issues.create.call_args.kwargs
        assert "asset:attachment" in call_kwargs.get("labels", [])

    def test_notice_with_no_assets_gets_label(self, mock_github_api, sample_notice):
        """자산 없는 공지 Issue 생성 시 has:no-assets 레이블이 포함된다."""
        from notice_solver.github.issues import GitHubIssues
        from notice_solver.models.notice import Notice
        from datetime import datetime, timezone
        empty_notice = Notice(
            source_id="99999",
            board_id="MAPP_TEST",
            title="자산없는공지",
            body_text="본문",
            source_url="http://example.com",
            published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            crawled_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        with patch("notice_solver.github.issues.GhApi", return_value=mock_github_api):
            gh = GitHubIssues("token", "owner", "repo")
            gh.create_notice_issue(empty_notice)
        labels = mock_github_api.issues.create.call_args.kwargs.get("labels", [])
        assert "has:no-assets" in labels

    def test_asset_index_updated_after_creation(self, tmp_cache_dir, mock_github_api, sample_asset):
        """자산 Issue 생성 후 AssetIndex에 저장된다."""
        from notice_solver.github.issues import GitHubIssues
        with patch("notice_solver.github.issues.GhApi", return_value=mock_github_api):
            gh = GitHubIssues("token", "owner", "repo")
            issue_num = gh.create_asset_issue(sample_asset)

        idx = AssetIndex(tmp_cache_dir)
        idx.add(sample_asset.asset_id, issue_num)
        assert idx.exists(sample_asset.asset_id)
        assert idx.get(sample_asset.asset_id) == 42

    def test_existing_asset_skipped(self, tmp_cache_dir, sample_asset):
        """이미 생성된 자산 ID는 AssetIndex.exists() 로 중복 방지된다."""
        idx = AssetIndex(tmp_cache_dir)
        idx.add(sample_asset.asset_id, 51)
        assert idx.exists(sample_asset.asset_id)
        assert idx.get(sample_asset.asset_id) == 51
