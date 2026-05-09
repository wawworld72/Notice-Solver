"""Integration tests for OCR pipeline (US3)."""
from unittest.mock import MagicMock, patch

import pytest


class TestOcrPipeline:
    def test_image_asset_ocr_complete(self, mock_github_api, sample_asset):
        """status:raw 이미지 자산 → OCR 완료 → status:ocr-complete 전환."""
        from notice_solver.github.issues import GitHubIssues

        mock_github_api.issues.get.return_value = {
            "number": 42,
            "body": "<!-- ASSET_META\nasset_id: test\n-->\n## OCR 결과\n\n_미처리_\n",
            "labels": [{"name": "status:raw"}, {"name": "type:asset"}],
        }
        mock_github_api.issues.update.return_value = {}

        with patch("notice_solver.github.issues.GhApi", return_value=mock_github_api):
            gh = GitHubIssues("token", "owner", "repo")
            gh.update_asset_issue(42, ocr_text="안녕하세요", status="ocr-complete", confidence=0.92)

        mock_github_api.issues.update.assert_called_once()
        call_kwargs = mock_github_api.issues.update.call_args.kwargs
        assert "status:ocr-complete" in call_kwargs.get("labels", [])
        assert "status:raw" not in call_kwargs.get("labels", [])

    def test_image_asset_no_text(self, mock_github_api, sample_asset):
        """OCR 결과 없음 → status:no-text 전환."""
        from notice_solver.github.issues import GitHubIssues

        mock_github_api.issues.get.return_value = {
            "number": 42,
            "body": "## OCR 결과\n_미처리_\n",
            "labels": [{"name": "status:raw"}],
        }
        with patch("notice_solver.github.issues.GhApi", return_value=mock_github_api):
            gh = GitHubIssues("token", "owner", "repo")
            gh.update_asset_issue(42, ocr_text="", status="no-text")

        call_kwargs = mock_github_api.issues.update.call_args.kwargs
        assert "status:no-text" in call_kwargs.get("labels", [])

    def test_image_asset_ocr_failed(self, mock_github_api):
        """OCR 실패 → status:ocr-failed 전환."""
        from notice_solver.github.issues import GitHubIssues

        mock_github_api.issues.get.return_value = {
            "number": 51,
            "body": "## OCR 결과\n_미처리_\n",
            "labels": [{"name": "status:raw"}],
        }
        with patch("notice_solver.github.issues.GhApi", return_value=mock_github_api):
            gh = GitHubIssues("token", "owner", "repo")
            gh.update_asset_issue(51, ocr_text="", status="ocr-failed")

        call_kwargs = mock_github_api.issues.update.call_args.kwargs
        assert "status:ocr-failed" in call_kwargs.get("labels", [])
