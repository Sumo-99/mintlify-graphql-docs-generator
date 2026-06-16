"""Task C: assemble one MDX file per FieldInfo and write the project tree.

Output layout (Mintlify, `mint dev`-ready):
    <out_dir>/
      docs.json
      api-reference/<kebab-field-name>.mdx   (one per root field)
"""

from __future__ import annotations

import json
from pathlib import Path

from docsjson import build_docs_json
from models import FieldInfo, ParsedSchema
from type_render import render_arguments, render_response
from utils import kebab_case, title_for

#: Badge label per root type, used as the page subtitle/description fallback.
_BADGE = {"query": "query", "mutation": "mutation", "subscription": "subscription"}


def _frontmatter(field: FieldInfo) -> str:
    """YAML frontmatter. Title from docstring (fallback field name); the
    operation badge label is carried as the description line."""
    title = title_for(field.docstring, field.name).replace('"', '\\"')
    badge = _BADGE.get(field.root_type, field.root_type)
    lines = ["---", f'title: "{title}"', f'description: "{badge}"', "---"]
    return "\n".join(lines)


def render_mdx(field: FieldInfo, type_map: dict) -> str:
    """Full MDX string: frontmatter + Arguments + Response sections.

    Sections with no content are omitted entirely (no empty headings).
    """
    parts = [_frontmatter(field)]

    args_block = render_arguments(field.args, field.arg_names, type_map)
    if args_block.strip():
        parts.append("## Arguments\n\n" + args_block)

    response_block = render_response(field.return_type, type_map)
    if response_block.strip():
        parts.append("## Response\n\n" + response_block)

    return "\n\n".join(parts) + "\n"


def write_project(schema: ParsedSchema, out_dir: str, name: str = "API Reference") -> None:
    """Write api-reference/*.mdx + docs.json into out_dir."""
    out = Path(out_dir)
    api_ref = out / "api-reference"
    api_ref.mkdir(parents=True, exist_ok=True)

    all_fields = schema.queries + schema.mutations + schema.subscriptions
    for field in all_fields:
        slug = kebab_case(field.name)
        (api_ref / f"{slug}.mdx").write_text(
            render_mdx(field, schema.type_map), encoding="utf-8"
        )

    docs = build_docs_json(schema, name=name)
    (out / "docs.json").write_text(json.dumps(docs, indent=2) + "\n", encoding="utf-8")
