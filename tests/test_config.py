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

    assert config.docs_dir == Path("./docs")
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
    """Empty YAML file yields default config."""
    config_file = tmp_path / "empty.yaml"
    config_file.write_text("", encoding="utf-8")
    config = Config.load(config_file)
    assert config.docs_dir == Path("./docs")
    assert config.server.port == 8080


def test_config_validation_weights_must_sum_to_one() -> None:
    """Test config validation - weights must sum to 1.0."""
    with pytest.raises(ValueError, match="must sum to 1.0"):
        Config(
            search=Config.SearchConfig(
                semantic_weight=0.8,
                keyword_weight=0.3,
            )
        )
