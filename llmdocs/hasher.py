"""File hashing for freshness detection."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Set, Tuple


class FileHasher:
    """Compute and compare file hashes for incremental indexing."""

    def hash_file(self, file_path: Path) -> str:
        """Compute SHA256 hash of file content."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def hash_directory(self, docs_dir: Path) -> Dict[str, str]:
        """Hash all markdown files under docs_dir (recursive)."""
        hashes: Dict[str, str] = {}
        for md_file in sorted(docs_dir.rglob("*.md")):
            if md_file.is_file():
                rel = md_file.relative_to(docs_dir)
                rel_path = "/" + rel.as_posix()
                hashes[rel_path] = self.hash_file(md_file)
        return hashes

    def detect_changes(
        self,
        old_hashes: Dict[str, str],
        new_hashes: Dict[str, str],
    ) -> Tuple[Set[str], Set[str], Set[str]]:
        """Return (changed, added, deleted) path sets."""
        old_paths = set(old_hashes.keys())
        new_paths = set(new_hashes.keys())

        added = new_paths - old_paths
        deleted = old_paths - new_paths
        common_paths = old_paths & new_paths
        changed = {p for p in common_paths if old_hashes[p] != new_hashes[p]}

        return changed, added, deleted
