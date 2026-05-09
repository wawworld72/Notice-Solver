from datetime import datetime, timezone

import httpx
import typer

ocr_app = typer.Typer(help="OCR 배치 처리")


@ocr_app.command("run")
def run(
    limit: int = typer.Option(50, help="처리할 최대 자산 수"),
    type_: str = typer.Option("all", "--type", help="자산 유형 필터: image | attachment | all"),
    retry_failed: bool = typer.Option(False, "--retry-failed", help="status:ocr-failed 자산 재시도"),
):
    """status:raw 자산 Issues에 OCR/텍스트 추출을 실행합니다."""
    try:
        from notice_solver.config import Settings
        settings = Settings()
    except Exception as e:
        typer.echo(f"[오류] 설정 로드 실패: {e}", err=True)
        raise typer.Exit(code=3)

    from notice_solver.github.frontmatter import parse_asset_meta
    from notice_solver.github.issues import GitHubIssues
    from notice_solver.models.crawl_run import CrawlRun
    from notice_solver.ocr.document import ExtractionError, get_extractor
    from notice_solver.ocr.image import EasyOCRWrapper

    gh = GitHubIssues(settings.github_token, settings.github_repo_owner, settings.github_repo_name)

    status_label = "status:ocr-failed" if retry_failed else "status:raw"
    labels_filter = f"type:asset,{status_label}"
    if type_ == "image":
        labels_filter += ",asset:image"
    elif type_ == "attachment":
        labels_filter += ",asset:attachment"

    asset_issues = gh.list_issues(labels=labels_filter, state="open", limit=limit)
    if not asset_issues:
        typer.echo(f"처리할 자산 없음 ({status_label})")
        return

    ocr_wrapper = EasyOCRWrapper(confidence_threshold=settings.ocr_confidence_threshold)
    run = CrawlRun(
        run_id=datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
        pipeline="ocr",
    )

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for issue in asset_issues:
            num = issue["number"]
            body = issue.get("body") or ""
            meta = parse_asset_meta(body)
            asset_type = meta.get("type", "")
            src_url = meta.get("src_url") or meta.get("full_url", "")

            if not src_url:
                typer.echo(f"[경고] 자산 #{num}: URL 없음 — 스킵", err=True)
                run.skipped += 1
                continue

            try:
                response = client.get(src_url)
                response.raise_for_status()
                file_bytes = response.content
            except Exception as e:
                typer.echo(f"[오류] 자산 #{num}: 다운로드 실패 ({e})", err=True)
                gh.update_asset_issue(num, ocr_text="", status="ocr-failed")
                run.failed += 1
                run.errors.append({"issue": num, "reason": str(e)})
                continue

            try:
                if asset_type == "image":
                    text, confidence = ocr_wrapper.extract(file_bytes)
                    if not text:
                        gh.update_asset_issue(num, ocr_text="", status="no-text")
                        typer.echo(f"[처리] 자산 #{num} (이미지) → 텍스트 없음")
                    else:
                        gh.update_asset_issue(num, ocr_text=text, status="ocr-complete", confidence=confidence)
                        typer.echo(f"[처리] 자산 #{num} (이미지) → OCR 완료, 신뢰도 {confidence:.2f}, 텍스트 {len(text)}자")
                else:
                    mime_type = meta.get("mime_type", "")
                    extractor = get_extractor(mime_type)
                    if extractor is None:
                        typer.echo(f"[경고] 자산 #{num}: 지원하지 않는 형식 ({mime_type})", err=True)
                        gh.update_asset_issue(num, ocr_text="", status="no-text")
                        run.skipped += 1
                        continue

                    text = extractor.extract(file_bytes)
                    if not text.strip():
                        gh.update_asset_issue(num, ocr_text="", status="no-text")
                        typer.echo(f"[처리] 자산 #{num} (첨부) → 텍스트 없음")
                    else:
                        gh.update_asset_issue(num, ocr_text=text, status="ocr-complete")
                        typer.echo(f"[처리] 자산 #{num} ({mime_type}) → 텍스트 추출 완료, {len(text)}자")

                run.processed += 1

            except ExtractionError as e:
                typer.echo(f"[오류] 자산 #{num}: {e}", err=True)
                gh.update_asset_issue(num, ocr_text="", status="ocr-failed")
                run.failed += 1
                run.errors.append({"issue": num, "reason": str(e)})
            except Exception as e:
                typer.echo(f"[오류] 자산 #{num}: {e}", err=True)
                gh.update_asset_issue(num, ocr_text="", status="ocr-failed")
                run.failed += 1
                run.errors.append({"issue": num, "reason": str(e)})

    run.finished_at = datetime.now(timezone.utc)
    typer.echo(run.report())
    run.save(settings.cache_dir)


@ocr_app.command("status")
def status():
    """OCR 처리 현황을 출력합니다."""
    try:
        from notice_solver.config import Settings
        settings = Settings()
    except Exception as e:
        typer.echo(f"[오류] 설정 로드 실패: {e}", err=True)
        raise typer.Exit(code=3)

    from notice_solver.github.issues import GitHubIssues

    gh = GitHubIssues(settings.github_token, settings.github_repo_owner, settings.github_repo_name)
    image_counts: dict[str, int] = {}
    attach_counts: dict[str, int] = {}

    for issue in gh.list_issues(labels="type:asset", state="open", limit=2000):
        labels = [lbl["name"] if isinstance(lbl, dict) else str(lbl) for lbl in issue.get("labels", [])]
        is_image = "asset:image" in labels
        is_attach = "asset:attachment" in labels
        for lbl in labels:
            if lbl.startswith("status:"):
                key = lbl[len("status:"):]
                if is_image:
                    image_counts[key] = image_counts.get(key, 0) + 1
                elif is_attach:
                    attach_counts[key] = attach_counts.get(key, 0) + 1

    typer.echo("OCR 현황")
    typer.echo("─" * 33)
    typer.echo("이미지 자산")
    for key in ("raw", "ocr-complete", "no-text", "ocr-failed"):
        typer.echo(f"  {key:<20}: {image_counts.get(key, 0):>5}개")
    typer.echo("첨부 자산")
    for key in ("raw", "ocr-complete", "no-text", "ocr-failed"):
        typer.echo(f"  {key:<20}: {attach_counts.get(key, 0):>5}개")
