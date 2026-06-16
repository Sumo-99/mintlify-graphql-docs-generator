"""Task D: build docs.json from ParsedSchema.

Mintlify docs.json schema reference (latest "mint" theme docs.json):
  - "$schema": "https://mintlify.com/docs.json"
  - "theme":   "mint"
  - "name":    site name (string)
  - "colors":  { "primary": "#hex" }
  - "navigation": { "groups": [ { "group": <label>, "pages": [<path str>, ...] } ] }
    * Each page entry is a path string to an MDX file relative to the docs root,
      WITHOUT the ".mdx" extension (e.g. "api-reference/get-product-by-id").
    * Groups with no pages are omitted entirely.

Slugs come from utils.kebab_case (owned by Task B).
"""

from __future__ import annotations

from models import ParsedSchema
from utils import kebab_case

#: Canonical Mintlify docs.json JSON-schema URL.
DOCS_JSON_SCHEMA = "https://mintlify.com/docs.json"

#: Mintlify theme used for the generated site (MVP default).
THEME = "mint"

#: Directory (relative to docs root) that holds the generated MDX pages.
API_REFERENCE_DIR = "api-reference"


def _page_path(field) -> str:
    """field name -> MDX page path used in navigation (no .mdx extension)."""
    return f"{API_REFERENCE_DIR}/{kebab_case(field.name)}"


def _group(label: str, fields) -> dict | None:
    """Build one nav group, or None when there are no fields to include."""
    if not fields:
        return None
    return {"group": label, "pages": [_page_path(f) for f in fields]}


def build_docs_json(
    schema: ParsedSchema,
    name: str = "API Reference",
    primary_color: str = "#16A34A",
) -> dict:
    """Build a Mintlify docs.json dict from a ParsedSchema.

    Navigation is split into "Queries", "Mutations", and "Subscriptions"
    groups (in that order). Any group with zero fields is omitted entirely.
    No api.mdx.server / playground block is emitted (MVP).
    """
    groups = []
    for label, fields in (
        ("Queries", schema.queries),
        ("Mutations", schema.mutations),
        ("Subscriptions", schema.subscriptions),
    ):
        group = _group(label, fields)
        if group is not None:
            groups.append(group)

    return {
        "$schema": DOCS_JSON_SCHEMA,
        "theme": THEME,
        "name": name,
        "colors": {"primary": primary_color},
        "navigation": {"groups": groups},
    }
