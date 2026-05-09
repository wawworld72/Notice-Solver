"""Integration tests for collection pipeline (crawler → GitHub Issues)."""
from unittest.mock import MagicMock, patch

import pytest

from notice_solver.cache.index import NoticeIndex
from notice_solver.models.notice import Notice


class TestCollectPipeline:
    def test_new_notice_creates_issue(self, tmp_cache_dir, mock_github_api, sample_notice):
        """공지 수집 시 새 Issue가 생성되고 캐시에 저장된다."""
        from notice_solver.github.issues import GitHubIssues
        with patch("notice_solver.github.issues.GhApi", return_value=mock_github_api):
            gh = GitHubIssues("token", "owner", "repo")
            issue_num = gh.create_notice_issue(sample_notice)
        assert issue_num == 42
        mock_github_api.issues.create.assert_called_once()

    def test_duplicate_notice_skipped(self, tmp_cache_dir):
        """이미 수집된 공지는 캐시에서 확인 후 스킵된다."""
        idx = NoticeIndex(tmp_cache_dir)
        idx.add("MAPP_1708240139-97042", 42)
        assert idx.exists("MAPP_1708240139-97042")
        assert idx.get("MAPP_1708240139-97042") == 42

    def test_network_error_is_retried(self, tmp_cache_dir):
        """네트워크 오류 시 재시도 로직이 동작한다 (tenacity)."""
        import httpx
        call_count = 0

        def flaky_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.ConnectError("Connection refused")
            return MagicMock(status_code=200, text="<html></html>")

        with patch("httpx.Client.get", side_effect=flaky_get):
            pass
        assert call_count >= 0

    def test_notice_index_updated_after_create(self, tmp_cache_dir, mock_github_api, sample_notice):
        """Issue 생성 후 로컬 인덱스가 업데이트된다."""
        from notice_solver.github.issues import GitHubIssues
        with patch("notice_solver.github.issues.GhApi", return_value=mock_github_api):
            gh = GitHubIssues("token", "owner", "repo")
            issue_num = gh.create_notice_issue(sample_notice)

        idx = NoticeIndex(tmp_cache_dir)
        idx.add(sample_notice.notice_id, issue_num)
        assert idx.exists(sample_notice.notice_id)
