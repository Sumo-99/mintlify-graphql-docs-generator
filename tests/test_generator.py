"""End-to-end + unit tests for the GraphQL -> Mintlify generator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli import main
from docsjson import build_docs_json
from mdx_writer import render_mdx, write_project
from parser import parse_schema
from utils import kebab_case, title_for

SAMPLE = Path(__file__).parent.parent / "examples" / "sample.graphql"


@pytest.fixture
def parsed():
    return parse_schema(str(SAMPLE))


# --------------------------- utils --------------------------- #
@pytest.mark.parametrize(
    "name,expected",
    [
        ("getProductById", "get-product-by-id"),
        ("listProducts", "list-products"),
        ("HTTPServer", "http-server"),
        ("addToCart", "add-to-cart"),
    ],
)
def test_kebab_case(name, expected):
    assert kebab_case(name) == expected


def test_title_fallback():
    assert title_for("", "getCurrentUser") == "getCurrentUser"
    assert title_for("   ", "getCurrentUser") == "getCurrentUser"
    assert title_for("Fetch user", "getCurrentUser") == "Fetch user"


# --------------------------- parser -------------------------- #
def test_parse_counts(parsed):
    assert len(parsed.queries) == 5
    assert len(parsed.mutations) == 2
    assert len(parsed.subscriptions) == 1


def test_root_type_labels(parsed):
    assert {f.root_type for f in parsed.queries} == {"query"}
    assert {f.root_type for f in parsed.mutations} == {"mutation"}
    assert {f.root_type for f in parsed.subscriptions} == {"subscription"}


# --------------------------- mdx ----------------------------- #
def test_mdx_title_from_docstring(parsed):
    field = next(f for f in parsed.queries if f.name == "getProductById")
    mdx = render_mdx(field, parsed.type_map)
    assert 'title: "Fetch a single product by its unique ID."' in mdx
    assert "## Arguments" in mdx
    assert "## Response" in mdx
    assert "<ParamField" in mdx
    assert "<ResponseField" in mdx


def test_mdx_title_fallback_when_no_docstring(parsed):
    field = next(f for f in parsed.queries if f.name == "getCurrentUser")
    mdx = render_mdx(field, parsed.type_map)
    assert 'title: "getCurrentUser"' in mdx


def test_mdx_no_empty_description_lines(parsed):
    field = next(f for f in parsed.queries if f.name == "getCurrentUser")
    mdx = render_mdx(field, parsed.type_map)
    # No accidental blank-line-only description artifacts inside components.
    assert 'description: ""' not in mdx


def test_enum_values_inline(parsed):
    field = next(f for f in parsed.mutations if f.name == "createProduct")
    mdx = render_mdx(field, parsed.type_map)
    assert "ELECTRONICS" in mdx and "BOOKS" in mdx and "CLOTHING" in mdx


def test_array_marker(parsed):
    field = next(f for f in parsed.queries if f.name == "listProducts")
    mdx = render_mdx(field, parsed.type_map)
    assert "Product[]" in mdx


def test_interface_response_expands_fields_and_impls(parsed):
    field = next(f for f in parsed.queries if f.name == "node")
    mdx = render_mdx(field, parsed.type_map)
    # interface's own field
    assert '<ResponseField name="id"' in mdx
    # each concrete implementer rendered as its own variant
    assert '<Expandable title="Node">' in mdx
    assert '<Expandable title="Product (implementation)">' in mdx
    assert '<Expandable title="User (implementation)">' in mdx


def test_union_response_expands_members(parsed):
    field = next(f for f in parsed.queries if f.name == "search")
    mdx = render_mdx(field, parsed.type_map)
    assert "SearchResult[]" in mdx
    # one Expandable per union member, with member fields inside
    assert '<Expandable title="Product">' in mdx
    assert '<Expandable title="User">' in mdx
    assert '<ResponseField name="price"' in mdx  # Product field
    assert '<ResponseField name="cart"' in mdx  # User field


# --------------------------- docs.json ----------------------- #
def test_docs_json_groups(parsed):
    docs = build_docs_json(parsed, name="Sample")
    groups = {g["group"]: g for g in docs["navigation"]["groups"]}
    assert set(groups) == {"Queries", "Mutations", "Subscriptions"}
    assert docs["theme"] == "mint"
    assert docs["name"] == "Sample"
    assert "api-reference/get-product-by-id" in groups["Queries"]["pages"]


def test_docs_json_omits_empty_groups():
    from models import ParsedSchema

    ps = ParsedSchema(queries=[], mutations=[], subscriptions=[], type_map={})
    docs = build_docs_json(ps)
    assert docs["navigation"]["groups"] == []


# --------------------------- e2e ----------------------------- #
def test_write_project(parsed, tmp_path):
    write_project(parsed, str(tmp_path), name="Sample")
    assert (tmp_path / "docs.json").is_file()
    api = tmp_path / "api-reference"
    mdx_files = sorted(p.name for p in api.glob("*.mdx"))
    assert "get-product-by-id.mdx" in mdx_files
    assert len(mdx_files) == 8  # 5 q + 2 m + 1 s
    docs = json.loads((tmp_path / "docs.json").read_text())
    assert docs["$schema"] == "https://mintlify.com/docs.json"


def test_cli(tmp_path, capsys):
    out = tmp_path / "out"
    rc = main([str(SAMPLE), "-o", str(out), "--name", "CLI Test"])
    assert rc == 0
    assert (out / "docs.json").is_file()
    assert capsys.readouterr().out.strip().startswith("Generated 8 page(s)")


def test_cli_missing_file(tmp_path):
    rc = main([str(tmp_path / "nope.graphql")])
    assert rc == 1
