"""Tests for the Infinispan metadata filter mapper.

Adapted from langchain4j InfinispanMetadataFilterMapperTest.
"""

import pytest
from langchain_core.structured_query import Comparator, Comparison, Operation, Operator

from langchain_infinispan._filters import translate_filter


class TestTranslateFilterNone:
    def test_none_returns_none(self) -> None:
        assert translate_filter(None) is None

    def test_empty_dict_returns_none(self) -> None:
        assert translate_filter({}) is None


class TestDictFilters:
    def test_single_string_equality(self) -> None:
        result = translate_filter({"name": "John"})
        assert result is not None
        assert "m0.name='name'" in result.query
        assert "m0.value = 'John'" in result.query
        assert result.join == "join i.metadata m0"

    def test_multiple_keys_produces_and(self) -> None:
        result = translate_filter({"name": "John", "age": 25})
        assert result is not None
        assert "AND" in result.query
        assert "m0" in result.query
        assert "m1" in result.query
        assert "join i.metadata m0 join i.metadata m1" == result.join

    def test_int_value_uses_value_int(self) -> None:
        result = translate_filter({"age": 25})
        assert result is not None
        assert "m0.value_int = 25" in result.query

    def test_float_value_uses_value_float(self) -> None:
        result = translate_filter({"score": 3.14})
        assert result is not None
        assert "m0.value_float = 3.14" in result.query

    def test_bool_value_uses_value_string(self) -> None:
        # bool is a subclass of int, but booleans are stored in the string
        # ``value`` column, so filtering must target ``value`` too (not value_int).
        result = translate_filter({"flag": True})
        assert result is not None
        assert "m0.value = 'True'" in result.query
        assert "value_int" not in result.query

    def test_list_value_produces_in(self) -> None:
        result = translate_filter({"category": ["A", "B", "C"]})
        assert result is not None
        assert "IN ('A', 'B', 'C')" in result.query


class TestComparisonFilters:
    def test_equal_string(self) -> None:
        f = Comparison(comparator=Comparator.EQ, attribute="name", value="John")
        result = translate_filter(f)
        assert result is not None
        assert result.query == "m0.name='name' and m0.value = 'John'"
        assert result.join == "join i.metadata m0"

    def test_equal_int(self) -> None:
        f = Comparison(comparator=Comparator.EQ, attribute="age", value=25)
        result = translate_filter(f)
        assert result is not None
        assert result.query == "m0.name='age' and m0.value_int = 25"

    def test_equal_float(self) -> None:
        f = Comparison(comparator=Comparator.EQ, attribute="score", value=3.14)
        result = translate_filter(f)
        assert result is not None
        assert result.query == "m0.name='score' and m0.value_float = 3.14"

    def test_equal_bool(self) -> None:
        f = Comparison(comparator=Comparator.EQ, attribute="flag", value=True)
        result = translate_filter(f)
        assert result is not None
        assert result.query == "m0.name='flag' and m0.value = 'True'"

    def test_not_equal(self) -> None:
        f = Comparison(comparator=Comparator.NE, attribute="status", value="active")
        result = translate_filter(f)
        assert result is not None
        assert "m0.value != 'active'" in result.query
        assert "m0.name='status'" in result.query
        assert "OR (i.metadata is null)" in result.query

    def test_greater_than_string(self) -> None:
        f = Comparison(comparator=Comparator.GT, attribute="name", value="A")
        result = translate_filter(f)
        assert result is not None
        assert result.query == "m0.name='name' and m0.value > 'A'"

    def test_greater_than_int(self) -> None:
        f = Comparison(comparator=Comparator.GT, attribute="age", value=18)
        result = translate_filter(f)
        assert result is not None
        assert result.query == "m0.name='age' and m0.value_int > 18"

    def test_greater_than_or_equal(self) -> None:
        f = Comparison(comparator=Comparator.GTE, attribute="name", value="A")
        result = translate_filter(f)
        assert result is not None
        assert result.query == "m0.name='name' and m0.value >= 'A'"

    def test_less_than(self) -> None:
        f = Comparison(comparator=Comparator.LT, attribute="name", value="Z")
        result = translate_filter(f)
        assert result is not None
        assert result.query == "m0.name='name' and m0.value < 'Z'"

    def test_less_than_float(self) -> None:
        f = Comparison(comparator=Comparator.LT, attribute="score", value=4.5)
        result = translate_filter(f)
        assert result is not None
        assert result.query == "m0.name='score' and m0.value_float < 4.5"

    def test_less_than_or_equal(self) -> None:
        f = Comparison(comparator=Comparator.LTE, attribute="name", value="Z")
        result = translate_filter(f)
        assert result is not None
        assert result.query == "m0.name='name' and m0.value <= 'Z'"


