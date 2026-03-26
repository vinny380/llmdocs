"""Tests for configuration loading."""

from pathlib import Path

import pytest

from llmdocs.config import Config, _resolve_env_vars


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


# ── embeddings config ─────────────────────────────────────────────────────


def test_embeddings_config_defaults() -> None:
    cfg = Config.EmbeddingsConfig()
    assert cfg.provider == "local"
    assert cfg.model == "sentence-transformers/all-MiniLM-L6-v2"
    assert cfg.api_key is None
    assert cfg.base_url is None


def test_embeddings_config_openai_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="api_key is required"):
        Config.EmbeddingsConfig(provider="openai", model="text-embedding-3-small")


def test_embeddings_config_openai_with_literal_key() -> None:
    cfg = Config.EmbeddingsConfig(
        provider="openai", model="text-embedding-3-small", api_key="sk-test123"
    )
    assert cfg.resolved_api_key() == "sk-test123"


def test_embeddings_config_env_var_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_KEY", "secret-from-env")
    cfg = Config.EmbeddingsConfig(
        provider="openai", model="text-embedding-3-small", api_key="${MY_KEY}"
    )
    assert cfg.resolved_api_key() == "secret-from-env"


def test_embeddings_config_local_ignores_extra_fields() -> None:
    """local provider does not error when api_key / base_url are present."""
    cfg = Config.EmbeddingsConfig(
        provider="local", api_key="unused", base_url="http://unused"
    )
    assert cfg.provider == "local"


def test_resolve_env_vars_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("A", "hello")
    monkeypatch.setenv("B", "world")
    assert _resolve_env_vars("${A}-${B}") == "hello-world"
    assert _resolve_env_vars(None) is None
    assert _resolve_env_vars("literal") == "literal"


def test_load_config_with_openai_embeddings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TEST_KEY", "sk-test")
    config_file = tmp_path / "llmdocs.yaml"
    config_file.write_text(
        "embeddings:\n"
        "  provider: openai\n"
        "  model: text-embedding-3-small\n"
        "  api_key: ${TEST_KEY}\n"
        "  base_url: http://localhost:4000\n",
        encoding="utf-8",
    )
    config = Config.load(config_file)
    assert config.embeddings.provider == "openai"
    assert config.embeddings.model == "text-embedding-3-small"
    assert config.embeddings.resolved_api_key() == "sk-test"
    assert config.embeddings.base_url == "http://localhost:4000"
