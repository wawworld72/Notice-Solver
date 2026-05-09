import typer

from notice_solver.cli.infer import infer_app

app = typer.Typer(
    name="notice-solver",
    help="호서대학교 공지사항 수집 및 지식 베이스 구축 CLI 도구",
    no_args_is_help=True,
)

app.add_typer(infer_app, name="infer")

from notice_solver.cli.collect import register as _reg_collect
_reg_collect(app)
