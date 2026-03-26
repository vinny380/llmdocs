"""Runtime state shared by HTTP routes and MCP tools."""

from __future__ import annotations

from dataclasses import dataclass

from llmdocs.config import Config
from llmdocs.parser import DocumentParser
from llmdocs.search import HybridSearchEngine


@dataclass
class LlmdocsRuntime:
    """Populated during FastAPI lifespan before MCP tools run."""

    search_engine: HybridSearchEngine | None = None
    parser: DocumentParser | None = None
    config: Config | None = None
