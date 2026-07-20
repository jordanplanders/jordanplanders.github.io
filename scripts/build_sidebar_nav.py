#!/usr/bin/env python3
"""Generate sidebar nav markup in the custom before-body includes from YAML config.

Two includes are generated from the same content/sidebar_nav.yml source:

- _includes/before-body.html        (index.qmd — the home page)
- _includes/before-body-inner.html  (every satellite/inner page)

The only structural difference is that "main" items with an anchor-only
href (e.g. "#about") are scrollable in-page links on the home page, but
need to point back at "index.html#about" when rendered on an inner page.
"satellite" items are already page-relative hrefs and render identically
in both variants.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "content" / "sidebar_nav.yml"
HOME_INCLUDE_PATH = ROOT / "_includes" / "before-body.html"
INNER_INCLUDE_PATH = ROOT / "_includes" / "before-body-inner.html"
START_MARKER = "<!-- NAV GENERATED START -->"
END_MARKER = "<!-- NAV GENERATED END -->"
INTROS_START_MARKER = "<!-- CATEGORY INTROS START -->"
INTROS_END_MARKER = "<!-- CATEGORY INTROS END -->"


class _UniqueKeyLoader(yaml.SafeLoader):
    """A YAML loader that rejects duplicate keys instead of silently
    letting the last one win.

    Plain YAML (and PyYAML's default loader) treats a repeated top-level
    key like a second 'satellite:' block as "overwrite the first one" —
    it parses without error but quietly discards everything under the
    first occurrence. That's an easy mistake to make when copy-pasting
    config blocks, and the failure mode (half your sidebar just isn't
    there) doesn't point back at the cause. Fail loudly here instead.
    """


def _construct_mapping_no_dupes(
    loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[str, Any]:
    seen: set[Any] = set()
    for key_node, _value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise ValueError(
                f"Duplicate key {key!r} at line {key_node.start_mark.line + 1} "
                f"of {CONFIG_PATH.name} — the first occurrence's value would "
                "be silently discarded. Merge the two blocks instead."
            )
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping_no_dupes
)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a YAML object at the top level.")
    return data


def icon_class(icon: str | None) -> str:
    if not icon:
        return "bx bx-link"
    return icon if icon.startswith("bx ") else f"bx {icon}"


def normalize_href(href: str, *, home: bool) -> str:
    """Resolve a configured href to a root-absolute URL.

    This site is served from the domain root (jordanplanders.github.io),
    and these nav includes are shared across pages at every depth in the
    source tree (index.qmd at root, science/*.qmd, software/*.qmd, ...).
    A page-relative href like "software.html" only resolves correctly
    from a page that is itself at the root, breaking anywhere else — so
    every internal link is rewritten to be root-absolute instead. This is
    what Quarto's native sidebar does for you automatically; since we're
    not using that here, we do it ourselves.
    """
    if href.startswith(("http://", "https://", "mailto:")):
        return href
    if href.startswith("#"):
        # In-page anchor. On the home page it's a local scroll target; on
        # every other page it points back at the section on the home page.
        return href if home else f"/index.html{href}"
    return href if href.startswith("/") else f"/{href}"


def render_link(item: dict[str, Any], *, home: bool) -> str:
    text = str(item.get("text", "")).strip()
    href = str(item.get("href", "")).strip()
    if not text or not href:
        raise ValueError(f"Link items require non-empty 'text' and 'href': {item}")

    href = normalize_href(href, home=home)

    classes = ["nav-link"]
    if bool(item.get("scrollto")) and home:
        classes.append("scrollto")
    if bool(item.get("active")) and home:
        classes.append("active")

    icon = icon_class(item.get("icon"))
    return (
        f'<li><a href="{escape(href)}" class="{" ".join(classes)}">'
        f'<i class="{escape(icon)}"></i> <span>{escape(text)}</span></a></li>'
    )


def _category_items(category: dict[str, Any]) -> list[Any]:
    items = category.get("items", category.get("links"))
    if not isinstance(items, list):
        raise ValueError(
            f"Category items require a list 'items' (or legacy 'links'): {category}"
        )
    return items


def render_category(category: dict[str, Any], *, home: bool) -> list[str]:
    """Render one collapsible category: a <details> dropdown, closed
    unless 'open: true' is set. Sections (the things with dividers)
    never collapse — only categories do, at any nesting depth. A
    category's own 'items' can themselves contain nested categories,
    rendered the same way one level deeper.
    """
    label = str(category.get("category", "")).strip()
    items = _category_items(category)
    if not label:
        raise ValueError(f"Category items require a non-empty 'category': {category}")

    icon = icon_class(category.get("icon") or "bx-folder")
    open_attr = " open" if bool(category.get("open")) else ""
    lines = [
        '<li class="nav-dropdown">',
        f"  <details{open_attr}>",
        f'    <summary><i class="{escape(icon)}"></i> <span>{escape(label)}</span></summary>',
        "    <ul>",
    ]
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"Category items must be objects: {item}")
        if "category" in item:
            lines.extend([f"    {line}" for line in render_category(item, home=home)])
        else:
            lines.append(f"      {render_link(item, home=home)}")
    lines.extend(["    </ul>", "  </details>", "</li>"])
    return lines


def render_group(group: dict[str, Any], *, home: bool) -> list[str]:
    """Render one sidebar section: a divider (its 'label'), then its
    'items' in order. Each item is either a plain link ({text, href,
    icon}) or a collapsible category ({category, icon, items: [...]}).

    An empty label (the normal case — dividers are usually unlabeled)
    renders no <li> at all, rather than an empty one. Emitting an
    empty-but-present label <li> still takes up a full line box's worth
    of vertical space even with no visible text, which is what made the
    gap above a section's first item so much bigger than the gap below
    its last one — the border/padding on the <ul> itself is the actual
    divider; the label <li> only needs to exist when there's a real
    label to show.
    """
    label = str(group.get("label", "")).strip()
    items = group.get("items")
    if not isinstance(items, list):
        raise ValueError(f"satellite entries require a list 'items': {group}")

    lines = []
    if label:
        lines.append(f'<li class="nav-section-label"><span>{escape(label)}</span></li>')
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"Section items must be objects: {item}")
        if "category" in item:
            lines.extend(render_category(item, home=home))
        else:
            lines.append(render_link(item, home=home))
    return lines


def collect_category_intros(
    satellite_groups: list[Any],
) -> dict[str, list[dict[str, str]]]:
    """Walk every section's items (recursively through nested
    categories) and build a map of page href -> ordered list of
    {label, blurb, image?} entries, from the outermost ancestor
    category down to the innermost.

    Categories without a 'blurb' or 'image' contribute nothing to the
    list but are still walked, so a page nested under an unlabeled
    wrapper category still picks up blurbs/images from categories
    further out. A page reached without ever passing through a
    category with a blurb or image gets no entry at all.

    'image' is optional and independent of 'blurb' — a category can set
    either, both, or neither. Its value is a path exactly like a link
    'href' (project-relative, e.g. "favorite_figures/.../thumb.jpg"),
    normalized to root-absolute the same way link hrefs are, since the
    same intro card can render on pages at any depth in the source
    tree.
    """
    intros: dict[str, list[dict[str, str]]] = {}

    def walk(items: list[Any], ancestors: list[dict[str, str]]) -> None:
        for item in items:
            if not isinstance(item, dict):
                continue
            if "category" in item:
                blurb = item.get("blurb")
                image = item.get("image")
                label = str(item.get("category", "")).strip()
                if blurb or image:
                    entry: dict[str, str] = {"label": label}
                    if blurb:
                        entry["blurb"] = str(blurb).strip()
                    if image:
                        entry["image"] = normalize_href(str(image).strip(), home=True)
                    next_ancestors = ancestors + [entry]
                else:
                    next_ancestors = ancestors
                walk(_category_items(item), next_ancestors)
            else:
                href = str(item.get("href", "")).strip()
                if href and ancestors:
                    # home=True/False only matters for anchor-only hrefs
                    # ("#about"); category links are always real pages.
                    intros[normalize_href(href, home=True)] = list(ancestors)

    for group in satellite_groups:
        if isinstance(group, dict):
            walk(group.get("items", []), [])

    return intros


def render_category_intros_script(config: dict[str, Any]) -> str:
    satellite_groups = config.get("satellite", [])
    intros = collect_category_intros(
        satellite_groups if isinstance(satellite_groups, list) else []
    )
    payload = json.dumps(intros, ensure_ascii=False, separators=(",", ":"))
    # A blurb containing the literal substring "</script" would end the
    # tag early no matter what the script's type is — the HTML parser
    # scans for it textually. Escape the slash so that can't happen.
    payload = payload.replace("</", "<\\/")
    return f'<script type="application/json" id="category-intros">{payload}</script>'


def render_nav(config: dict[str, Any], *, home: bool) -> str:
    main_items = config.get("main", [])
    satellite_groups = config.get("satellite", [])

    if not isinstance(main_items, list) or not isinstance(satellite_groups, list):
        raise ValueError("'main' and 'satellite' must be YAML lists.")

    lines: list[str] = []
    lines.append("      <ul>")
    for item in main_items:
        if not isinstance(item, dict):
            raise ValueError(f"main items must be objects: {item}")
        lines.append(f"        {render_link(item, home=home)}")
    lines.append("      </ul>")

    # Each entry under 'satellite' is one sidebar section: a divider
    # (its 'label', can be '') followed by its own <ul> of items. One
    # divider per entry, in the order they're written — that's the whole
    # mechanism for controlling where dividers land. Sections themselves
    # never collapse; an item within a section can opt into collapsing
    # by being a 'category' instead of a plain link.
    for group in satellite_groups:
        if not isinstance(group, dict):
            raise ValueError(f"satellite entries must be objects: {group}")
        lines.append("      <ul>")
        for line in render_group(group, home=home):
            lines.append(f"        {line}")
        lines.append("      </ul>")

    return "\n".join(lines)


def replace_marked_block(
    raw: str,
    replacement: str,
    include_path: Path,
    *,
    start_marker: str = START_MARKER,
    end_marker: str = END_MARKER,
    indent: str = "\n    ",
) -> str:
    start = raw.find(start_marker)
    end = raw.find(end_marker)
    if start == -1 or end == -1 or end < start:
        raise ValueError(
            f"Could not find markers in {include_path}: "
            f"{start_marker} ... {end_marker}"
        )
    start_content = start + len(start_marker)
    return raw[:start_content] + "\n" + replacement + indent + raw[end:]


def write_variant(config: dict[str, Any], include_path: Path, *, home: bool) -> None:
    raw = include_path.read_text(encoding="utf-8")
    raw = replace_marked_block(raw, render_nav(config, home=home), include_path)
    raw = replace_marked_block(
        raw,
        render_category_intros_script(config),
        include_path,
        start_marker=INTROS_START_MARKER,
        end_marker=INTROS_END_MARKER,
        indent="\n",
    )
    include_path.write_text(raw, encoding="utf-8")
    print(f"Updated {include_path.relative_to(ROOT)} from {CONFIG_PATH.relative_to(ROOT)}")


def main() -> None:
    config = load_yaml(CONFIG_PATH)
    write_variant(config, HOME_INCLUDE_PATH, home=True)
    write_variant(config, INNER_INCLUDE_PATH, home=False)


if __name__ == "__main__":
    main()
