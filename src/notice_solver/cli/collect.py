import logging
import sys
from datetime import datetime, timezone

import typer

logger = logging.getLogger(__name__)


def register(app: typer.Typer) -> None:
    @app.command("collect")
    def collect(
        board: str = typer.Option("", help="게시판 ID (기본: DEFAULT_BOARD_ID)"),
        full: bool = typer.Option(False, help="전체 재수집 (기본: 증분)"),
        limit: int = typer.Option(0, help="수집할 최대 공지 수 (기본: 무제한)"),
        dry_run: bool = typer.Option(False, "--dry-run", help="실제 Issue 생성 없이 수집 결과만 출력"),
    ):
        """게시판을 크롤링하여 공지를 GitHub Issues로 수집합니다."""
        try:
            from notice_solver.config import Settings
            settings = Settings()
        except Exception as e:
            typer.echo(f"[오류] 설정 로드 실패: {e}", err=True)
            raise typer.Exit(code=3)

        from notice_solver.cache.index import NoticeIndex
        from notice_solver.crawlers.hoseo import HoseoCrawler, BOARD_ID
        from notice_solver.github.issues import GitHubIssues
        from notice_solver.models.crawl_run import CrawlRun

        board_id = board or settings.default_board_id
        run = CrawlRun(
            run_id=datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
            pipeline="collect",
            board_id=board_id,
        )

        index = NoticeIndex(settings.cache_dir)

        mode = "전체" if full else "증분"
        typer.echo(f"[{_now()}] 수집 시작: {board_id} ({mode}){' [dry-run]' if dry_run else ''}")

        try:
            gh = GitHubIssues(settings.github_token, settings.github_repo_owner, settings.github_repo_name)
        except Exception as e:
            typer.echo(f"[오류] GitHub API 초기화 실패: {e}", err=True)
            raise typer.Exit(code=2)

        # GitHub Issues를 권위 있는 중복 방지 인덱스로 사용
        # (로컬 캐시는 만료될 수 있으므로 Issues가 항상 최신 기준)
        if not dry_run:
            typer.echo(f"[{_now()}] GitHub Issues에서 기수집 목록 조회 중...")
            gh_known = gh.get_known_notice_ids()
            typer.echo(f"[{_now()}] GitHub Issues 확인: {len(gh_known)}건 / 로컬 캐시: {len(index)}건")
            for nid, inum in gh_known.items():
                if not index.exists(nid):
                    index._data[nid] = inum
            if gh_known:
                index.save()
            typer.echo(f"[{_now()}] 기수집 합계: {len(index)}건")

        known_ids = set(_read_index_keys(index))

        with HoseoCrawler(delay_sec=settings.request_delay_sec, retry_count=settings.retry_count) as crawler:
            try:
                for notice in crawler.crawl_incremental(full=full, limit=limit, known_ids=known_ids):
                    if index.exists(notice.notice_id):
                        typer.echo(f"[{_now()}] 공지 {notice.source_id} → 스킵 (이미 수집됨)")
                        run.skipped += 1
                        continue

                    imgs = len(notice.image_urls)
                    attachs = len(notice.attachments)
                    if dry_run:
                        typer.echo(
                            f"[{_now()}] [dry-run] 공지 {notice.source_id}: {notice.title[:40]} "
                            f"(이미지 {imgs}개, 첨부 {attachs}개)"
                        )
                        run.processed += 1
                    else:
                        try:
                            issue_num = gh.create_notice_issue(notice)
                            index.add(notice.notice_id, issue_num)
                            typer.echo(
                                f"[{_now()}] 공지 {notice.source_id} → Issue #{issue_num} 생성 "
                                f"(이미지 {imgs}개, 첨부 {attachs}개)"
                            )
                            run.processed += 1
                        except Exception as e:
                            typer.echo(f"[오류] 공지 {notice.source_id}: {e}", err=True)
                            run.failed += 1
                            run.errors.append({"id": notice.notice_id, "reason": str(e)})

            except Exception as e:
                typer.echo(f"[오류] 크롤링 실패: {e}", err=True)
                raise typer.Exit(code=1)

        run.finished_at = datetime.now(timezone.utc)
        typer.echo(run.report())
        if not dry_run:
            run.save(settings.cache_dir)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _read_index_keys(index) -> list[str]:
    return list(index._data.keys())
