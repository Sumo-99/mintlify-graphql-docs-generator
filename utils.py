"""Shared helpers. Owned by Task B but used everywhere."""

from __future__ import annotations

import re

# 1. Split between a lowercase/digit and an uppercase: getProduct -> get|Product
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
# 2. Split between an acronym run and a following Capitalized word:
#    HTTPServer -> HTTP|Server, getJSONData -> ...JSON|Data
_ACRONYM_BOUNDARY = re.compile(r"(?<=[A-Z])(?=[A-Z][a-z])")
# 3. Split between a letter and a digit: get2 -> get|2, v2Api handled below
_LETTER_DIGIT = re.compile(r"(?<=[A-Za-z])(?=[0-9])")
# Runs of non-alphanumeric characters become a single separator.
_NON_ALNUM = re.compile(r"[^A-Za-z0-9]+")


def kebab_case(name: str) -> str:
    """'getProductById' -> 'get-product-by-id'.

    Handles camelCase, PascalCase, acronyms (HTTPServer -> http-server),
    digits, and existing separators (snake_case / spaces / dots).
    """
    if not name:
        return ""
    # Normalise existing separators to spaces first.
    s = _NON_ALNUM.sub(" ", name)
    # Insert boundaries for the camel/acronym/digit cases.
    s = _ACRONYM_BOUNDARY.sub(" ", s)
    s = _CAMEL_BOUNDARY.sub(" ", s)
    s = _LETTER_DIGIT.sub(" ", s)
    parts = [p for p in s.split() if p]
    return "-".join(p.lower() for p in parts)


def title_for(docstring: str, field_name: str) -> str:
    """Return the stripped docstring if non-blank, else the field name."""
    if docstring and docstring.strip():
        return docstring.strip()
    return field_name
