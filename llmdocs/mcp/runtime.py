"""Runtime state shared between the HTTP server lifespan and MCP tools."""

from __future__ import annotations

from dataclasses import dataclass

from llmdocs.config import Config
from llmdocs.indexing.parser import DocumentParser
from llmdocs.indexing.search import HybridSearchEngine


@dataclass
class LlmdocsRuntime:
    """Populated during FastAPI lifespan; MCP tools read from it at request time."""

    search_engine: HybridSearchEngine | None = None
    parser: DocumentParser | None = None
    config: Config | None = None
