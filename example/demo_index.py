#!/usr/bin/env python3
"""
Minimal end-to-end example: markdown → parse → chunk → Chroma → hybrid search.

Run from the repository root after installing the package:

    pip install -e .
    python example/demo_index.py

Requires network on first run (downloads the embedding model).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from llmdocs.chunker import DocumentChunker
from llmdocs.hasher import FileHasher
from llmdocs.indexer import DocumentIndexer
from llmdocs.parser import DocumentParser
from llmdocs.search import HybridSearchEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        docs = root / "docs"
        docs.mkdir()
        data = root / "data"
        data.mkdir()

        (docs / "intro.md").write_text(
            """---
title: "Introduction"
description: "Getting started"
category: "Guide"
---

# Introduction

Welcome to the example project.

## Install

Run `pip install something` to install dependencies.
""",
            encoding="utf-8",
        )

        (docs / "api.md").write_text(
            """---
title: "API"
category: "Reference"
---

# API

Use the REST endpoint `/search` for queries.
""",
            encoding="utf-8",
        )

        parser = DocumentParser()
        chunker = DocumentChunker(max_chunk_tokens=256)
        hasher = FileHasher()
        indexer = DocumentIndexer(data_dir=data)

        docs_list = parser.load_all(docs)
        all_chunks = []
        hashes = hasher.hash_directory(docs)

        for doc in docs_list:
            doc.file_hash = hashes[doc.path]
            for ch in chunker.chunk(doc):
                ch.metadata["file_hash"] = doc.file_hash
                all_chunks.append(ch)

        indexer.index_chunks(all_chunks)

        engine = HybridSearchEngine(
            indexer=indexer,
            semantic_weight=0.7,
            keyword_weight=0.3,
        )

        query = "how do I install"
        print(f"Query: {query!r}\n")
        for i, hit in enumerate(engine.search(query, limit=3), start=1):
            print(f"{i}. score={hit.score:.4f}  {hit.url}")
            print(f"   {hit.content_chunk[:120].replace(chr(10), ' ')}...")
            print()


if __name__ == "__main__":
    main()
