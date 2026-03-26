"""Document chunking for search indexing."""

from __future__ import annotations

import re
from typing import List

import tiktoken

from llmdocs.models import Chunk, Document


def _slug_anchor(section_name: str) -> str:
    s = section_name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


class DocumentChunker:
    """Chunks documents for better search precision."""

    def __init__(self, max_chunk_tokens: int = 500) -> None:
        self.max_chunk_tokens = max_chunk_tokens
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoder.encode(text))

    def _split_tokens(self, text: str) -> List[str]:
        """Split text into pieces each under max_chunk_tokens (byte-safe)."""
        ids = self.encoder.encode(text)
        if len(ids) <= self.max_chunk_tokens:
            return [text]
        out: List[str] = []
        step = self.max_chunk_tokens
        for i in range(0, len(ids), step):
            chunk_ids = ids[i : i + step]
            out.append(self.encoder.decode(chunk_ids))
        return out

    def chunk(self, document: Document) -> List[Chunk]:
        """Chunk a document into searchable pieces."""
        chunks: List[Chunk] = []
        content = document.content

        h2_pattern = r"^##\s+(.+)$"
        h2_matches = list(re.finditer(h2_pattern, content, re.MULTILINE))

        if not h2_matches:
            chunk = self._create_chunk(
                document=document,
                chunk_index=0,
                title_hierarchy=[document.title],
                content=content.strip(),
                section_name="",
            )
            return [chunk]

        for i, match in enumerate(h2_matches):
            h2_title = match.group(1).strip()
            start_pos = match.end()
            end_pos = h2_matches[i + 1].start() if i + 1 < len(h2_matches) else len(content)
            section_content = content[start_pos:end_pos].strip()

            has_h3 = bool(re.search(r"^###\s+", section_content, re.MULTILINE))
            too_big = self.count_tokens(section_content) > self.max_chunk_tokens

            if has_h3 or too_big:
                sub = self._split_large_section(
                    document=document,
                    parent_hierarchy=[document.title, h2_title],
                    section_content=section_content,
                    section_name=h2_title,
                    chunk_index_offset=len(chunks),
                )
                chunks.extend(sub)
            else:
                chunks.append(
                    self._create_chunk(
                        document=document,
                        chunk_index=len(chunks),
                        title_hierarchy=[document.title, h2_title],
                        content=section_content,
                        section_name=h2_title,
                    )
                )

        return chunks

    def _split_large_section(
        self,
        document: Document,
        parent_hierarchy: List[str],
        section_content: str,
        section_name: str,
        chunk_index_offset: int,
    ) -> List[Chunk]:
        """Split a large section by H3 or paragraphs."""
        chunks: List[Chunk] = []
        h3_pattern = r"^###\s+(.+)$"
        h3_matches = list(re.finditer(h3_pattern, section_content, re.MULTILINE))

        if h3_matches:
            for i, match in enumerate(h3_matches):
                h3_title = match.group(1).strip()
                start = match.end()
                end = h3_matches[i + 1].start() if i + 1 < len(h3_matches) else len(section_content)
                body = section_content[start:end].strip()

                if i == 0:
                    intro = section_content[: match.start()].strip()
                    if intro:
                        body = f"{intro}\n\n{body}".strip()

                if self.count_tokens(body) > self.max_chunk_tokens:
                    paras = [p.strip() for p in body.split("\n\n") if p.strip()]
                    for para in paras:
                        for piece in self._split_tokens(para):
                            chunks.append(
                                self._create_chunk(
                                    document=document,
                                    chunk_index=chunk_index_offset + len(chunks),
                                    title_hierarchy=parent_hierarchy + [h3_title],
                                    content=piece,
                                    section_name=h3_title,
                                )
                            )
                else:
                    chunks.append(
                        self._create_chunk(
                            document=document,
                            chunk_index=chunk_index_offset + len(chunks),
                            title_hierarchy=parent_hierarchy + [h3_title],
                            content=body,
                            section_name=h3_title,
                        )
                    )
            return chunks

        return self._split_by_paragraphs(
            document=document,
            parent_hierarchy=parent_hierarchy,
            section_content=section_content,
            section_name=section_name,
            chunk_index_offset=chunk_index_offset,
        )

    def _split_by_paragraphs(
        self,
        document: Document,
        parent_hierarchy: List[str],
        section_content: str,
        section_name: str,
        chunk_index_offset: int,
    ) -> List[Chunk]:
        chunks: List[Chunk] = []
        paragraphs = [p.strip() for p in section_content.split("\n\n") if p.strip()]

        current_parts: List[str] = []
        current_tokens = 0

        def flush() -> None:
            nonlocal current_parts, current_tokens
            if not current_parts:
                return
            text = "\n\n".join(current_parts)
            chunks.append(
                self._create_chunk(
                    document=document,
                    chunk_index=chunk_index_offset + len(chunks),
                    title_hierarchy=parent_hierarchy,
                    content=text,
                    section_name=section_name,
                )
            )
            current_parts = []
            current_tokens = 0

        for para in paragraphs:
            pieces = self._split_tokens(para)
            for piece in pieces:
                pt = self.count_tokens(piece)
                if pt > self.max_chunk_tokens:
                    flush()
                    for sp in self._split_tokens(piece):
                        chunks.append(
                            self._create_chunk(
                                document=document,
                                chunk_index=chunk_index_offset + len(chunks),
                                title_hierarchy=parent_hierarchy,
                                content=sp,
                                section_name=section_name,
                            )
                        )
                    continue
                if current_parts and current_tokens + pt > self.max_chunk_tokens:
                    flush()
                current_parts.append(piece)
                current_tokens += pt

        flush()
        return chunks

    def _create_chunk(
        self,
        document: Document,
        chunk_index: int,
        title_hierarchy: List[str],
        content: str,
        section_name: str,
    ) -> Chunk:
        anchor = ""
        if section_name:
            anchor = "#" + _slug_anchor(section_name)

        return Chunk(
            chunk_id=f"{document.path}_chunk{chunk_index}",
            doc_path=document.path,
            title_hierarchy=title_hierarchy,
            content=content,
            url=f"{document.path}{anchor}",
            metadata={"category": document.metadata.category},
        )
