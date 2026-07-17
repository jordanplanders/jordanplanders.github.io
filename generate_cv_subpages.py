#!/usr/bin/env python3
"""
Generate Quarto include fragments for CV sections from a BibTeX file.

Usage:
  python generate_cv_subpages.py

This script reads:
  - jlanders_CV/CV_ref.bib

And writes:
  - subpages/posters.qmd                 (type: inproceedings)
  - subpages/articles.qmd                (type: article)
  - subpages/educational_materials.qmd   (type: edumat)
  - subpages/seminars.qmd                (type: talk)
  - subpages/conference_talks.qmd        (type: unpublished)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, List


ROOT = Path(__file__).resolve().parent
BIB_PATH = ROOT / "jlanders_CV" / "CV_ref.bib"
OUT_DIR = ROOT / "subpages"

CATEGORY_TO_TYPE = {
    "posters.qmd": "inproceedings",
    "articles.qmd": "article",
    "educational_materials.qmd": "edumat",
    "seminars.qmd": "talk",
    "conference_talks.qmd": "unpublished",
}


@dataclass
class BibEntry:
    entry_type: str
    key: str
    fields: Dict[str, str]


def strip_outer_wrappers(value: str) -> str:
    text = value.strip()
    while len(text) >= 2 and (
        (text.startswith("{") and text.endswith("}"))
        or (text.startswith('"') and text.endswith('"'))
    ):
        text = text[1:-1].strip()
    return text


def normalize_text(value: str) -> str:
    text = strip_outer_wrappers(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_year(value: str) -> int:
    text = normalize_text(value)
    m = re.search(r"\d{4}", text)
    return int(m.group(0)) if m else -1


def strip_bib_comments(text: str) -> str:
    """Remove '%' comments to end-of-line (unless escaped as '\\%')."""
    out: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "%" and (i == 0 or text[i - 1] != "\\"):
            while i < n and text[i] not in "\r\n":
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def parse_bibtex_entries(text: str) -> List[BibEntry]:
    text = strip_bib_comments(text)
    entries: List[BibEntry] = []
    i = 0
    n = len(text)

    while i < n:
        at = text.find("@", i)
        if at == -1:
            break

        j = at + 1
        while j < n and (text[j].isalnum() or text[j] in "_-"):
            j += 1
        if j == at + 1:
            i = at + 1
            continue

        entry_type = text[at + 1 : j].strip().lower()

        while j < n and text[j].isspace():
            j += 1
        if j >= n or text[j] != "{":
            i = at + 1
            continue

        depth = 0
        k = j
        while k < n:
            ch = text[k]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1

        # Tolerant behavior: malformed trailing content is skipped.
        if k >= n:
            break

        inner = text[j + 1 : k].strip()
        parsed = parse_entry_inner(entry_type, inner)
        if parsed is not None:
            entries.append(parsed)

        i = k + 1

    return entries


def parse_entry_inner(entry_type: str, inner: str) -> BibEntry | None:
    if not inner:
        return None

    comma_idx = find_top_level_comma(inner)
    if comma_idx == -1:
        return None

    key = inner[:comma_idx].strip()
    if not key:
        return None

    fields_blob = inner[comma_idx + 1 :]
    fields = parse_fields(fields_blob)
    return BibEntry(entry_type=entry_type, key=key, fields=fields)


def find_top_level_comma(text: str) -> int:
    depth = 0
    in_quotes = False
    escape = False
    for idx, ch in enumerate(text):
        if in_quotes:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_quotes = False
            continue

        if ch == '"':
            in_quotes = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            return idx
    return -1


def parse_fields(blob: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    i = 0
    n = len(blob)

    while i < n:
        while i < n and (blob[i].isspace() or blob[i] == ","):
            i += 1
        if i >= n:
            break

        name_start = i
        while i < n and (blob[i].isalnum() or blob[i] in "_-"):
            i += 1
        if i == name_start:
            i += 1
            continue

        field_name = blob[name_start:i].strip().lower()
        while i < n and blob[i].isspace():
            i += 1
        if i >= n or blob[i] != "=":
            i += 1
            continue
        i += 1
        while i < n and blob[i].isspace():
            i += 1
        if i >= n:
            break

        value, i = read_value(blob, i)
        fields[field_name] = value.strip()

    return fields


def read_value(text: str, i: int) -> tuple[str, int]:
    n = len(text)
    if i >= n:
        return "", i

    if text[i] == "{":
        depth = 0
        start = i
        while i < n:
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    i += 1
                    return text[start:i], i
            i += 1
        return text[start:], n

    if text[i] == '"':
        start = i
        i += 1
        escape = False
        while i < n:
            ch = text[i]
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                i += 1
                break
            i += 1
        return text[start:i], i

    start = i
    while i < n and text[i] not in ",\n\r":
        i += 1
    return text[start:i], i


def sanitize_url(url: str) -> str:
    text = normalize_text(url)
    text = re.sub(r"^\\url\{", "", text)
    text = re.sub(r"\}$", "", text)
    return text


def format_entry(entry: BibEntry) -> str:
    f = entry.fields
    year = normalize_text(f.get("year", ""))
    author = normalize_text(f.get("author", ""))
    title = normalize_text(f.get("title", ""))
    venue = normalize_text(f.get("journal", "")) or normalize_text(f.get("booktitle", ""))
    address = normalize_text(f.get("address", ""))
    note = normalize_text(f.get("note", ""))
    url = sanitize_url(f.get("url", ""))

    parts: List[str] = []
    if year:
        parts.append(f"**{year}**")
    if author:
        parts.append(author)
    if title:
        parts.append(f'"{title}"')
    if venue:
        parts.append(venue)
    if address:
        parts.append(address)
    if note:
        parts.append(note)
    if url:
        parts.append(f"[link]({url})")

    if not parts:
        parts.append(entry.key)

    return "- " + ". ".join(parts) + "."


def sort_entries(entries: List[BibEntry]) -> List[BibEntry]:
    def sort_key(entry: BibEntry) -> tuple[int, str, str]:
        year = parse_year(entry.fields.get("year", ""))
        title = normalize_text(entry.fields.get("title", "")).lower()
        return (year, title, entry.key.lower())

    return sorted(entries, key=sort_key, reverse=True)


def build_output(entries: List[BibEntry]) -> str:
    if not entries:
        return "<!-- No entries found for this category. -->\n"
    lines = [format_entry(e) for e in entries]
    return "\n".join(lines) + "\n"


def main() -> None:
    if not BIB_PATH.exists():
        raise SystemExit(f"Missing BibTeX file: {BIB_PATH}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = BIB_PATH.read_text(encoding="utf-8")
    all_entries = parse_bibtex_entries(raw)

    for filename, bib_type in CATEGORY_TO_TYPE.items():
        filtered = [e for e in all_entries if e.entry_type == bib_type]
        filtered = sort_entries(filtered)
        output_text = build_output(filtered)
        (OUT_DIR / filename).write_text(output_text, encoding="utf-8")

    print(f"Parsed {len(all_entries)} entries from {BIB_PATH}")
    for filename, bib_type in CATEGORY_TO_TYPE.items():
        count = sum(1 for e in all_entries if e.entry_type == bib_type)
        print(f"{filename}: {count} ({bib_type})")


if __name__ == "__main__":
    main()
