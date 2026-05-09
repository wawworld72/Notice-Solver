import typer

infer_app = typer.Typer(help="추론 파이프라인 (Phase 3 — 향후 구현 예정)")


@infer_app.command("run")
def infer_run(
    topic: str = typer.Argument(..., help="분석 주제 (예: '장학금 패턴')"),
    labels: str = typer.Option("", help="조회할 GitHub Issue 레이블 (콤마 구분)"),
    limit: int = typer.Option(30, help="참조할 최대 공지 수"),
):
    """수집·정리된 공지를 분석하여 추론 Issue를 생성합니다. (보류)"""
    typer.echo("[보류] 추론 기능은 향후 별도 스펙(002-knowledge-inference)에서 구현됩니다.")
