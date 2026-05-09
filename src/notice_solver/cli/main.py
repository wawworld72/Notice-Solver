import typer

from notice_solver.cli.assets import assets_app
from notice_solver.cli.infer import infer_app
from notice_solver.cli.ocr import ocr_app
from notice_solver.cli.status import status_app

app = typer.Typer(
    name="notice-solver",
    help="호서대학교 공지사항 수집 및 지식 베이스 구축 CLI 도구",
    no_args_is_help=True,
)

app.add_typer(assets_app, name="assets")
app.add_typer(ocr_app, name="ocr")
app.add_typer(infer_app, name="infer")
app.add_typer(status_app, name="status")

from notice_solver.cli.collect import register as _reg_collect
_reg_collect(app)


@app.command("init-labels")
def init_labels():
    """GitHub 저장소에 모든 레이블을 일괄 생성합니다."""
    try:
        from notice_solver.config import Settings
        settings = Settings()
    except Exception as e:
        typer.echo(f"[오류] 설정 로드 실패: {e}", err=True)
        raise typer.Exit(code=3)

    from ghapi.all import GhApi
    from notice_solver.github.labels import ensure_labels
    api = GhApi(owner=settings.github_repo_owner, repo=settings.github_repo_name, token=settings.github_token)
    created, skipped = ensure_labels(api, settings.github_repo_owner, settings.github_repo_name)
    typer.echo(f"[완료] 레이블 생성: {created}개 | 기존: {skipped}개")
