"""Smoke tests for the CLI entrypoint."""

from click.testing import CliRunner

from llmdocs.cli import cli


def test_cli_version_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_version_command() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert result.output.strip() == "0.1.0"


def test_help_lists_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "serve" in result.output