class TestInFilters:
    def test_string_in(self) -> None:
        f = Comparison(
            comparator=Comparator.IN,
            attribute="category",
            value=["A", "B", "C"],
        )
        result = translate_filter(f)
        assert result is not None
        assert "m0.name='category'" in result.query
        assert "m0.value IN ('A', 'B', 'C')" in result.query

    def test_int_in(self) -> None:
        f = Comparison(comparator=Comparator.IN, attribute="status", value=[1, 2, 3])
        result = translate_filter(f)
        assert result is not None
        assert "m0.value_int IN (1, 2, 3)" in result.query

    def test_string_not_in(self) -> None:
        f = Comparison(
            comparator=Comparator.NIN,
            attribute="category",
            value=["X", "Y", "Z"],
        )
        result = translate_filter(f)
        assert result is not None
        assert "m0.value NOT IN ('X', 'Y', 'Z')" in result.query
        assert "m0.name='category'" in result.query
        assert "OR (i.metadata is null)" in result.query

    def test_bool_in_uses_value_string(self) -> None:
        f = Comparison(comparator=Comparator.IN, attribute="flag", value=[True, False])
        result = translate_filter(f)
        assert result is not None
        assert "m0.value IN ('True', 'False')" in result.query

    def test_bool_and_string_in_does_not_mix(self) -> None:
        # bools are strings here, so mixing with text must not raise.
        f = Comparison(
            comparator=Comparator.IN, attribute="flag", value=[True, "maybe"]
        )
        result = translate_filter(f)
        assert result is not None
        assert "m0.value IN ('True', 'maybe')" in result.query

    def test_empty_in_raises(self) -> None:
        f = Comparison(comparator=Comparator.IN, attribute="key", value=[])
        with pytest.raises(ValueError, match="must contain values"):
            translate_filter(f)

    def test_mixed_types_in_raises(self) -> None:
        f = Comparison(comparator=Comparator.IN, attribute="key", value=[1, "text"])
        with pytest.raises(ValueError, match="cannot mix"):
            translate_filter(f)


class TestLogicalOperations:
    def test_and(self) -> None:
        f = Operation(
            operator=Operator.AND,
            arguments=[
                Comparison(comparator=Comparator.EQ, attribute="name", value="John"),
                Comparison(comparator=Comparator.EQ, attribute="age", value=25),
            ],
        )
        result = translate_filter(f)
        assert result is not None
        assert "m0.name='name' and m0.value = 'John'" in result.query
        assert "m1.name='age' and m1.value_int = 25" in result.query
        assert "AND" in result.query
        assert result.join == "join i.metadata m0 join i.metadata m1"

    def test_or(self) -> None:
        f = Operation(
            operator=Operator.OR,
            arguments=[
                Comparison(comparator=Comparator.EQ, attribute="name", value="John"),
                Comparison(comparator=Comparator.EQ, attribute="name", value="Jane"),
            ],
        )
        result = translate_filter(f)
        assert result is not None
        assert "OR" in result.query
        assert "m0.value = 'John'" in result.query
        assert "m1.value = 'Jane'" in result.query

    def test_not(self) -> None:
        f = Operation(
            operator=Operator.NOT,
            arguments=[
                Comparison(comparator=Comparator.EQ, attribute="name", value="John"),
            ],
        )
        result = translate_filter(f)
        assert result is not None
        assert "NOT" in result.query

    def test_complex_nested(self) -> None:
        f = Operation(
            operator=Operator.AND,
            arguments=[
                Comparison(
                    comparator=Comparator.EQ, attribute="category", value="book"
                ),
                Operation(
                    operator=Operator.OR,
                    arguments=[
                        Comparison(
                            comparator=Comparator.GT, attribute="price", value=10.0
                        ),
                        Comparison(
                            comparator=Comparator.LT, attribute="price", value=5.0
                        ),
                    ],
                ),
            ],
        )
        result = translate_filter(f)
        assert result is not None
        assert "m0.name='category'" in result.query
        assert "m1.name='price'" in result.query
        assert "m2.name='price'" in result.query
        assert "AND" in result.query
        assert "OR" in result.query
        assert result.join == "join i.metadata m0 join i.metadata m1 join i.metadata m2"

    def test_four_metadata_joins(self) -> None:
        f = Operation(
            operator=Operator.AND,
            arguments=[
                Comparison(comparator=Comparator.EQ, attribute="name", value="John"),
                Operation(
                    operator=Operator.AND,
                    arguments=[
                        Comparison(comparator=Comparator.EQ, attribute="age", value=25),
                        Operation(
                            operator=Operator.AND,
                            arguments=[
                                Comparison(
                                    comparator=Comparator.EQ,
                                    attribute="city",
                                    value="New York",
                                ),
                                Comparison(
                                    comparator=Comparator.EQ,
                                    attribute="country",
                                    value="USA",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
        result = translate_filter(f)
        assert result is not None
        assert result.join == (
            "join i.metadata m0 join i.metadata m1 "
            "join i.metadata m2 join i.metadata m3"
        )


class TestEscaping:
    def test_single_quote_in_value(self) -> None:
        f = Comparison(comparator=Comparator.EQ, attribute="name", value="O'Brien")
        result = translate_filter(f)
        assert result is not None
        assert "O''Brien" in result.query

    def test_single_quote_in_key(self) -> None:
        f = Comparison(comparator=Comparator.EQ, attribute="o'clock", value="noon")
        result = translate_filter(f)
        assert result is not None
        assert "o''clock" in result.query

    def test_backslash_in_value(self) -> None:
        f = Comparison(
            comparator=Comparator.EQ, attribute="path", value="C:\\Users\\test"
        )
        result = translate_filter(f)
        assert result is not None
        assert "C:\\\\Users\\\\test" in result.query

    def test_ickle_injection_in_value(self) -> None:
        f = Comparison(comparator=Comparator.EQ, attribute="name", value="x' OR 1=1 --")
        result = translate_filter(f)
        assert result is not None
        assert "x'' OR 1=1 --" in result.query

    def test_ickle_injection_in_key(self) -> None:
        f = Comparison(
            comparator=Comparator.EQ,
            attribute="foo' OR 1=1 OR name='",
            value="bar",
        )
        result = translate_filter(f)
        assert result is not None
        assert "foo'' OR 1=1 OR name=''" in result.query


class TestUnsupported:
    def test_unsupported_filter_type_raises(self) -> None:
        with pytest.raises(TypeError, match="Unsupported filter type"):
            translate_filter(42)  # type: ignore[arg-type]
