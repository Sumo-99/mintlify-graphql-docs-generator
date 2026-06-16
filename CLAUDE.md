# GraphQL → Mintlify Docs Generator

Python CLI: GraphQL SDL schema (`.graphql`) → Mintlify docs project (`docs.json` + MDX per root operation).

## Stack
- Python ≥ 3.10
- `graphql-core` ≥ 3.2 (SDL parsing)
- Mintlify (output format)

## Project structure
Flat at repo root. No nested packages.

| Module | Purpose |
|--------|---------|
| `cli.py` | argparse entry (`gql-mintlify` command) |
| `parser.py` | SDL → `ParsedSchema` (root fields + type_map) |
| `type_render.py` | Recursive `ParamField`/`ResponseField`/`Expandable` MDX |
| `mdx_writer.py` | Assemble one MDX per field + write project |
| `docsjson.py` | Build `docs.json` navigation |
| `models.py` | `FieldInfo`, `ParsedSchema` dataclasses |
| `utils.py` | kebab-case slug, docstring fallback, array detection |

## Generation rules
- **Pages:** only `Query`, `Mutation`, `Subscription` root fields → one MDX file each
- **Supporting types:** objects, inputs, enums, scalars rendered inline as expandable blocks
- **Filename:** field name → kebab-case
- **Arguments:** `!` = required, else optional. Named types expanded recursively
- **Return types:** expanded recursively via `<Expandable>`. Cycle guard: visit set
- **Enums:** show allowed values inline
- **Navigation:** grouped by operation type in `docs.json`

## Development workflow

**Setup:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Generate from example schema:**
```bash
python cli.py examples/sample.graphql -o build_out --name "Sample API"
```

**Run tests:**
```bash
pytest
```

**Adding a feature:**
1. Identify which module(s): parsing (parser.py), rendering (type_render.py), output (mdx_writer.py, docsjson.py)
2. Update data models in models.py if new field info needed
3. Write test (golden-file MDX in tests/)
4. Run against real schema to verify

**Fixing a bug:**
1. Reproduce with pytest or real schema
2. Trace through parser → type_render → mdx_writer / docsjson pipeline
3. Check cycle guard logic in type_render.py if infinite recursion suspected
4. Test with pytest

## Common gotchas
- **Cycle detection:** `visited` set in type_render.py prevents infinite loops. Check it's threaded through all recursive calls.
- **Docstring handling:** empty strings (`""""""``) should produce no output — check `utils.docstring_or_fallback()`
- **Array detection:** `[Type]` notation in GraphQL → must mark in type display. See `is_array_type()` in utils.py
- **Slug generation:** field names → kebab-case, deterministic. Must match file output and nav entries.
- **MDX syntax:** ParamField, ResponseField, Expandable components. Verify exact nesting against Mintlify docs.

## Testing
Golden-file tests in `tests/`. Each test case writes MDX and compares against expected output.

To test against real schema:
```bash
gql-mintlify /path/to/your.graphql -o /tmp/test_out
cd /tmp/test_out && mint dev  # preview locally
```

## Entry point
`gql-mintlify` command maps to `cli:main()` (pyproject.toml). Accepts schema path, `-o` (output dir), `--name` (site name).

## Verify changes
Run pytest. If adding features, add golden-file test case.
