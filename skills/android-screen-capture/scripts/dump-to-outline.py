#!/usr/bin/env python3
"""Turn a uiautomator XML dump into a readable outline of one screen.

The outline is what an agent reads instead of guessing from pixels: every visible
text, every resource-id, and which nodes are actually clickable, with their
position on screen. Run it with -I so nothing is imported from the dump's folder.

Usage:
    python3 -I dump-to-outline.py <screen>.uix [--format outline|markdown|json]
                                  [--max-depth N] [--include-invisible]

Output goes to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET

# Containers carry no information of their own; they are only shown when they
# are clickable or hold a resource-id worth naming.
NOISE_CLASSES = {
    "android.view.View",
    "android.view.ViewGroup",
    "android.widget.FrameLayout",
    "android.widget.LinearLayout",
    "android.widget.RelativeLayout",
    "androidx.constraintlayout.widget.ConstraintLayout",
    "androidx.compose.ui.platform.ComposeView",
}


def parse_bounds(value: str) -> tuple[int, int, int, int] | None:
    """'[0,84][1080,2217]' -> (0, 84, 1080, 2217)."""
    try:
        left, right = value.split("][")
        x1, y1 = left.lstrip("[").split(",")
        x2, y2 = right.rstrip("]").split(",")
        return int(x1), int(y1), int(x2), int(y2)
    except (ValueError, AttributeError):
        return None


def short_id(resource_id: str) -> str:
    """'com.example:id/btn_save' -> 'btn_save'; keeps anything unrecognised whole."""
    return resource_id.split("/", 1)[1] if "/" in resource_id else resource_id


def short_class(class_name: str) -> str:
    return class_name.rsplit(".", 1)[-1] if class_name else ""


def collect(node: ET.Element, depth: int, include_invisible: bool) -> dict | None:
    attrib = node.attrib
    bounds = parse_bounds(attrib.get("bounds", ""))
    width = bounds[2] - bounds[0] if bounds else 0
    height = bounds[3] - bounds[1] if bounds else 0

    visible = attrib.get("visible-to-user", "true") != "false" and width > 0 and height > 0
    text = (attrib.get("text") or "").strip()
    desc = (attrib.get("content-desc") or "").strip()
    rid = attrib.get("resource-id") or ""
    cls = attrib.get("class") or ""

    children = []
    for child in node:
        item = collect(child, depth + 1, include_invisible)
        if item:
            children.append(item)

    interactive = any(
        attrib.get(flag) == "true"
        for flag in ("clickable", "long-clickable", "checkable", "scrollable", "focusable")
    )
    editable = short_class(cls) in {"EditText", "AutoCompleteTextView", "SearchView"}
    informative = bool(text or desc or rid) or interactive or editable

    if not include_invisible and not visible:
        # An invisible container may still hold visible children (rare, but it
        # happens with overlays), so keep those rather than dropping the branch.
        return {"collapsed": True, "children": children} if children else None

    if not informative and short_class(cls) in {short_class(c) for c in NOISE_CLASSES}:
        return {"collapsed": True, "children": children} if children else None

    return {
        "collapsed": False,
        "class": short_class(cls),
        "full_class": cls,
        "id": short_id(rid) if rid else "",
        "resource_id": rid,
        "text": text,
        "content_desc": desc,
        "bounds": list(bounds) if bounds else None,
        "clickable": attrib.get("clickable") == "true",
        "long_clickable": attrib.get("long-clickable") == "true",
        "scrollable": attrib.get("scrollable") == "true",
        "checkable": attrib.get("checkable") == "true",
        "checked": attrib.get("checked") == "true",
        "enabled": attrib.get("enabled", "true") == "true",
        "focused": attrib.get("focused") == "true",
        "editable": editable,
        "package": attrib.get("package", ""),
        "children": children,
    }


def flatten(item: dict, depth: int = 0) -> list[tuple[int, dict]]:
    """Drop collapsed containers, lifting their children to the parent's depth."""
    out: list[tuple[int, dict]] = []
    if item.get("collapsed"):
        for child in item.get("children", []):
            out.extend(flatten(child, depth))
        return out
    out.append((depth, item))
    for child in item.get("children", []):
        out.extend(flatten(child, depth + 1))
    return out


