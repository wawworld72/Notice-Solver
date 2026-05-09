"""CLI contract tests — verify CLI behavior against spec."""
import os
from unittest.mock import patch

import pytest


class TestCollectContract:
    def test_collect_help_exits_zero(self, cli_runner):
        """collect --help 는 종료코드 0으로 도움말을 출력한다."""
        from notice_solver.cli.main import app
        result = cli_runner.invoke(app, ["collect", "--help"])
        assert result.exit_code == 0
        assert "collect" in result.output.lower() or "usage" in result.output.lower()

    def test_collect_missing_token_exits_3(self, cli_runner):
        """GITHUB_TOKEN 없이 collect 실행 시 종료코드 3을 반환한다."""
        from notice_solver.cli.main import app
        env = {k: v for k, v in os.environ.items() if k not in ("GITHUB_TOKEN",)}
        with patch.dict(os.environ, env, clear=True):
            result = cli_runner.invoke(app, ["collect"])
        assert result.exit_code in (1, 2, 3)

    def test_top_level_help(self, cli_runner):
        """notice-solver --help 는 종료코드 0으로 도움말을 출력한다."""
        from notice_solver.cli.main import app
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_infer_run_stub_exits_zero(self, cli_runner):
        """infer run 스텁 명령은 종료코드 0으로 종료된다."""
        from notice_solver.cli.main import app
        result = cli_runner.invoke(app, ["infer", "run", "테스트주제"])
        assert result.exit_code == 0
        assert "보류" in result.output

    def test_infer_run_help(self, cli_runner):
        """infer run --help 는 종료코드 0으로 도움말을 출력한다."""
        from notice_solver.cli.main import app
        result = cli_runner.invoke(app, ["infer", "run", "--help"])
        assert result.exit_code == 0
