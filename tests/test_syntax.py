"""Cover malformed constructions and composition at multiple depths."""

from xml.etree import ElementTree

import pytest

from src.main import convert


@pytest.mark.parametrize("source", [
    "$[A_:$[]]", "$[А:1.0]", "$[A : ]", "$[A=1.0]",
    "$[A:1.0,,]", "$[,A:1.0]", "[A:1.0]", "$[A:[1.0]]",
    "1.0 -> lower 2.0", "1.0 -> A", "@A", "@()", "@(a)",
    "@(A + 1.0)", "$[X:nan]", "$[X:true]", "'it's text'",
    "{- only a comment -}", "{- outer {- inner -} tail -}1.0",
])
def test_malformed_constructs(source):
    """Require the stated delimiters, alphabet and complete root value."""
    with pytest.raises(ValueError):
        convert(source)


def test_composition():
    """Combine a dictionary constant, local string, nested reference and WS."""
    source = """
    {- document comment -}
    $[RATE: -1.50] -> BASE
    $[
        INNER: $[
            'literal {- text -}' -> TITLE,
            DATA: @(BASE),
            TEXT: @(TITLE),
        ],
        EMPTY: $[],
    ]
    """
    root = ElementTree.fromstring(convert(source))
    assert root.find("INNER/DATA/RATE").text == "-1.50"
    assert root.find("INNER/TEXT").text == "literal {- text -}"
    assert root.find("EMPTY").get("type") == "dictionary"


def test_field_order():
    """Preserve declaration order of dictionary members in XML output."""
    root = ElementTree.fromstring(convert("$[Z:1.0,A:2.0,M:3.0]"))
    assert [child.tag for child in root] == ["Z", "A", "M"]


def test_deep_dictionary():
    """Parse and translate a dictionary nested forty times."""
    depth = 40
    source = "$[A:" * depth + "'bottom'" + "]" * depth
    root = ElementTree.fromstring(convert(source))
    for _ in range(depth):
        root = root.find("A")
    assert root.text == "bottom"


def test_excessive_depth():
    """Turn the runtime recursion limit into a clean translation error."""
    depth = 2000
    source = "$[A:" * depth + "1.0" + "]" * depth
    with pytest.raises(ValueError, match="nesting is too deep"):
        convert(source)
