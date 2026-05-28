"""Strip manuscript markdown so TTS reads prose, not markup."""
from __future__ import annotations

import re


def strip_markdown(text: str) -> str:
    """Light cleanup for pasted chapter fragments."""
    if not text or not text.strip():
        return ""

    t = text.replace("\r\n", "\n")

    # YAML frontmatter
    if t.startswith("---"):
        end = t.find("\n---", 3)
        if end != -1:
            t = t[end + 4 :]

    # ATX headings -> plain line
    t = re.sub(r"^#{1,6}\s+", "", t, flags=re.MULTILINE)

    # Bold/italic
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    t = re.sub(r"_([^_]+)_", r"\1", t)

    # Links [text](url) -> text
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)

    # Inline code
    t = re.sub(r"`([^`]+)`", r"\1", t)

    # Blockquotes
    t = re.sub(r"^>\s?", "", t, flags=re.MULTILINE)

    # Horizontal rules
    t = re.sub(r"^[-*_]{3,}\s*$", "", t, flags=re.MULTILINE)

    # Collapse excessive blank lines
    t = re.sub(r"\n{3,}", "\n\n", t)

    return t.strip()


def split_paragraphs(text: str) -> list[str]:
    """Split into speakable chunks (paragraphs)."""
    cleaned = strip_markdown(text)
    if not cleaned:
        return []
    parts = re.split(r"\n\s*\n+", cleaned)
    chunks: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Very long paragraphs: split on sentence boundaries
        if len(part) > 1200:
            sentences = re.split(r"(?<=[.!?])\s+", part)
            buf = ""
            for sent in sentences:
                if len(buf) + len(sent) + 1 > 900 and buf:
                    chunks.append(buf.strip())
                    buf = sent
                else:
                    buf = f"{buf} {sent}".strip() if buf else sent
            if buf.strip():
                chunks.append(buf.strip())
        else:
            chunks.append(part)
    return chunks
