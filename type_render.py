"""Task B: recursive GraphQL type -> Mintlify MDX component strings.

Mintlify components used (props per Mintlify docs):
  - <ParamField>:    body="<name>" | query | path | header, type="...",
                     required (boolean attr), deprecated. Description is the
                     child text/markdown between the tags.
  - <ResponseField>: name="<name>" type="..." required (boolean attr).
                     Description is child text/markdown.
  - <Expandable title="...">: collapsible group wrapping nested
                     <ParamField>/<ResponseField> children.

graphql-core introspection (v3.2): wrapper types GraphQLNonNull / GraphQLList
expose `.of_type`; named types are unwrapped via graphql.get_named_type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from graphql import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    get_named_type,
)

if TYPE_CHECKING:
    from graphql import GraphQLArgument, GraphQLNamedType, GraphQLType

_INDENT = "  "


# --------------------------------------------------------------------------- #
# Type-wrapper analysis
# --------------------------------------------------------------------------- #
def _unwrap(gql_type: "GraphQLType") -> tuple["GraphQLNamedType", bool, bool]:
    """Peel NonNull / List wrappers.

    Returns (named_type, required, is_list). `required` reflects an outer
    NonNull (whether the value itself must be supplied). `is_list` is True if
    a List wrapper appears anywhere in the chain.
    """
    required = False
    is_list = False
    t = gql_type
    if isinstance(t, GraphQLNonNull):
        required = True
        t = t.of_type
    while isinstance(t, (GraphQLList, GraphQLNonNull)):
        if isinstance(t, GraphQLList):
            is_list = True
        t = t.of_type
    return t, required, is_list


def _type_display(gql_type: "GraphQLType") -> str:
    """Human-facing type string, e.g. 'String', 'Product[]', 'Color'."""
    named, _required, is_list = _unwrap(gql_type)
    name = named.name
    return f"{name}[]" if is_list else name


def _required_attr(required: bool) -> str:
    return " required" if required else ""


def _enum_description(base: str, enum: GraphQLEnumType) -> str:
    """Append the inline list of allowed enum values to a description."""
    values = ", ".join(f"`{name}`" for name in enum.values)
    line = f"Allowed values: {values}"
    return f"{base}\n\n{line}" if base else line


def _block(open_tag: str, body: str, close_tag: str, indent: str) -> str:
    """Render an element. `body` may be empty (-> no inner lines)."""
    if body:
        inner = "\n".join(indent + _INDENT + ln for ln in body.splitlines())
        return f"{indent}{open_tag}\n{inner}\n{indent}{close_tag}"
    return f"{indent}{open_tag}\n{indent}{close_tag}"


# --------------------------------------------------------------------------- #
# Arguments  ->  <ParamField>
# --------------------------------------------------------------------------- #
def render_arguments(
    args: list["GraphQLArgument"],
    arg_names: dict[int, str],
    type_map: dict[str, "GraphQLNamedType"],
) -> str:
    """Render all args as <ParamField> blocks (input types expand recursively)."""
    blocks: list[str] = []
    for i, arg in enumerate(args):
        name = arg_names.get(i, f"arg{i}")
        blocks.append(
            _render_param_field(
                name=name,
                gql_type=arg.type,
                description=getattr(arg, "description", None),
                type_map=type_map,
                indent="",
                visited=set(),
            )
        )
    return "\n".join(blocks)


def _render_param_field(
    name: str,
    gql_type: "GraphQLType",
    description: str | None,
    type_map: dict[str, "GraphQLNamedType"],
    indent: str,
    visited: set[str],
) -> str:
    named, required, _is_list = _unwrap(gql_type)
    desc = (description or "").strip()

    if isinstance(named, GraphQLEnumType):
        desc = _enum_description(desc, named)

    open_tag = (
        f'<ParamField body="{name}" type="{_type_display(gql_type)}"'
        f"{_required_attr(required)}>"
    )

    inner_parts: list[str] = []
    if desc:
        inner_parts.append(desc)

    # Expand named INPUT object types into nested <ParamField> children.
    if isinstance(named, GraphQLInputObjectType) and named.name not in visited:
        child_visited = visited | {named.name}
        child_blocks = [
            _render_param_field(
                name=fname,
                gql_type=fdef.type,
                description=getattr(fdef, "description", None),
                type_map=type_map,
                indent="",
                visited=child_visited,
            )
            for fname, fdef in named.fields.items()
        ]
        inner_parts.append(
            _block(
                f'<Expandable title="{named.name}">',
                "\n".join(child_blocks),
                "</Expandable>",
                "",
            )
        )

    body = "\n".join(inner_parts)
    return _block(open_tag, body, "</ParamField>", indent)


# --------------------------------------------------------------------------- #
# Response  ->  <ResponseField> / <Expandable>
# --------------------------------------------------------------------------- #
def render_response(
    return_type: "GraphQLType",
    type_map: dict[str, "GraphQLNamedType"],
    visited: set[str] | None = None,
) -> str:
    """Render a return type as <ResponseField>, expanding object types via
    <Expandable>. Cycles are broken by tracking visited type names."""
    if visited is None:
        visited = set()
    named, required, _is_list = _unwrap(return_type)
    return _render_response_field(
        name="response",
        gql_type=return_type,
        description=getattr(named, "description", None),
        type_map=type_map,
        indent="",
        visited=visited,
    )


def _render_response_field(
    name: str,
    gql_type: "GraphQLType",
    description: str | None,
    type_map: dict[str, "GraphQLNamedType"],
    indent: str,
    visited: set[str],
) -> str:
    named, required, _is_list = _unwrap(gql_type)
    desc = (description or "").strip()

    if isinstance(named, GraphQLEnumType):
        desc = _enum_description(desc, named)

    open_tag = (
        f'<ResponseField name="{name}" type="{_type_display(gql_type)}"'
        f"{_required_attr(required)}>"
    )

    inner_parts: list[str] = []
    if desc:
        inner_parts.append(desc)

    # Expand object output types recursively, guarding against cycles.
    if isinstance(named, GraphQLObjectType) and named.name not in visited:
        child_visited = visited | {named.name}
        child_blocks = [
            _render_response_field(
                name=fname,
                gql_type=fdef.type,
                description=getattr(fdef, "description", None),
                type_map=type_map,
                indent="",
                visited=child_visited,
            )
            for fname, fdef in named.fields.items()
        ]
        inner_parts.append(
            _block(
                f'<Expandable title="{named.name}">',
                "\n".join(child_blocks),
                "</Expandable>",
                "",
            )
        )

    body = "\n".join(inner_parts)
    return _block(open_tag, body, "</ResponseField>", indent)
