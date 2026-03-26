"""Tests for file hashing."""

from pathlib import Path

from llmdocs.hasher import FileHasher


def test_hash_file(tmp_path: Path) -> None:
    """Test hashing a file."""
    file_path = tmp_path / "test.md"
    file_path.write_text("# Test Document\n\nContent here.", encoding="utf-8")

    hasher = FileHasher()
    hash1 = hasher.hash_file(file_path)

    assert hash1
    assert len(hash1) == 64

    hash2 = hasher.hash_file(file_path)
    assert hash1 == hash2


def test_hash_changes_when_content_changes(tmp_path: Path) -> None:
    """Test that hash changes when file content changes."""
    file_path = tmp_path / "test.md"
    file_path.write_text("# Original Content", encoding="utf-8")

    hasher = FileHasher()
    hash1 = hasher.hash_file(file_path)

    file_path.write_text("# Modified Content", encoding="utf-8")
    hash2 = hasher.hash_file(file_path)

    assert hash1 != hash2


def test_hash_directory(tmp_path: Path) -> None:
    """Test hashing all files in directory."""
    (tmp_path / "doc1.md").write_text("# Doc 1", encoding="utf-8")
    (tmp_path / "doc2.md").write_text("# Doc 2", encoding="utf-8")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "doc3.md").write_text("# Doc 3", encoding="utf-8")

    hasher = FileHasher()
    hashes = hasher.hash_directory(tmp_path)

    assert len(hashes) == 3
    assert "/doc1.md" in hashes
    assert "/doc2.md" in hashes
    assert "/subdir/doc3.md" in hashes


def test_detect_changes() -> None:
    """Test detecting changes between hash sets."""
    old_hashes = {
        "/doc1.md": "hash1",
        "/doc2.md": "hash2",
        "/doc3.md": "hash3",
    }

    new_hashes = {
        "/doc1.md": "hash1",
        "/doc2.md": "hash2_modified",
        "/doc4.md": "hash4",
    }

    hasher = FileHasher()
    changed, added, deleted = hasher.detect_changes(old_hashes, new_hashes)

    assert changed == {"/doc2.md"}
    assert added == {"/doc4.md"}
    assert deleted == {"/doc3.md"}