def render_outline(rows: list[tuple[int, dict]]) -> str:
    lines = []
    for depth, node in rows:
        parts = [node["class"] or "?"]
        if node["id"]:
            parts.append(f"#{node['id']}")
        if node["text"]:
            parts.append(f'"{node["text"]}"')
        if node["content_desc"] and node["content_desc"] != node["text"]:
            parts.append(f'desc="{node["content_desc"]}"')
        flags = []
        if node["clickable"]:
            flags.append("click")
        if node["long_clickable"]:
            flags.append("long-click")
        if node["scrollable"]:
            flags.append("scroll")
        if node["editable"]:
            flags.append("input")
        if node["checkable"]:
            flags.append("checked" if node["checked"] else "unchecked")
        if not node["enabled"]:
            flags.append("disabled")
        if flags:
            parts.append("[" + " ".join(flags) + "]")
        if node["bounds"]:
            x1, y1, x2, y2 = node["bounds"]
            parts.append(f"@{x1},{y1}-{x2},{y2}")
        lines.append("  " * depth + " ".join(parts))
    return "\n".join(lines)


def render_markdown(rows: list[tuple[int, dict]], source: str) -> str:
    texts, actions, inputs, ids = [], [], [], []
    for _, node in rows:
        label = node["text"] or node["content_desc"]
        if node["text"]:
            texts.append(node["text"])
        if node["id"]:
            ids.append(node["id"])
        if node["editable"]:
            inputs.append((node["id"] or "(no id)", node["text"] or node["content_desc"] or ""))
        elif node["clickable"] and (label or node["id"]):
            actions.append((label or f"#{node['id']}", node["id"] or "(no id)"))

    def dedupe(seq):
        seen, out = set(), []
        for item in seq:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out

    chunks = [f"### Visible copy\n"]
    chunks.append(
        "\n".join(f"- {t}" for t in dedupe(texts)) if texts else "_No text nodes in the dump._"
    )
    chunks.append("\n\n### Actions (clickable)\n")
    if actions:
        chunks.append("| Label | resource-id |\n|---|---|\n")
        chunks.append("\n".join(f"| {a} | `{b}` |" for a, b in dedupe(actions)))
    else:
        chunks.append("_No clickable nodes._")
    chunks.append("\n\n### Inputs\n")
    if inputs:
        chunks.append("| resource-id | Current value |\n|---|---|\n")
        chunks.append("\n".join(f"| `{a}` | {b} |" for a, b in dedupe(inputs)))
    else:
        chunks.append("_No text inputs._")
    chunks.append(f"\n\n### View hierarchy\n\n```\n{render_outline(rows)}\n```\n")
    chunks.append(f"\n_Source: `{source}`_\n")
    return "".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump", help="path to a .uix / .xml uiautomator dump")
    parser.add_argument("--format", choices=("outline", "markdown", "json"), default="outline")
    parser.add_argument("--max-depth", type=int, default=0, help="0 = no limit")
    parser.add_argument("--include-invisible", action="store_true")
    args = parser.parse_args()

    try:
        tree = ET.parse(args.dump)
    except (OSError, ET.ParseError) as exc:
        print(f"cannot read {args.dump}: {exc}", file=sys.stderr)
        return 1

    root = collect(tree.getroot(), 0, args.include_invisible)
    if root is None:
        print("dump holds no visible nodes", file=sys.stderr)
        return 1

    rows = flatten(root)
    if args.max_depth:
        rows = [(d, n) for d, n in rows if d <= args.max_depth]

    if args.format == "json":
        print(json.dumps([n for _, n in rows], indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(render_markdown(rows, args.dump))
    else:
        print(render_outline(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
