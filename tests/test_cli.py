"""Tests for the CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from llmdocs import __version__
from llmdocs.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """A tmp directory with a valid llmdocs.yaml and a docs/ tree."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text(
        '---\ntitle: "Home"\ndescription: "Welcome."\ncategory: "General"\norder: 1\n---\n\n# Home\n',
        encoding="utf-8",
    )
    (docs_dir / "guide.md").write_text(
        '---\ntitle: "Guide"\ndescription: "A guide."\ncategory: "Tutorial"\norder: 1\n---\n\n# Guide\n',
        encoding="utf-8",
    )
    llms_out = tmp_path / "llms.txt"
    (tmp_path / "llmdocs.yaml").write_text(
        f"docs_dir: {docs_dir}\n" f"llms_txt:\n  output_path: {llms_out}\n",
        encoding="utf-8",
    )
    return tmp_path


# ── version ────────────────────────────────────────────────────────────────


def test_version_flag(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_version_command(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


# ── init ───────────────────────────────────────────────────────────────────


def test_init_creates_config_and_sample_doc(runner: CliRunner, tmp_path: Path) -> None:
    with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0, result.output
        assert (Path(fs) / "llmdocs.yaml").exists()
        assert (Path(fs) / "docs" / "index.md").exists()


def test_init_output_mentions_created_files(runner: CliRunner, tmp_path: Path) -> None:
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["init"])
    assert "llmdocs.yaml" in result.output
    assert "index.md" in result.output


def test_init_skips_existing_config_without_force(
    runner: CliRunner, tmp_path: Path
) -> None:
    with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
        cfg = Path(fs) / "llmdocs.yaml"
        cfg.write_text("original: true\n", encoding="utf-8")
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert "skip" in result.output
        assert cfg.read_text(encoding="utf-8") == "original: true\n"


def test_init_force_overwrites_existing(runner: CliRunner, tmp_path: Path) -> None:
    with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
        cfg = Path(fs) / "llmdocs.yaml"
        cfg.write_text("original: true\n", encoding="utf-8")
        runner.invoke(cli, ["init", "--force"])
        assert "original: true" not in cfg.read_text(encoding="utf-8")


def test_init_shows_next_steps(runner: CliRunner, tmp_path: Path) -> None:
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["init"])
    assert "serve" in result.output
    assert "validate" in result.output


# ── serve ──────────────────────────────────────────────────────────────────


def test_serve_missing_config_exits_nonzero(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(cli, ["serve", "--config", str(tmp_path / "nope.yaml")])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_serve_calls_run_server(runner: CliRunner, config_dir: Path) -> None:
    with patch("llmdocs.server.run_server") as mock_run:
        result = runner.invoke(
            cli,
            [
                "serve",
                "--config",
                str(config_dir / "llmdocs.yaml"),
                "--data-dir",
                str(config_dir / "data"),
            ],
        )
    assert result.exit_code == 0, result.output
    mock_run.assert_called_once()


def test_serve_overrides_host_and_port(runner: CliRunner, config_dir: Path) -> None:
    with patch("llmdocs.server.run_server") as mock_run:
        runner.invoke(
            cli,
            [
                "serve",
                "--config",
                str(config_dir / "llmdocs.yaml"),
                "--data-dir",
                str(config_dir / "data"),
                "--host",
                "127.0.0.1",
                "--port",
                "9999",
            ],
        )
    cfg_passed = mock_run.call_args[0][0]
    assert cfg_passed.server.host == "127.0.0.1"
    assert cfg_passed.server.port == 9999


def test_serve_passes_watch_flag(runner: CliRunner, config_dir: Path) -> None:
    with patch("llmdocs.server.run_server") as mock_run:
        runner.invoke(
            cli,
            [
                "serve",
                "--config",
                str(config_dir / "llmdocs.yaml"),
                "--data-dir",
                str(config_dir / "data"),
                "--watch",
            ],
        )
    _, kwargs = mock_run.call_args
    assert kwargs.get("watch") is True or mock_run.call_args[0][2] is True


# ── build ──────────────────────────────────────────────────────────────────


def test_build_missing_config_exits_nonzero(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(cli, ["build", "--config", str(tmp_path / "nope.yaml")])
    assert result.exit_code != 0


def test_build_indexes_docs_and_writes_llms_txt(
    runner: CliRunner, config_dir: Path
) -> None:
    result = runner.invoke(
        cli,
        [
            "build",
            "--config",
            str(config_dir / "llmdocs.yaml"),
            "--data-dir",
            str(config_dir / "data"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Done" in result.output
    assert "Written" in result.output
    assert (config_dir / "llms.txt").exists()


def test_build_llms_txt_contains_docs(runner: CliRunner, config_dir: Path) -> None:
    runner.invoke(
        cli,
        [
            "build",
            "--config",
            str(config_dir / "llmdocs.yaml"),
            "--data-dir",
            str(config_dir / "data"),
        ],
    )
    content = (config_dir / "llms.txt").read_text(encoding="utf-8")
    assert "Home" in content
    assert "Guide" in content


# ── validate ───────────────────────────────────────────────────────────────


def test_validate_missing_config_exits_nonzero(
    runner: CliRunner, tmp_path: Path
) -> None:
    result = runner.invoke(cli, ["validate", "--config", str(tmp_path / "nope.yaml")])
    assert result.exit_code != 0


def test_validate_passes_for_valid_docs(runner: CliRunner, config_dir: Path) -> None:
    result = runner.invoke(
        cli, ["validate", "--config", str(config_dir / "llmdocs.yaml")]
    )
    assert result.exit_code == 0, result.output
    assert "no issues" in result.output.lower()


def test_validate_fails_when_description_missing(
    runner: CliRunner, tmp_path: Path
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "nodesc.md").write_text(
        '---\ntitle: "No Desc"\n---\n\n# No Desc\n',
        encoding="utf-8",
    )
    cfg = tmp_path / "llmdocs.yaml"
    cfg.write_text(f"docs_dir: {docs_dir}\n", encoding="utf-8")

    result = runner.invoke(cli, ["validate", "--config", str(cfg)])
    assert result.exit_code == 1
    assert "missing description" in result.output.lower()


def test_validate_reports_issue_count(runner: CliRunner, tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    for i in range(3):
        (docs_dir / f"doc{i}.md").write_text(
            f'---\ntitle: "Doc {i}"\n---\n\n# Doc {i}\n',
            encoding="utf-8",
        )
    cfg = tmp_path / "llmdocs.yaml"
    cfg.write_text(f"docs_dir: {docs_dir}\n", encoding="utf-8")

    result = runner.invoke(cli, ["validate", "--config", str(cfg)])
    assert result.exit_code == 1
    assert "3" in result.output
