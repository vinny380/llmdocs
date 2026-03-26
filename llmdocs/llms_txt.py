"""llms.txt generation from indexed documentation."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import List, Optional

from llmdocs.models import Document


def generate_llms_txt(docs: List[Document], project_name: str = "llmdocs") -> str:
    """Generate llms.txt content grouping docs by category, sorted by order then path.

    Format follows the llms.txt standard:
      # Project Name
      ## Category
      - [Title](URL): Description
    """
    by_category: dict[str, list[Document]] = defaultdict(list)
    for doc in docs:
        by_category[doc.metadata.category].append(doc)

    lines: list[str] = [f"# {project_name}", ""]

    for category in sorted(by_category):
        sorted_docs = sorted(
            by_category[category], key=lambda d: (d.metadata.order, d.path)
        )
        lines.append(f"## {category}")
        lines.append("")
        for doc in sorted_docs:
            entry = f"- [{doc.title}]({doc.path})"
            if doc.description:
                entry += f": {doc.description}"
            lines.append(entry)
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


def load_llms_txt(override_path: Optional[Path]) -> Optional[str]:
    """Return the contents of ``override_path`` if it is an existing file, else ``None``."""
    if override_path is None or not override_path.is_file():
        return None
    return override_path.read_text(encoding="utf-8")
