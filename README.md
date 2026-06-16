# GraphQL → Mintlify Docs Generator

A Python CLI that turns a GraphQL SDL schema (`.graphql`) into a ready-to-run
[Mintlify](https://mintlify.com) docs project: a `docs.json` config plus one MDX
page per root operation, served with `mint dev`.

Only `Query`, `Mutation`, and `Subscription` fields become pages. Every other
type (objects, inputs, enums, scalars) is rendered inline as supporting material
inside the operation pages.

## How it works

- **One page per root field.** Each Query/Mutation/Subscription field →
  one MDX file + one navigation entry.
- **Deterministic slugs.** Field name → kebab-case
  (`getProductById` → `get-product-by-id.mdx`).
- **Arguments → `<ParamField>`.** `!` = required, otherwise optional. Named
  input types are expanded recursively into nested `<ParamField>` blocks.
- **Return types → `<ResponseField>`.** Named types expanded recursively via
  `<Expandable>`, with a visited-set cycle guard (unlimited depth otherwise).
- **Enums** render their allowed values inline; descriptions are pulled from the
  GraphQL `description` where present.
- **Navigation** in `docs.json` is split into `Queries`, `Mutations`, and
  `Subscriptions` groups (empty groups omitted).

## Requirements

- Python ≥ 3.10
- [`graphql-core`](https://pypi.org/project/graphql-core/) ≥ 3.2 (installed
  automatically below)
- [Mintlify CLI](https://www.npmjs.com/package/mint) (`mint`) — optional, only
  needed to preview the generated docs locally.

## Setup

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .                   # installs deps + the `gql-mintlify` command
```

To also install dev/test dependencies:

```bash
pip install -e ".[dev]"
```

## Usage

```
gql-mintlify <schema.graphql> [-o OUT_DIR] [--name "Site Name"]
```

| Flag           | Default         | Description                          |
|----------------|-----------------|--------------------------------------|
| `schema`       | *(required)*    | Path to a `.graphql` SDL schema file |
| `-o`, `--out`  | `docs`          | Output directory                     |
| `--name`       | `API Reference` | `docs.json` site name                |

Generate docs from the bundled example schema:

```bash
gql-mintlify examples/sample.graphql -o build_out --name "Sample API"
```

Output:

```
Generated 6 page(s) -> build_out/  (run `mint dev` inside it)
```

You can also run it without installing, straight from the source tree:

```bash
python cli.py examples/sample.graphql -o build_out --name "Sample API"
```

## Output layout

```
build_out/
├── docs.json                       # Mintlify config + navigation
└── api-reference/
    ├── get-product-by-id.mdx
    ├── list-products.mdx
    ├── get-current-user.mdx
    ├── create-product.mdx
    ├── add-to-cart.mdx
    └── product-price-changed.mdx
```

## Preview the docs

With the [Mintlify CLI](https://www.npmjs.com/package/mint) installed:

```bash
cd build_out
mint dev
```

Then open the local URL it prints (default <http://localhost:3000>).

## Project structure

Flat layout — modules live at the repo root.

| File             | Responsibility                                                        |
|------------------|-----------------------------------------------------------------------|
| `cli.py`         | argparse entry point (`gql-mintlify = cli:main`)                      |
| `parser.py`      | `graphql-core` SDL → `ParsedSchema` (root fields + type map)         |
| `type_render.py` | Recursive `ParamField` / `ResponseField` / `Expandable` rendering    |
| `mdx_writer.py`  | Assemble one MDX per field + `write_project`                         |
| `docsjson.py`    | Build `docs.json` navigation grouped by operation type               |
| `models.py`      | `FieldInfo`, `ParsedSchema` data contracts                           |
| `utils.py`       | kebab-case slug, docstring fallback, array detection                 |
| `examples/`      | `sample.graphql` reference schema                                    |
| `tests/`         | pytest suite (golden-file MDX)                                       |

## Tests

```bash
pip install -e ".[dev]"
pytest
```
