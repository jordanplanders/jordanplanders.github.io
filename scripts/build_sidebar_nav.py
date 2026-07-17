#!/usr/bin/env python3
"""Generate sidebar nav markup in _includes/before-body.html from YAML config."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "content" / "sidebar_nav.yml"
INCLUDE_PATH = ROOT / "_includes" / "before-body.html"
START_MARKER = "<!-- NAV GENERATED START -->"
END_MARKER = "<!-- NAV GENERATED END -->"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a YAML object at the top level.")
    return data


def icon_class(icon: str | None) -> str:
    if not icon:
        return "bx bx-link"
    return icon if icon.startswith("bx ") else f"bx {icon}"


def render_link(item: dict[str, Any]) -> str:
    text = str(item.get("text", "")).strip()
    href = str(item.get("href", "")).strip()
    if not text or not href:
        raise ValueError(f"Link items require non-empty 'text' and 'href': {item}")

    classes = ["nav-link"]
    if bool(item.get("scrollto")):
        classes.append("scrollto")
    if bool(item.get("active")):
        classes.append("active")

    icon = icon_class(item.get("icon"))
    return (
        f'<li><a href="{escape(href)}" class="{" ".join(classes)}">'
        f'<i class="{escape(icon)}"></i> <span>{escape(text)}</span></a></li>'
    )


def render_dropdown(section_item: dict[str, Any]) -> list[str]:
    title = str(section_item.get("section", "")).strip()
    links = section_item.get("links")
    if not title or not isinstance(links, list):
        raise ValueError(
            "Dropdown items require 'section' and list 'links': "
            f"{section_item}"
        )

    icon = icon_class(section_item.get("icon") or "bx-folder")
    lines = [
        '<li class="nav-dropdown">',
        "  <details>",
        f'    <summary><i class="{escape(icon)}"></i> <span>{escape(title)}</span></summary>',
        "    <ul>",
    ]
    for link in links:
        if not isinstance(link, dict):
            raise ValueError(f"Dropdown link items must be objects: {link}")
        lines.append(f"      {render_link(link)}")
    lines.extend(["    </ul>", "  </details>", "</li>"])
    return lines


def render_nav(config: dict[str, Any]) -> str:
    main_items = config.get("main", [])
    satellite_items = config.get("satellite", [])
    satellite_label = str(config.get("satellite_label", "Satellite Pages")).strip()

    if not isinstance(main_items, list) or not isinstance(satellite_items, list):
        raise ValueError("'main' and 'satellite' must be YAML lists.")

    lines: list[str] = []
    lines.append("      <ul>")
    for item in main_items:
        if not isinstance(item, dict):
            raise ValueError(f"main items must be objects: {item}")
        lines.append(f"        {render_link(item)}")
    lines.append("      </ul>")
    lines.append("      <ul>")
    lines.append(
        f'        <li class="nav-section-label"><span>{escape(satellite_label)}</span></li>'
    )
    for item in satellite_items:
        if not isinstance(item, dict):
            raise ValueError(f"satellite items must be objects: {item}")
        if "section" in item:
            lines.extend([f"        {line}" for line in render_dropdown(item)])
        else:
            lines.append(f"        {render_link(item)}")
    lines.append("      </ul>")
    return "\n".join(lines)


def replace_marked_block(raw: str, replacement: str) -> str:
    start = raw.find(START_MARKER)
    end = raw.find(END_MARKER)
    if start == -1 or end == -1 or end < start:
        raise ValueError(
            f"Could not find markers in {INCLUDE_PATH}: "
            f"{START_MARKER} ... {END_MARKER}"
        )
    start_content = start + len(START_MARKER)
    return raw[:start_content] + "\n" + replacement + "\n    " + raw[end:]


def main() -> None:
    config = load_yaml(CONFIG_PATH)
    rendered = render_nav(config)
    before_body = INCLUDE_PATH.read_text(encoding="utf-8")
    updated = replace_marked_block(before_body, rendered)
    INCLUDE_PATH.write_text(updated, encoding="utf-8")
    print(f"Updated {INCLUDE_PATH} from {CONFIG_PATH}")


if __name__ == "__main__":
    main()
