"""Shared data contracts. Defined in Task 0; consumed by all other tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graphql import GraphQLArgument, GraphQLNamedType, GraphQLType


@dataclass
class FieldInfo:
    """One root operation field -> one MDX page."""

    name: str
    """GraphQL field name, e.g. 'getProductById'."""

    docstring: str
    """Field description from SDL. Empty string if none."""

    args: list["GraphQLArgument"]
    """Ordered argument objects (graphql-core), name carried via .arg_name."""

    return_type: "GraphQLType"
    """Raw return type (may be NonNull/List wrapped)."""

    root_type: str
    """One of: 'query', 'mutation', 'subscription'."""

    arg_names: dict[int, str] = field(default_factory=dict)
    """Index -> arg name, since GraphQLArgument has no own name."""


@dataclass
class ParsedSchema:
    queries: list[FieldInfo]
    mutations: list[FieldInfo]
    subscriptions: list[FieldInfo]
    type_map: dict[str, "GraphQLNamedType"]
