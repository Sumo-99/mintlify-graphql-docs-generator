"""Task C: argparse entry point.

    gql-mintlify <schema.graphql> -o <out_dir> [--name "My API"]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mdx_writer import write_project
from parser import parse_schema


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="gql-mintlify",
        description="Generate a Mintlify docs project from a GraphQL SDL schema.",
    )
    ap.add_argument("schema", help="path to a .graphql SDL schema file")
    ap.add_argument(
        "-o", "--out", default="docs", help="output directory (default: docs)"
    )
    ap.add_argument(
        "--name", default="API Reference", help="docs.json site name"
    )
    args = ap.parse_args(argv)

    schema_path = Path(args.schema)
    if not schema_path.is_file():
        print(f"error: schema file not found: {schema_path}", file=sys.stderr)
        return 1

    parsed = parse_schema(str(schema_path))
    write_project(parsed, args.out, name=args.name)

    n = len(parsed.queries) + len(parsed.mutations) + len(parsed.subscriptions)
    print(f"Generated {n} page(s) -> {args.out}/  (run `mint dev` inside it)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
