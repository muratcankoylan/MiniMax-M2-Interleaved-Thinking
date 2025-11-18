"""Demo tool implementations backed by sample project artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


SAMPLE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "claude_minimax"
    / "examples"
    / "sample_project"
)


def _load_markdown_sections(file_path: Path) -> Dict[str, str]:
    """Split a markdown file into sections keyed by h2 headings."""
    content = file_path.read_text(encoding="utf-8")
    sections: Dict[str, List[str]] = {}
    current_key = "introduction"
    sections[current_key] = []

    for line in content.splitlines():
        if line.startswith("## "):
            current_key = line[3:].strip().lower()
            sections[current_key] = []
        else:
            sections.setdefault(current_key, []).append(line)

    return {
        key: "\n".join(value).strip()
        for key, value in sections.items()
        if value
    }


def get_design_tokens(category: str) -> str:
    """
    Return relevant tokens from design_system.md.

    Parameters
    ----------
    category: Literal describing which block to fetch
        Supported: colors, typography, spacing, shadows, border radius, breakpoints
    """
    data = _load_markdown_sections(SAMPLE_ROOT / "design_system.md")
    normalized = category.lower()
    for key, value in data.items():
        if normalized in key:
            return json.dumps(
                {
                    "section": key,
                    "tokens": value[:1200],
                }
            )
    return json.dumps(
        {
            "section": "not_found",
            "tokens": f"No section matched '{category}'. Available: {list(data.keys())}",
        }
    )


def get_component_spec(component: str) -> str:
    """
    Return component spec from component_specs.md.

    component: Component name such as Button, Card, Input, Modal, Alert.
    """
    raw = (SAMPLE_ROOT / "component_specs.md").read_text(encoding="utf-8")
    normalized = component.strip().lower()
    blocks = raw.split("## ")
    for block in blocks:
        header, *body = block.splitlines()
        if not header:
            continue
        if header.strip().lower().startswith(normalized):
            snippet = "\n".join(body).strip()
            return json.dumps({"component": header.strip(), "spec": snippet[:1600]})
    return json.dumps({"component": component, "spec": "Component not found in specs document."})


def get_pattern_guidance(topic: str) -> str:
    """Return guidance from code_patterns.md for the requested topic."""
    sections = _load_markdown_sections(SAMPLE_ROOT / "code_patterns.md")
    normalized = topic.lower()
    for key, value in sections.items():
        if normalized in key or normalized in value.lower():
            return json.dumps({"topic": key, "guidance": value[:1600]})
    return json.dumps({"topic": topic, "guidance": "No matching pattern found."})


TOOL_REGISTRY = {
    "get_design_tokens": get_design_tokens,
    "get_component_spec": get_component_spec,
    "get_pattern_guidance": get_pattern_guidance,
}


