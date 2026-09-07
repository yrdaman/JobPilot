import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
import tiktoken


@dataclass
class Chunk:
    text: str
    metadata: dict[str, Any]


KEYWORDS = [
    "summary", "profile", "skills", "experience",
    "education", "projects", "certifications", "internship"
]

SECTION_ALIASES = {
    "summary": "summary",
    "profile": "summary",
    "skills": "skills",
    "experience": "experience",
    "work": "experience",
    "internship": "experience",
    "education": "education",
    "project": "projects",
    "projects": "projects",
    "certification": "certifications",
    "certifications": "certifications",
}

BAD_HEADING_PREFIXES = [
    "cgpa", "gpa", "email", "linkedin", "github", "phone"
]


@lru_cache(maxsize=1)
def _encoding():
    return tiktoken.get_encoding("cl100k_base")


def token_count(text: str) -> int:
    enc = _encoding()
    return len(enc.encode(text))


def split_by_tokens(text: str, max_tokens: int = 350, overlap_tokens: int = 40) -> list[str]:
    if max_tokens <= 0:
        raise ValueError("max_tokens must be greater than zero")
    if overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be between zero and max_tokens - 1")

    enc = _encoding()
    ids = enc.encode(text)

    chunks = []
    start = 0
    n = len(ids)

    while start < n:
        end = min(start + max_tokens, n)
        piece = enc.decode(ids[start:end]).strip()
        if piece:
            chunks.append(piece)
        if end == n:
            break
        start = max(0, end - overlap_tokens)

    return chunks


def looks_like_heading(line: str) -> bool:
    s = line.strip()
    if not s:
        return False

    # length guard
    if len(s) > 70:
        return False

    # headings usually don't end with period
    if s.endswith("."):
        return False

    lower = s.lower()

    # Bullet content is evidence, even when it contains a section keyword.
    if s.startswith(("- ", "* ", "• ", "● ", "▪ ", "◦ ")):
        return False

    # reject obvious non-headings
    if any(lower.startswith(b) for b in BAD_HEADING_PREFIXES):
        return False

    # reject lines with numeric score patterns like "CGPA: 7.29/10"
    if re.search(r"\d+(\.\d+)?\s*/\s*\d+", s):
        return False

    # reject contact-ish lines
    if "|" in s and any(k in lower for k in ["email", "linkedin", "github"]):
        return False

    # A sentence-like line is unlikely to be a section label.
    if any(mark in s for mark in [",", ";", ":", "!", "?"]):
        return False

    words = s.split()
    if len(words) > 8:
        return False

    has_keyword = any(re.search(rf"\b{re.escape(k)}\b", lower) for k in KEYWORDS)

    alpha = [c for c in s if c.isalpha()]
    upper_ratio = (sum(1 for c in alpha if c.isupper()) / len(alpha)) if alpha else 0.0

    # all caps label like "RELEVANT SKILLS"
    all_caps_like = (
        upper_ratio > 0.75
        and (has_keyword or len(words) >= 3)
    )

    heading_case = s.isupper() or all(
        not word.isalpha() or word[0].isupper()
        for word in words
    )

    return all_caps_like or (has_keyword and heading_case)


def normalize_section_name(title: str) -> str:
    """Return a stable key while retaining the original title in metadata."""
    lower = title.lower()
    for alias, canonical in SECTION_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", lower):
            return canonical
    if title == "GENERAL":
        return "general"
    return "other"


def section_split(text: str) -> list[dict]:
    if not text or not text.strip():
        return []

    lines = text.splitlines()

    sections = []
    current_title = "GENERAL"
    current_lines = []
    detected = 0

    for index, line in enumerate(lines):
        stripped = line.strip()

        if looks_like_heading(stripped):
            if current_lines:
                sections.append({
                    "section": current_title,
                    "section_key": normalize_section_name(current_title),
                    "text": "\n".join(current_lines).strip()
                })
            current_title = stripped
            current_lines = []
            detected += 1
        else:
            if stripped:
                current_lines.append(stripped)

    if current_lines:
        sections.append({
            "section": current_title,
            "section_key": normalize_section_name(current_title),
            "text": "\n".join(current_lines).strip()
        })

    # Use one general section only when no heading was detected at all.
    if detected == 0:
        return [{
            "section": "GENERAL",
            "section_key": "general",
            "text": text.strip(),
        }]

    return sections


def chunk_resume_hybrid(
    resume_text: str,
    max_tokens: int = 350,
    overlap_tokens: int = 40
) -> list[Chunk]:
    if max_tokens <= 0:
        raise ValueError("max_tokens must be greater than zero")
    if overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be between zero and max_tokens - 1")

    sections = section_split(resume_text)
    output: list[Chunk] = []

    chunk_id = 0
    for sec in sections:
        sec_name = sec["section"]
        section_key = sec["section_key"]
        sec_text = sec["text"]

        if not sec_text:
            continue

        if token_count(sec_text) <= max_tokens:
            output.append(
                Chunk(
                    text=sec_text,
                    metadata={
                        "chunk_id": chunk_id,
                        "section": sec_name,
                        "section_key": section_key,
                        "strategy": "section"
                    },
                )
            )
            chunk_id += 1
            continue

        parts = split_by_tokens(
            sec_text,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
        )
        for part, part_index in zip(parts, range(1, len(parts) + 1)):
            output.append(
                Chunk(
                    text=part,
                    metadata={
                        "chunk_id": chunk_id,
                        "section": sec_name,
                        "section_key": section_key,
                        "strategy": "section+token",
                        "part": part_index,
                        "parts_total": len(parts),
                    },
                )
            )
            chunk_id += 1

    return output