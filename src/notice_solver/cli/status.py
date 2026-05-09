import typer

status_app = typer.Typer(help="전체 파이프라인 현황")


@status_app.callback(invoke_without_command=True)
def status(
    ctx: typer.Context,
    board: str = typer.Option("", help="게시판 필터"),
):
    """전체 파이프라인 현황을 출력합니다."""
    if ctx.invoked_subcommand is not None:
        return

    try:
        from notice_solver.config import Settings
        settings = Settings()
    except Exception as e:
        typer.echo(f"[오류] 설정 로드 실패: {e}", err=True)
        raise typer.Exit(code=3)

    from notice_solver.github.issues import GitHubIssues
    from notice_solver.models.crawl_run import CrawlRun

    gh = GitHubIssues(settings.github_token, settings.github_repo_owner, settings.github_repo_name)

    label_filter = f"board:{board}" if board else ""

    phase_counts: dict[str, int] = {"collection": 0, "organization": 0, "inference": 0}
    for issue in gh.list_issues(labels=label_filter, state="open", limit=5000):
        labels = [lbl["name"] if isinstance(lbl, dict) else str(lbl) for lbl in issue.get("labels", [])]
        for lbl in labels:
            if lbl.startswith("phase:"):
                key = lbl[len("phase:"):]
                phase_counts[key] = phase_counts.get(key, 0) + 1

    status_counts: dict[str, int] = {}
    for issue in gh.list_issues(labels="type:asset", state="open", limit=5000):
        labels_raw = issue.get("labels", [])
        labels = [lbl["name"] if isinstance(lbl, dict) else str(lbl) for lbl in labels_raw]
        for lbl in labels:
            if lbl.startswith("status:"):
                key = lbl[len("status:"):]
                status_counts[key] = status_counts.get(key, 0) + 1

    last_collect = CrawlRun.load_latest(settings.cache_dir, "collect")
    last_ocr = CrawlRun.load_latest(settings.cache_dir, "ocr")

    repo = f"{settings.github_repo_owner}/{settings.github_repo_name}"
    board_label = board or settings.default_board_id
    typer.echo(f"Notice-Solver 현황")
    typer.echo("═" * 41)
    typer.echo(f"저장소: {repo}")
    typer.echo(f"게시판: {board_label}")
    typer.echo("")
    typer.echo("공지 현황")
    typer.echo("─" * 33)
    typer.echo(f"  phase:collection  : {phase_counts.get('collection', 0):>6}개 (자산 생성 대기)")
    typer.echo(f"  phase:organization: {phase_counts.get('organization', 0):>6}개 (정리 완료)")
    typer.echo(f"  phase:inference   : {phase_counts.get('inference', 0):>6}개 (추론 완료)")
    typer.echo("")
    typer.echo("자산 현황")
    typer.echo("─" * 33)
    for key in ("raw", "ocr-complete", "no-text", "ocr-failed", "auth-required"):
        typer.echo(f"  status:{key:<17}: {status_counts.get(key, 0):>6}개")
    typer.echo("")
    typer.echo("마지막 실행")
    typer.echo("─" * 33)
    if last_collect:
        ts = last_collect.finished_at.strftime("%Y-%m-%d %H:%M") if last_collect.finished_at else "진행 중"
        typer.echo(f"  수집: {ts}  ({last_collect.processed}건 수집)")
    else:
        typer.echo("  수집: 기록 없음")
    if last_ocr:
        ts = last_ocr.finished_at.strftime("%Y-%m-%d %H:%M") if last_ocr.finished_at else "진행 중"
        typer.echo(f"  OCR:  {ts}  ({last_ocr.processed}건 처리)")
    else:
        typer.echo("  OCR:  기록 없음")
