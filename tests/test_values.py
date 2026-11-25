"""Check the grammar's scalar and dictionary values."""

from decimal import Decimal
from xml.etree import ElementTree

import pytest

from src.evaluator import evaluate_document
from src.main import convert
from src.parser import parse_source


@pytest.mark.parametrize("source,expected", [
    ("12.50", Decimal("12.50")), ("+1.0", Decimal("1.0")),
    ("-0.25", Decimal("-0.25")), ("'Привет'", "Привет"),
    ("''", ""), ("$[]", {}),
    ("$[A:1.0,B:$[C:'text']]", {"A": Decimal("1.0"), "B": {"C": "text"}}),
])
def test_values(source, expected):
    """Recognize each value kind, including nesting and empty values."""
    assert evaluate_document(parse_source(source)) == expected


def test_comment_and_trailing_comma():
    """Ignore a multiline comment between dictionary tokens."""
    root = ElementTree.fromstring(convert("$[A:{- first\nsecond -}1.0,]"))
    assert root.find("A").text == "1.0"


def test_xml_escaping():
    """Round-trip XML special characters without creating extra elements."""
    value = "A & B < C > D"
    output = convert("$[TEXT:'" + value + "']")
    assert "&amp;" in output
    assert "&lt;" in output
    assert ElementTree.fromstring(output).find("TEXT").text == value


@pytest.mark.parametrize("source", [
    "1", ".5", "1.", "1.0e2", "$[lower:1.0]", "$[A1:1.0]",
    "$[A:1.0 B:2.0]", "$[A:1.0", "'unfinished", "{- unfinished",
    "$[A:1.0,A:2.0]", "", "1.0 2.0",
])
def test_invalid_values(source):
    """Reject syntax errors and repeated dictionary keys."""
    with pytest.raises(ValueError):
        convert(source)
