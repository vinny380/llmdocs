"""Tests for llms.txt generation."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from llmdocs.llms_txt import generate_llms_txt, load_llms_txt
from llmdocs.models import Document, DocumentMetadata


def _doc(
    path: str,
    title: str,
    description: str = "",
    category: str = "General",
    order: int = 999,
) -> Document:
    return Document(
        path=path,
        title=title,
        description=description,
        content="",
        metadata=DocumentMetadata(category=category, order=order),
    )


# --- generate_llms_txt ---


def test_generate_starts_with_project_name() -> None:
    output = generate_llms_txt([])
    assert output.startswith("# llmdocs")


def test_generate_custom_project_name() -> None:
    output = generate_llms_txt([], project_name="My Docs")
    assert output.startswith("# My Docs")


def test_generate_groups_by_category() -> None:
    docs = [
        _doc("/a.md", "Alpha", category="Tutorial"),
        _doc("/b.md", "Beta", category="Reference"),
    ]
    output = generate_llms_txt(docs)
    assert "## Tutorial" in output
    assert "## Reference" in output


def test_generate_categories_sorted_alphabetically() -> None:
    docs = [
        _doc("/z.md", "Z", category="Zebra"),
        _doc("/a.md", "A", category="Apple"),
    ]
    output = generate_llms_txt(docs)
    assert output.index("## Apple") < output.index("## Zebra")


def test_generate_docs_sorted_by_order_within_category() -> None:
    docs = [
        _doc("/c.md", "Step C", category="Guide", order=3),
        _doc("/a.md", "Step A", category="Guide", order=1),
        _doc("/b.md", "Step B", category="Guide", order=2),
    ]
    output = generate_llms_txt(docs)
    assert output.index("Step A") < output.index("Step B") < output.index("Step C")


def test_generate_entry_with_description() -> None:
    docs = [_doc("/start.md", "Getting Started", description="Quick setup guide")]
    output = generate_llms_txt(docs)
    assert "- [Getting Started](/start.md): Quick setup guide" in output


def test_generate_entry_without_description() -> None:
    docs = [_doc("/start.md", "Getting Started")]
    output = generate_llms_txt(docs)
    assert "- [Getting Started](/start.md)" in output
    assert "- [Getting Started](/start.md):" not in output


def test_generate_output_ends_with_newline() -> None:
    assert generate_llms_txt([]).endswith("\n")
    assert generate_llms_txt([_doc("/a.md", "A")]).endswith("\n")


# --- load_llms_txt ---


def test_load_returns_none_when_no_override() -> None:
    assert load_llms_txt(None) is None


def test_load_returns_none_when_file_missing(tmp_path: Path) -> None:
    assert load_llms_txt(tmp_path / "nonexistent.txt") is None


def test_load_returns_file_content(tmp_path: Path) -> None:
    override = tmp_path / "llms.txt"
    override.write_text("# Custom\n\nOverride content\n", encoding="utf-8")
    assert load_llms_txt(override) == "# Custom\n\nOverride content\n"


# --- /llms.txt HTTP endpoint ---


def test_llms_txt_endpoint(test_client: TestClient) -> None:
    response = test_client.get("/llms.txt")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text
    assert body.startswith("# llmdocs")
    assert "/index.md" in body or "/guide.md" in body


def test_llms_txt_endpoint_has_categories(test_client: TestClient) -> None:
    response = test_client.get("/llms.txt")
    body = response.text
    assert "##" in body


def test_llms_txt_manual_override(test_config, tmp_path: Path) -> None:
    from llmdocs.server import create_app

    override_file = tmp_path / "custom_llms.txt"
    override_file.write_text("# Custom Override\n\nStatic content.\n", encoding="utf-8")
    test_config.llms_txt.manual_override = override_file

    app = create_app(config=test_config, data_dir=tmp_path / "data")
    with TestClient(app) as client:
        response = client.get("/llms.txt")

    assert response.status_code == 200
    assert "# Custom Override" in response.text
    assert "Static content." in response.text
