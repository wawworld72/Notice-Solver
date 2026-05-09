"""CLI contract tests — verify CLI behavior against spec."""
import os
from unittest.mock import patch

import pytest


class TestCollectContract:
    def test_collect_help_exits_zero(self, cli_runner):
        from notice_solver.cli.main import app
        result = cli_runner.invoke(app, ["collect", "--help"])
        assert result.exit_code == 0

    def test_collect_missing_token_exits_nonzero(self, cli_runner):
        from notice_solver.cli.main import app
        env = {k: v for k, v in os.environ.items() if k not in ("GITHUB_TOKEN",)}
        with patch.dict(os.environ, env, clear=True):
            result = cli_runner.invoke(app, ["collect"])
        assert result.exit_code in (1, 2, 3)

    def test_top_level_help(self, cli_runner):
        from notice_solver.cli.main import app
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "collect" in result.output
        assert "assets" in result.output
        assert "ocr" in result.output
        assert "status" in result.output
        assert "infer" in result.output


class TestAssetsContract:
    def test_assets_create_help(self, cli_runner):
        from notice_solver.cli.main import app
        result = cli_runner.invoke(app, ["assets", "create", "--help"])
        assert result.exit_code == 0

    def test_assets_status_help(self, cli_runner):
        from notice_solver.cli.main import app
        result = cli_runner.invoke(app, ["assets", "status", "--help"])
        assert result.exit_code == 0


class TestOcrContract:
    def test_ocr_run_help(self, cli_runner):
        from notice_solver.cli.main import app
        result = cli_runner.invoke(app, ["ocr", "run", "--help"])
        assert result.exit_code == 0
        assert "--limit" in result.output
        assert "--type" in result.output
        assert "--retry-failed" in result.output

    def test_ocr_status_help(self, cli_runner):
        from notice_solver.cli.main import app
        result = cli_runner.invoke(app, ["ocr", "status", "--help"])
        assert result.exit_code == 0


class TestStatusContract:
    def test_status_help(self, cli_runner):
        from notice_solver.cli.main import app
        result = cli_runner.invoke(app, ["status", "--help"])
        assert result.exit_code == 0


class TestInferContract:
    def test_infer_run_stub_exits_zero(self, cli_runner):
        from notice_solver.cli.main import app
        result = cli_runner.invoke(app, ["infer", "run", "테스트주제"])
        assert result.exit_code == 0
        assert "보류" in result.output

    def test_infer_run_help(self, cli_runner):
        from notice_solver.cli.main import app
        result = cli_runner.invoke(app, ["infer", "run", "--help"])
        assert result.exit_code == 0


class TestInitLabelsContract:
    def test_init_labels_help(self, cli_runner):
        from notice_solver.cli.main import app
        result = cli_runner.invoke(app, ["init-labels", "--help"])
        assert result.exit_code == 0
