"""Verify XML validity, decimal precision and exact string round trips."""

from xml.etree import ElementTree

import pytest

from src.main import convert


@pytest.mark.parametrize("value", [
    "", "   ", "\t", "\n", "\r", "first\r\nsecond", "Привет 😀",
    "<tag>&text</tag>", 'text "quoted"', "{- not a comment -}",
    "literal \\n text", "-> @(NAME) $[A:1.0]",
])
def test_string_round_trip(value):
    """Preserve content while escaping markup and literal carriage returns."""
    output = convert("$[TEXT:'" + value + "']")
    root = ElementTree.fromstring(output)
    assert (root.find("TEXT").text or "") == value
    assert root.find("TEXT").get("type") == "string"


@pytest.mark.parametrize("character", [
    "\x00", "\x01", "\x0b", "\x1f", "\ud800", "\ufffe", "\uffff",
])
def test_forbidden_xml_characters(character):
    """Fail with a position instead of emitting an invalid XML character."""
    with pytest.raises(ValueError, match="Line 1.*not allowed in XML"):
        convert("'" + character + "'")


@pytest.mark.parametrize("source,expected", [
    ("12345678901234567890.12345678901234567890",
     "12345678901234567890.12345678901234567890"),
    ("+0001.2300", "1.2300"), ("-0.0", "-0.0"),
    ("١٢.٥٠", "12.50"),
])
def test_exact_numbers(source, expected):
    """Avoid binary float rounding while preserving fractional zeroes."""
    root = ElementTree.fromstring(convert(source))
    assert root.get("type") == "number"
    assert root.text == expected


def test_empty_types():
    """Use type attributes to distinguish structurally empty values."""
    root = ElementTree.fromstring(convert("$[TEXT:'',DATA:$[]]"))
    assert root.find("TEXT").get("type") == "string"
    assert root.find("DATA").get("type") == "dictionary"


def test_bom():
    """Allow one UTF-8 signature at the start of the input."""
    assert ElementTree.fromstring(convert("\ufeff1.0")).text == "1.0"


def test_semantic_position():
    """Locate an undefined reference at its actual position in a dictionary."""
    with pytest.raises(ValueError, match="Line 2, column 3"):
        convert("$[\nA:@(MISSING)\n]")
