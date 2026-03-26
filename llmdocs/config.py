"""Configuration loading from llmdocs.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, field_validator, model_validator


class Config(BaseModel):
    """Main configuration for llmdocs."""

    class ServerConfig(BaseModel):
        """Server configuration."""

        host: str = "0.0.0.0"
        port: int = 8080

    class SearchConfig(BaseModel):
        """Search configuration."""

        semantic_weight: float = 0.7
        keyword_weight: float = 0.3
        chunk_size: int = 500

        @model_validator(mode="after")
        def validate_weights(self) -> SearchConfig:
            """Validate that weights sum to 1.0."""
            total = self.semantic_weight + self.keyword_weight
            if abs(total - 1.0) > 0.001:
                raise ValueError(
                    f"semantic_weight + keyword_weight must sum to 1.0, got {total}"
                )
            return self

    class EmbeddingsConfig(BaseModel):
        """Embeddings configuration."""

        model: str = "sentence-transformers/all-MiniLM-L6-v2"

    class LlmsTxtConfig(BaseModel):
        """llms.txt generation configuration."""

        output_path: Path = Path("./llms.txt")
        manual_override: Optional[Path] = None

        @field_validator("output_path", "manual_override", mode="before")
        @classmethod
        def path_or_none(cls, v: Any) -> Any:
            if v is None:
                return None
            return Path(v) if isinstance(v, str) else v

    docs_dir: Path = Path("./docs")
    server: ServerConfig = ServerConfig()
    search: SearchConfig = SearchConfig()
    embeddings: EmbeddingsConfig = EmbeddingsConfig()
    llms_txt: LlmsTxtConfig = LlmsTxtConfig()

    @field_validator("docs_dir", mode="before")
    @classmethod
    def resolve_docs_dir(cls, v: Any) -> Path:
        """Convert string paths to Path objects."""
        return Path(v) if isinstance(v, str) else v

    @classmethod
    def load(cls, config_path: Path) -> Config:
        """Load configuration from YAML file.

        Relative paths in the config (``docs_dir``, ``llms_txt.output_path``,
        ``llms_txt.manual_override``) are resolved relative to the directory
        that contains the config file, not the current working directory.
        """
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            data = {}
        cfg = cls(**data)
        base = config_path.resolve().parent

        if not cfg.docs_dir.is_absolute():
            cfg = cfg.model_copy(update={"docs_dir": (base / cfg.docs_dir).resolve()})

        lt = cfg.llms_txt
        lt_updates: dict = {}
        if not lt.output_path.is_absolute():
            lt_updates["output_path"] = (base / lt.output_path).resolve()
        if lt.manual_override is not None and not lt.manual_override.is_absolute():
            lt_updates["manual_override"] = (base / lt.manual_override).resolve()
        if lt_updates:
            cfg = cfg.model_copy(update={"llms_txt": lt.model_copy(update=lt_updates)})

        return cfg
