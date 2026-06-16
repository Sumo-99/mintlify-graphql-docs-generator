"""Task A: SDL parsing. graphql-core -> ParsedSchema.

Reads a GraphQL SDL file, builds the schema, and extracts each Query/Mutation/
Subscription root field into a FieldInfo. Supporting types are exposed via
ParsedSchema.type_map for downstream recursive rendering.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from graphql import build_schema

from models import FieldInfo, ParsedSchema

if TYPE_CHECKING:
    from graphql import GraphQLObjectType


def _extract_fields(
    root_type: "GraphQLObjectType | None", root_label: str
) -> list[FieldInfo]:
    """Turn one root object type's fields into ordered FieldInfo objects."""
    if root_type is None:
        return []

    fields: list[FieldInfo] = []
    for field_name, gql_field in root_type.fields.items():
        # GraphQLField.args is a dict[str, GraphQLArgument]; GraphQLArgument has
        # no own name, so we keep an index->name map alongside the ordered args.
        arg_items = list(gql_field.args.items())
        args = [arg for _, arg in arg_items]
        arg_names = {i: name for i, (name, _) in enumerate(arg_items)}

        fields.append(
            FieldInfo(
                name=field_name,
                docstring=gql_field.description or "",
                args=args,
                return_type=gql_field.type,
                root_type=root_label,
                arg_names=arg_names,
            )
        )
    return fields


def parse_schema(path: str) -> ParsedSchema:
    """Load an SDL file and extract root operation fields plus the full type_map.

    Args:
        path: Filesystem path to a `.graphql` SDL schema file.

    Returns:
        A ParsedSchema with queries/mutations/subscriptions as FieldInfo lists
        and type_map = schema.type_map (all named types).
    """
    sdl = Path(path).read_text(encoding="utf-8")
    schema = build_schema(sdl)

    return ParsedSchema(
        queries=_extract_fields(schema.query_type, "query"),
        mutations=_extract_fields(schema.mutation_type, "mutation"),
        subscriptions=_extract_fields(schema.subscription_type, "subscription"),
        type_map=schema.type_map,
    )
