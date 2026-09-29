"""Metadata filter mapper for Infinispan Ickle queries.

Translates LangChain filter expressions into Infinispan Ickle query fragments
with ``join i.metadata mN`` clauses, adapted from the langchain4j Java
implementation (InfinispanMetadataFilterMapper).

Supports two filter formats:
  - ``dict``: simple key-value equality matching (e.g. ``{"source": "web"}``)
  - ``FilterDirective``: langchain-core structured query filters
    (``Comparison`` and ``Operation`` with ``Comparator``/``Operator`` enums)
"""

from __future__ import annotations

from typing import Any, Collection, Optional

from langchain_core.structured_query import (
    Comparator,
    Comparison,
    FilterDirective,
    Operation,
    Operator,
)


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "''")


def _value_column(values: Collection[Any]) -> str:
    if any(isinstance(v, float) for v in values):
        return "value_float"
    if all(isinstance(v, int) for v in values):
        return "value_int"
    return "value"


def _format_comparison_value(value: Any, as_float: bool = False) -> str:
    if not isinstance(value, (int, float)):
        return f"'{_escape(str(value))}'"
    if as_float:
        return str(float(value))
    return str(value)


class _FilterState:
    def __init__(self) -> None:
        self._counter = -1

    def next_alias(self) -> str:
        self._counter += 1
        return f"m{self._counter}"

    @property
    def join_clause(self) -> str:
        if self._counter < 0:
            return ""
        return " ".join(f"join i.metadata m{j}" for j in range(self._counter + 1))


class FilterResult:
    """Result of translating a filter to Ickle query fragments."""

    def __init__(self, query: str, join: str) -> None:
        self.query = query
        self.join = join


def _map_comparison(comp: Comparison, state: _FilterState) -> str:
    alias = state.next_alias()
    key = comp.attribute
    value = comp.value
    comparator = comp.comparator

    key_clause = f"{alias}.name='{_escape(key)}'"

    if comparator == Comparator.EQ:
        return key_clause + " and " + _compute_filter(alias, "=", value)

    elif comparator == Comparator.NE:
        return (
            _compute_filter(alias, "!=", value)
            + f" and {alias}.name='{_escape(key)}'"
            + " OR (i.metadata is null) "
        )

    elif comparator == Comparator.GT:
        return key_clause + " and " + _compute_filter(alias, ">", value)

    elif comparator == Comparator.GTE:
        return key_clause + " and " + _compute_filter(alias, ">=", value)

    elif comparator == Comparator.LT:
        return key_clause + " and " + _compute_filter(alias, "<", value)

    elif comparator == Comparator.LTE:
        return key_clause + " and " + _compute_filter(alias, "<=", value)

    elif comparator == Comparator.IN:
        return _map_in(alias, key, value)

    elif comparator == Comparator.NIN:
        return _map_not_in(alias, key, value)

    elif comparator == Comparator.CONTAIN:
        return key_clause + f" and {alias}.value like '%{_escape(str(value))}%'"

    elif comparator == Comparator.LIKE:
        return key_clause + f" and {alias}.value like '{_escape(str(value))}'"

    else:
        raise ValueError(f"Unsupported comparator: {comparator}")


def _compute_filter(alias: str, operator: str, value: Any) -> str:
    if isinstance(value, int):
        return f"{alias}.value_int {operator} {value}"
    elif isinstance(value, float):
        return f"{alias}.value_float {operator} {value}"
    else:
        return f"{alias}.value {operator} '{_escape(str(value))}'"


def _map_in(alias: str, key: str, values: Collection[Any]) -> str:
    if not values:
        raise ValueError("Infinispan metadata filter IN must contain values")
    _validate_no_mixed_types(values)
    column = f"{alias}.{_value_column(values)}"
    as_float = _value_column(values) == "value_float"
    formatted = ", ".join(_format_comparison_value(v, as_float) for v in values)
    return f"{alias}.name='{_escape(key)}' and {column} IN ({formatted})"


def _map_not_in(alias: str, key: str, values: Collection[Any]) -> str:
    if not values:
        raise ValueError("Infinispan metadata filter NOT IN must contain values")
    _validate_no_mixed_types(values)
    column = f"{alias}.{_value_column(values)}"
    as_float = _value_column(values) == "value_float"
    formatted = ", ".join(_format_comparison_value(v, as_float) for v in values)
    escaped_key = _escape(key)
    return (
        f"({column} NOT IN ({formatted}) and {alias}.name='{escaped_key}') "
        f"OR ({column} IN ({formatted}) and {alias}.name!='{escaped_key}') "
        f"OR (i.metadata is null) "
    )


def _validate_no_mixed_types(values: Collection[Any]) -> None:
    has_numeric = any(isinstance(v, (int, float)) for v in values)
    has_non_numeric = any(not isinstance(v, (int, float)) for v in values)
    if has_numeric and has_non_numeric:
        raise ValueError(
            "Infinispan metadata filter IN/NOT IN cannot mix "
            "numeric and non-numeric values"
        )


def _map_operation(op: Operation, state: _FilterState) -> str:
    if op.operator == Operator.AND:
        parts = [_map_filter_directive(arg, state) for arg in op.arguments]
        return "((" + ") AND (".join(parts) + "))"

    elif op.operator == Operator.OR:
        parts = [_map_filter_directive(arg, state) for arg in op.arguments]
        return "((" + ") OR (".join(parts) + "))"

    elif op.operator == Operator.NOT:
        if len(op.arguments) != 1:
            raise ValueError("NOT operator requires exactly one argument")
        inner = _map_filter_directive(op.arguments[0], state)
        return f"(NOT ({inner}))"

    else:
        raise ValueError(f"Unsupported operator: {op.operator}")


def _map_filter_directive(f: FilterDirective, state: _FilterState) -> str:
    if isinstance(f, Comparison):
        return _map_comparison(f, state)
    elif isinstance(f, Operation):
        return _map_operation(f, state)
    else:
        raise ValueError(f"Unsupported filter type: {type(f).__name__}")


def _map_dict_filter(d: dict[str, Any], state: _FilterState) -> str:
    """Convert a simple dict filter to Ickle query using equality comparisons."""
    if not d:
        return ""
    parts = []
    for key, value in d.items():
        if isinstance(value, (list, tuple, set)):
            comp = Comparison(
                comparator=Comparator.IN, attribute=key, value=list(value)
            )
        else:
            comp = Comparison(comparator=Comparator.EQ, attribute=key, value=value)
        parts.append(_map_comparison(comp, state))
    if len(parts) == 1:
        return parts[0]
    return "((" + ") AND (".join(parts) + "))"


def translate_filter(
    filter: Optional[dict[str, Any] | FilterDirective],
) -> Optional[FilterResult]:
    """Translate a filter into Ickle query fragments.

    Args:
        filter: Either a dict (simple key-value equality) or a
            langchain-core FilterDirective (Comparison/Operation).

    Returns:
        FilterResult with ``query`` and ``join`` strings, or None if
        no filter is provided.
    """
    if filter is None:
        return None

    state = _FilterState()

    if isinstance(filter, dict):
        if not filter:
            return None
        query = _map_dict_filter(filter, state)
    elif isinstance(filter, FilterDirective):
        query = _map_filter_directive(filter, state)
    else:
        raise TypeError(
            f"Unsupported filter type: {type(filter).__name__}. "
            "Expected dict or FilterDirective."
        )

    return FilterResult(query=query, join=state.join_clause)
