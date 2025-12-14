"""Tests for CLI argument parsing"""

from github_dependents_info.__main__ import app
from typer.testing import CliRunner

runner = CliRunner()


def test_cli_no_duplicate_param_warnings():
    """Test that help command doesn't show duplicate parameter warnings"""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "parameter -d is used more than once" not in result.stderr
    assert "parameter -c is used more than once" not in result.stderr


def test_cli_args_without_equals():
    """Test CLI accepts arguments without equals sign"""
    result = runner.invoke(
        app,
        [
            "--repo",
            "test/repo",
            "--markdownfile",
            "./test.md",
            "--sort",
            "stars",
            "--verbose",
        ],
    )
    assert "unexpected extra arguments" not in result.stderr
    assert "does not take a value" not in result.stderr


def test_cli_args_with_equals():
    """Test CLI accepts arguments with equals sign"""
    result = runner.invoke(
        app,
        [
            "--repo=test/repo",
            "--markdownfile=./test.md",
            "--sort=stars",
            "--verbose",
        ],
    )
    assert "unexpected extra arguments" not in result.stderr
    assert "does not take a value" not in result.stderr
