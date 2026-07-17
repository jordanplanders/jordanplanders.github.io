#!/usr/bin/env python3
"""
Build script: injects content from ./content into index.html.

Targets in your current HTML:
- professional  -> #resume (div.col-lg-6[data-aos-delay="100"]) under "Professional Experience"
- teaching      -> #resume (same column) under "Teaching"
- talks         -> #news ul
- community     -> #community ul
- software      -> optional: injects into an element with id="software" if you add one later

Input formats:
- YAML: structured lists (recommended for professional/teaching)
- Markdown: simple lists/paragraphs (recommended for talks/community/software)

Output:
- writes index.built.html (does not overwrite index.html unless you want it to)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import sys

# --- optional deps ---
try:
    import yaml  # pip install pyyaml
except Exception as e:
    yaml = None

try:
    from bs4 import BeautifulSoup  # pip install beautifulsoup4
except Exception:
    BeautifulSoup = None

# Markdown renderer: try markdown, then markdown2; else fallback to minimal.
_md_renderer = None
try:
    import markdown as _markdown  # pip install markdown
    _md_renderer = ("markdown", _markdown)
except Exception:
    try:
        import markdown2 as _markdown2  # pip install markdown2
        _md_renderer = ("markdown2", _markdown2)
    except Exception:
        _md_renderer = None


ROOT = Path(__file__).resolve().parent
CONTENT_DIR = ROOT / "content"
OUTPUT_DIR = ROOT / 'site'


def die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_yaml(path: Path) -> Any:
    if yaml is None:
        die("PyYAML not installed. Run: pip install pyyaml")
    return yaml.safe_load(read_text(path))


def md_to_html(md: str) -> str:
    if _md_renderer is None:
        # minimal fallback: paragraphs + bullet lists starting with "- "
        lines = md.strip().splitlines()
        out: list[str] = []
        buf: list[str] = []
        in_ul = False
        for ln in lines:
            ln = ln.rstrip()
            if not ln:
                if buf:
                    out.append(f"<p>{' '.join(buf).strip()}</p>")
                    buf = []
                if in_ul:
                    out.append("</ul>")
                    in_ul = False
                continue
            if ln.lstrip().startswith("- "):
                if buf:
                    out.append(f"<p>{' '.join(buf).strip()}</p>")
                    buf = []
                if not in_ul:
                    out.append("<ul>")
                    in_ul = True
                out.append(f"<li>{ln.lstrip()[2:].strip()}</li>")
            else:
                buf.append(ln.strip())
        if buf:
            out.append(f"<p>{' '.join(buf).strip()}</p>")
        if in_ul:
            out.append("</ul>")
        return "\n".join(out)

    kind, lib = _md_renderer
    if kind == "markdown":
        return lib.markdown(md, extensions=["extra", "sane_lists"])
    return lib.markdown(md)  # markdown2


@dataclass
class Role:
    title: str
    org: Optional[str] = None
    dates: Optional[str] = None
    location: Optional[str] = None
    bullets: Optional[list[str]] = None


def role_to_resume_item_html(role: Role) -> str:
    # Matches your existing resume-item structure.
    h4 = role.title
    org = role.org or ""
    dates = role.dates or ""
    loc = role.location or ""

    parts: list[str] = ['<div class="resume-item">']
    parts.append(f"<h4>{escape_html(h4)}</h4>")
    if dates:
        parts.append(f"<h5>{escape_html(dates)}</h5>")
    if org or loc:
        em = escape_html(org)
        if loc:
            em = f"{em}, {escape_html(loc)}" if em else escape_html(loc)
        parts.append(f"<p><em>{em}</em></p>")
    if role.bullets:
        parts.append("<ul>")
        for b in role.bullets:
            parts.append(f"<li>{escape_html(b)}</li>")
        parts.append("</ul>")
    parts.append("</div>")
    return "\n".join(parts)


def escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&#39;")
    )


def load_content_stem(stem: str) -> tuple[str, str]:
    """
    Returns (kind, html) where kind in {"yaml", "md"}.
    Looks for content/<stem>.yaml|yml|md
    """
    candidates = [
        CONTENT_DIR / f"{stem}.yaml",
        CONTENT_DIR / f"{stem}.yml",
        CONTENT_DIR / f"{stem}.md",
    ]
    for p in candidates:
        if p.exists():
            if p.suffix in {".yaml", ".yml"}:
                return ("yaml", p.as_posix())
            return ("md", p.as_posix())
    die(f"Missing content file for '{stem}'. Expected one of: {[c.name for c in candidates]}")
    return ("", "")


def inject_markdown_list(soup, section_id: str, md_path: Path) -> None:
    section = soup.find(id=section_id)
    if section is None:
        return
    ul = section.find("ul")
    if ul is None:
        return
    ul.clear()
    md = read_text(md_path)
    html = md_to_html(md)

    # If markdown renders as <ul>...</ul>, take its <li> children.
    frag = BeautifulSoup(html, "html.parser")
    first_ul = frag.find("ul")
    if first_ul is not None:
        for li in list(first_ul.find_all("li", recursive=False)):
            ul.append(li)
    else:
        # otherwise insert as a single <li> block (keeps your structure intact)
        ul.append(BeautifulSoup(f"<li>{html}</li>", "html.parser"))


def inject_teaching_ul(soup, md_or_yaml_path: Path) -> None:
    """
    Your HTML has a Teaching block inside #resume in the right column.
    We replace that Teaching <ul> with either:
    - YAML list of strings (simple)
    - Markdown list
    """
    resume = soup.find(id="resume")
    if resume is None:
        return

    # Find the right column (the one with data-aos-delay="100") where teaching lives in your file.
    cols = resume.find_all("div", class_="col-lg-6")
    right_col = None
    for c in cols:
        if c.get("data-aos-delay") == "100":
            right_col = c
            break
    if right_col is None:
        return

    # Find the "Teaching" heading and the next <ul>.
    teaching_h3 = None
    for h3 in right_col.find_all("h3", class_="resume-title"):
        if (h3.get_text(strip=True) or "").lower() == "teaching":
            teaching_h3 = h3
            break
    if teaching_h3 is None:
        return

    ul = teaching_h3.find_next("ul")
    if ul is None:
        return

    ul.clear()

    if md_or_yaml_path.suffix in {".yaml", ".yml"}:
        data = read_yaml(md_or_yaml_path)
        if not isinstance(data, dict) or "items" not in data or not isinstance(data["items"], list):
            die("teaching YAML must be: {items: [..]}")
        for it in data["items"]:
            ul.append(BeautifulSoup(f"<li>{escape_html(str(it))}</li>", "html.parser"))
    else:
        md = read_text(md_or_yaml_path)
        html = md_to_html(md)
        frag = BeautifulSoup(html, "html.parser")
        first_ul = frag.find("ul")
        if first_ul is None:
            die("teaching.md should contain a bullet list (lines starting with '- ').")
        for li in list(first_ul.find_all("li", recursive=False)):
            ul.append(li)


def inject_professional_roles(soup, yaml_path: Path) -> None:
    """
    Replace the "Professional Experience" block items in the right column of #resume.
    Expects YAML: {roles: [{title, org, dates, location, bullets: [...]}, ...]}
    """
    resume = soup.find(id="resume")
    if resume is None:
        return

    cols = resume.find_all("div", class_="col-lg-6")
    right_col = None
    for c in cols:
        if c.get("data-aos-delay") == "100":
            right_col = c
            break
    if right_col is None:
        return

    prof_h3 = None
    for h3 in right_col.find_all("h3", class_="resume-title"):
        if (h3.get_text(strip=True) or "").lower() == "professional experience":
            prof_h3 = h3
            break
    if prof_h3 is None:
        return

    data = read_yaml(yaml_path)
    if not isinstance(data, dict) or "roles" not in data or not isinstance(data["roles"], list):
        die("professional YAML must be: {roles: [{title:..., ...}, ...]}")

    # Remove existing resume-item divs between this h3 and the next resume-title (Teaching)
    cursor = prof_h3.find_next_sibling()
    to_remove = []
    while cursor is not None:
        if getattr(cursor, "name", None) == "h3" and "resume-title" in (cursor.get("class") or []):
            break
        if getattr(cursor, "name", None) == "div" and "resume-item" in (cursor.get("class") or []):
            to_remove.append(cursor)
        cursor = cursor.find_next_sibling()

    for node in to_remove:
        node.decompose()

    # Insert new items right after the Professional Experience heading
    insert_after = prof_h3
    for r in data["roles"]:
        role = Role(
            title=str(r.get("title", "")).strip(),
            org=(str(r.get("org", "")).strip() or None),
            dates=(str(r.get("dates", "")).strip() or None),
            location=(str(r.get("location", "")).strip() or None),
            bullets=[str(b).strip() for b in (r.get("bullets") or [])] or None,
        )
        html = role_to_resume_item_html(role)
        new_node = BeautifulSoup(html, "html.parser")
        insert_after.insert_after(new_node)
        insert_after = new_node


def main() -> None:
    if BeautifulSoup is None:
        die("BeautifulSoup not installed. Run: pip install beautifulsoup4")

    index_in = ROOT / "index.html"
    if not index_in.exists():
        die(f"Cannot find {index_in}")

    if not CONTENT_DIR.exists():
        die(f"Missing {CONTENT_DIR}. Create it and add content files.")

    soup = BeautifulSoup(read_text(index_in), "html.parser")

    # professional (YAML roles)
    kind, path_str = load_content_stem("professional")
    if kind != "yaml":
        die("professional must be YAML (professional.yaml).")
    inject_professional_roles(soup, Path(path_str))

    # teaching (YAML items or Markdown list)
    kind, path_str = load_content_stem("teaching")
    inject_teaching_ul(soup, Path(path_str))

    # talks -> #news ul (your page labels this section "Recent Presentations")
    kind, path_str = load_content_stem("talks")
    if kind != "md":
        die("talks should be Markdown (talks.md).")
    inject_markdown_list(soup, "news", Path(path_str))

    # community -> #community ul
    kind, path_str = load_content_stem("community")
    if kind != "md":
        die("community should be Markdown (community.md).")
    inject_markdown_list(soup, "community", Path(path_str))

    # software -> optional #software ul (only if you add a section with id="software")
    soft_files = [CONTENT_DIR / "software.md", CONTENT_DIR / "software.yaml", CONTENT_DIR / "software.yml"]
    for p in soft_files:
        if p.exists():
            if soup.find(id="software") is not None:
                if p.suffix == ".md":
                    inject_markdown_list(soup, "software", p)
                else:
                    # simple YAML {items:[...]} -> <ul>
                    section = soup.find(id="software")
                    ul = section.find("ul") if section else None
                    if ul:
                        ul.clear()
                        data = read_yaml(p)
                        if not isinstance(data, dict) or "items" not in data:
                            die("software YAML must be: {items: [..]}")
                        for it in data["items"]:
                            ul.append(BeautifulSoup(f"<li>{escape_html(str(it))}</li>", "html.parser"))
            break

    out_path = OUTPUT_DIR / "index.built.html"
    out_path.write_text(str(soup), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
