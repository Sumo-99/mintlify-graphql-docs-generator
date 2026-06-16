# GraphQL → Mintlify Docs Generator — Build Plan

Python CLI: input a GraphQL SDL `.graphql` file → output a ready-to-run Mintlify
docs project (`docs.json` + `api-reference/` MDX, one file per root operation).
Serve with `mint dev`.

**Stack:** Python, `graphql-core` for SDL parsing.

## Inputs / Outputs
- **Input:** path to a `.graphql` SDL schema file.
- **Output:** a folder containing:
  - `docs.json`
  - `api-reference/` — one MDX file per Query/Mutation/Subscription field.

## Generation rules (authoritative)
- Only `Query`, `Mutation`, `Subscription` fields generate pages. All other
  types (objects, inputs, enums, scalars) are supporting material rendered inline.
- Each root field → one MDX file + one nav entry.
- **Filename slug:** field name → kebab-case (`getProductById` → `get-product-by-id.mdx`). Deterministic.
- **Page title:** field docstring; fall back to field name if empty/blank.
- **Operation badge label:** root type → `query` / `mutation` / `subscription`.
- **Arguments → `<ParamField>`:** `!` = required, no `!` = optional. Scalars shown
  as-is. Named input types expanded recursively into nested `<ParamField>`.
- **Return type → `<ResponseField>`:** named types expanded recursively using
  `<Expandable>`. Track visited types in a set to break cycles. Unlimited depth
  otherwise.
- **Empty docstring `""""""`:** skip description silently — render no blank lines.
- **`[Type]`:** mark as array in the field's type display.
- **Enums:** render allowed values inline. Pull arg/field descriptions from
  GraphQL `description` where present.

## docs.json
Standard Mintlify config: `theme`, `name`, `colors.primary`, and `navigation`
groups split by operation type (`Queries`, `Mutations`, `Subscriptions`).
No `api.mdx.server` / playground block for MVP.

## Example MDX structure
```mdx
---
title: "Field docstring or field name"
description: "optional second line"
---

## Arguments
<ParamField ...>
...
</ParamField>

## Response
<ResponseField ...>
  <Expandable ...>
  ...
  </Expandable>
</ResponseField>
```
NOTE: example files in `../mintlify-testing/` use the OpenAPI shortcut
(`openapi: get /products`). Our GraphQL output is different — we hand-write the
full `<ParamField>`/`<ResponseField>` components.

## Package layout (flat — modules at repo root)
```
cli.py            # argparse entry: input .graphql, output dir
parser.py         # graphql-core: SDL -> schema, extract root fields + type_map
type_render.py    # recursive type expansion -> ParamField/ResponseField MDX
mdx_writer.py     # assemble one MDX per field + write_project
docsjson.py       # build docs.json nav grouped by op type
utils.py          # kebab-case slug, docstring fallback, array detection
models.py         # FieldInfo, ParsedSchema data contracts
pyproject.toml    # py-modules flat layout; entry point: gql-mintlify = cli:main
tests/
examples/sample.graphql
```

## Shared data contracts (define in Task 0, before fan-out)
- `parser.parse_schema(path) -> ParsedSchema`
  - `ParsedSchema`: `queries: list[FieldInfo]`, `mutations: list[FieldInfo]`,
    `subscriptions: list[FieldInfo]`, `type_map: dict[str, GraphQLType]`
- `FieldInfo`: `name`, `docstring`, `args`, `return_type`, `root_type`
- `type_render` fns: `(gql_type, type_map, visited: set[str]) -> str` (MDX block)
- slug = field name kebab-case

## Task split (parallel after Task 0)
| # | Task | Files | Depends |
|---|------|-------|---------|
| 0 | Scaffold: pyproject, package skeleton, FieldInfo dataclasses, stub signatures | pyproject, `__init__`, dataclasses | none — do first |
| A | SDL parser: load schema, extract root fields + type_map | parser.py | 0 |
| B | Type renderer: recursive ParamField/ResponseField/Expandable, enums, array, cycle guard | type_render.py, utils.py | 0 (mock FieldInfo) |
| C | MDX writer + CLI wiring | mdx_writer.py, cli.py | A, B |
| D | docs.json builder | docsjson.py | 0 |
| E | Tests + examples/sample.graphql (golden-file MDX) | tests/, examples/ | A, B, C, D |

A, B, D run fully parallel after 0. C joins when A+B done. E validates at end.

## Agent rules
- Every subagent MUST use the **context7 MCP** (`resolve-library-id` →
  `query-docs`) to fetch latest docs for `graphql-core` and Mintlify component
  syntax (`ParamField`, `ResponseField`, `Expandable`, `docs.json` schema)
  before/while implementing. Do not rely on memory for library APIs.
- Each agent ends its task by self-verifying with explanatory output (run the
  code / print results) and returns a short report of what it built + verification.

