from datetime import datetime, timezone

import typer

from notice_solver.github.frontmatter import parse_notice_meta
from notice_solver.parsers.assets import extract_image_urls, extract_attachment_refs

assets_app = typer.Typer(help="자산 Issue 관리")


@assets_app.command("create")
def create(
    notice: int = typer.Option(0, "--notice", help="특정 공지 Issue 번호만 처리 (0=전체)"),
    limit: int = typer.Option(50, help="처리할 최대 공지 수"),
    dry_run: bool = typer.Option(False, "--dry-run", help="실제 Issue 생성 없이 결과만 출력"),
):
    """수집된 공지 Issues에서 자산 Issues를 생성합니다."""
    try:
        from notice_solver.config import Settings
        settings = Settings()
    except Exception as e:
        typer.echo(f"[오류] 설정 로드 실패: {e}", err=True)
        raise typer.Exit(code=3)

    from notice_solver.cache.index import AssetIndex
    from notice_solver.github.issues import GitHubIssues
    from notice_solver.models.asset import Asset
    from notice_solver.models.crawl_run import CrawlRun

    gh = GitHubIssues(settings.github_token, settings.github_repo_owner, settings.github_repo_name)
    asset_index = AssetIndex(settings.cache_dir)

    run = CrawlRun(
        run_id=datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
        pipeline="asset",
    )

    if notice > 0:
        notice_issues = [gh.get_issue(notice)]
    else:
        notice_issues = gh.list_issues(labels="phase:collection", state="open", limit=limit)

    total_images = 0
    total_attachments = 0

    for issue in notice_issues:
        body = issue.get("body") or ""
        meta = parse_notice_meta(body)
        notice_id = meta.get("id", "")
        issue_number = issue["number"]

        image_urls = extract_image_urls(body)
        attachment_refs = extract_attachment_refs(body)

        if not image_urls and not attachment_refs:
            typer.echo(f"[처리] 공지 #{issue_number} → 자산 없음 (has:no-assets)")
            run.processed += 1
            continue

        asset_issues_created: list[dict] = []

        for i, url in enumerate(image_urls, 1):
            asset_id = f"{notice_id}-img-{i:03d}"
            if asset_index.exists(asset_id):
                typer.echo(f"  스킵 (이미 생성됨): {asset_id}")
                run.skipped += 1
                continue
            asset = Asset(
                asset_id=asset_id,
                parent_notice_id=notice_id,
                parent_issue_number=issue_number,
                type="image",
                sequence=i,
                total_in_notice=len(image_urls),
                src_url=url,
            )
            if not dry_run:
                try:
                    num = gh.create_asset_issue(asset, notice_title=issue.get("title", ""))
                    asset_index.add(asset_id, num)
                    asset_issues_created.append({"number": num, "type": "image", "seq": i, "status": "raw"})
                    total_images += 1
                except Exception as e:
                    typer.echo(f"  [오류] 이미지 자산 생성 실패: {e}", err=True)
                    run.failed += 1
            else:
                typer.echo(f"  [dry-run] 이미지 자산: {asset_id}")
                total_images += 1

        for i, ref in enumerate(attachment_refs, 1):
            asset_id = f"{notice_id}-attach-{i:03d}"
            if asset_index.exists(asset_id):
                typer.echo(f"  스킵 (이미 생성됨): {asset_id}")
                run.skipped += 1
                continue
            asset = Asset(
                asset_id=asset_id,
                parent_notice_id=notice_id,
                parent_issue_number=issue_number,
                type="attachment",
                sequence=i,
                total_in_notice=len(attachment_refs),
                src_url=ref.url,
                filename=ref.filename,
                mime_type=ref.mime_type,
            )
            if not dry_run:
                try:
                    num = gh.create_asset_issue(asset, notice_title=issue.get("title", ""))
                    asset_index.add(asset_id, num)
                    asset_issues_created.append({"number": num, "type": "attachment", "seq": i, "status": "raw"})
                    total_attachments += 1
                except Exception as e:
                    typer.echo(f"  [오류] 첨부 자산 생성 실패: {e}", err=True)
                    run.failed += 1
            else:
                typer.echo(f"  [dry-run] 첨부 자산: {asset_id}")
                total_attachments += 1

        if asset_issues_created and not dry_run:
            try:
                gh.update_notice_body_with_assets(issue_number, asset_issues_created)
            except Exception as e:
                typer.echo(f"  [경고] 공지 Issue 업데이트 실패: {e}", err=True)

        typer.echo(f"[처리] 공지 #{issue_number} → 이미지 자산 {len(image_urls)}개, 첨부 자산 {len(attachment_refs)}개 생성")
        run.processed += 1

    run.finished_at = datetime.now(timezone.utc)
    typer.echo(f"[완료] 이미지 자산: {total_images}개 | 첨부 자산: {total_attachments}개 | {run.report()}")
    if not dry_run:
        run.save(settings.cache_dir)


@assets_app.command("status")
def status(
    board: str = typer.Option("", help="게시판 필터"),
):
    """자산 처리 현황을 출력합니다."""
    try:
        from notice_solver.config import Settings
        settings = Settings()
    except Exception as e:
        typer.echo(f"[오류] 설정 로드 실패: {e}", err=True)
        raise typer.Exit(code=3)

    from notice_solver.github.issues import GitHubIssues

    gh = GitHubIssues(settings.github_token, settings.github_repo_owner, settings.github_repo_name)
    label_filter = "type:asset"
    if board:
        label_filter += f",board:{board}"

    status_counts: dict[str, int] = {"raw": 0, "ocr-complete": 0, "no-text": 0, "ocr-failed": 0, "auth-required": 0}
    issues = gh.list_issues(labels=label_filter, state="open", limit=1000)
    for issue in issues:
        for lbl in issue.get("labels", []):
            name = lbl["name"] if isinstance(lbl, dict) else str(lbl)
            if name.startswith("status:"):
                key = name[len("status:"):]
                status_counts[key] = status_counts.get(key, 0) + 1

    board_label = f" (board: {board})" if board else ""
    typer.echo(f"자산 현황{board_label}")
    typer.echo("─" * 33)
    for key, count in status_counts.items():
        typer.echo(f"  {key:<20}: {count:>5}개")
