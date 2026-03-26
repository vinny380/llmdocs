"""Tests for configuration loading."""

from pathlib import Path

import pytest

from llmdocs.config import Config


def test_load_config_from_file(tmp_path: Path) -> None:
    """Test loading config from YAML file."""
    config_file = tmp_path / "llmdocs.yaml"
    config_file.write_text(
        """
docs_dir: ./docs
server:
  host: 0.0.0.0
  port: 8080
search:
  semantic_weight: 0.7
  keyword_weight: 0.3
  chunk_size: 500
embeddings:
  model: sentence-transformers/all-MiniLM-L6-v2
llms_txt:
  output_path: ./llms.txt
  manual_override: null
""",
        encoding="utf-8",
    )

    config = Config.load(config_file)

    # Relative paths are resolved against the config file's directory.
    assert config.docs_dir == (tmp_path / "docs").resolve()
    assert config.server.host == "0.0.0.0"
    assert config.server.port == 8080
    assert config.search.semantic_weight == 0.7
    assert config.search.keyword_weight == 0.3
    assert config.embeddings.model == "sentence-transformers/all-MiniLM-L6-v2"


def test_config_defaults() -> None:
    """Test default configuration values."""
    config = Config()

    assert config.docs_dir == Path("./docs")
    assert config.server.port == 8080
    assert config.search.semantic_weight == 0.7
    assert config.search.keyword_weight == 0.3


def test_load_empty_yaml_uses_defaults(tmp_path: Path) -> None:
    """Empty YAML file yields default config, paths resolved against config dir."""
    config_file = tmp_path / "empty.yaml"
    config_file.write_text("", encoding="utf-8")
    config = Config.load(config_file)
    assert config.docs_dir == (tmp_path / "docs").resolve()
    assert config.server.port == 8080


def test_load_resolves_relative_paths_against_config_dir(tmp_path: Path) -> None:
    """docs_dir and llms_txt paths are resolved relative to the config file, not cwd."""
    subdir = tmp_path / "project"
    subdir.mkdir()
    config_file = subdir / "llmdocs.yaml"
    config_file.write_text(
        "docs_dir: ./docs\nllms_txt:\n  output_path: ./out/llms.txt\n", encoding="utf-8"
    )

    config = Config.load(config_file)

    assert config.docs_dir == (subdir / "docs").resolve()
    assert config.llms_txt.output_path == (subdir / "out" / "llms.txt").resolve()


def test_load_absolute_paths_unchanged(tmp_path: Path) -> None:
    """Absolute paths in config are kept as-is."""
    config_file = tmp_path / "llmdocs.yaml"
    abs_docs = tmp_path / "my-docs"
    config_file.write_text(f"docs_dir: {abs_docs}\n", encoding="utf-8")

    config = Config.load(config_file)

    assert config.docs_dir == abs_docs.resolve()


def test_config_validation_weights_must_sum_to_one() -> None:
    """Test config validation - weights must sum to 1.0."""
    with pytest.raises(ValueError, match="must sum to 1.0"):
        Config(
            search=Config.SearchConfig(
                semantic_weight=0.8,
                keyword_weight=0.3,
            )
        )
