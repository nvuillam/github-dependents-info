"""Tests for CLI argument parsing"""

import subprocess


def test_cli_no_duplicate_param_warnings():
    """Test that help command doesn't show duplicate parameter warnings"""
    result = subprocess.run(
        ["github-dependents-info", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    # Should not have duplicate parameter warnings
    assert "parameter -d is used more than once" not in result.stderr
    assert "parameter -c is used more than once" not in result.stderr


def test_cli_args_without_equals():
    """Test CLI accepts arguments without equals sign"""
    result = subprocess.run(
        [
            "github-dependents-info",
            "--repo",
            "test/repo",
            "--markdownfile",
            "./test.md",
            "--sort",
            "stars",
            "--verbose",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    # Should not have parsing errors
    assert "unexpected extra arguments" not in result.stderr
    assert "does not take a value" not in result.stderr


def test_cli_args_with_equals():
    """Test CLI accepts arguments with equals sign"""
    result = subprocess.run(
        [
            "github-dependents-info",
            "--repo=test/repo",
            "--markdownfile=./test.md",
            "--sort=stars",
            "--verbose",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    # Should not have parsing errors
    assert "unexpected extra arguments" not in result.stderr
    assert "does not take a value" not in result.stderr
