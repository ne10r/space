"""Check constants of every value kind and nested lexical scopes."""

from decimal import Decimal
from xml.etree import ElementTree

import pytest

from src.evaluator import evaluate_document
from src.main import convert
from src.parser import parse_source


@pytest.mark.parametrize("source,expected", [
    ("1.25 -> RATE @(RATE)", Decimal("1.25")),
    ("'text' -> TEXT @(TEXT)", "text"),
    ("$[A:1.0] -> DATA @(DATA)", {"A": Decimal("1.0")}),
    ("1.0 -> A @(A) -> B @(B)", Decimal("1.0")),
    ("$[1.0 -> A, VALUE:@(A)]", {"VALUE": Decimal("1.0")}),
    ("$[1.0 -> A]", {}),
])
def test_constant_values(source, expected):
    """Evaluate numbers, strings, dictionaries, aliases and local bindings."""
    assert evaluate_document(parse_source(source)) == expected


def test_nested_shadowing():
    """An inner constant shadows the outer one only inside its dictionary."""
    source = "1.0->A $[X:$[2.0->A,Y:@(A)],Z:@(A)]"
    root = ElementTree.fromstring(convert(source))
    assert root.find("X/Y").text == "2.0"
    assert root.find("Z").text == "1.0"


def test_reused_dictionary():
    """Resolve the same dictionary into independent XML subtrees."""
    root = ElementTree.fromstring(convert("$[X:'value']->D $[A:@(D),B:@(D)]"))
    assert root.find("A/X").text == "value"
    assert root.find("B/X").text == "value"


@pytest.mark.parametrize("source,message", [
    ("@(MISSING)", "Undefined constant"),
    ("@(A)->A 1.0", "Undefined constant"),
    ("1.0->A 2.0->A @(A)", "Duplicate constant"),
    ("$[1.0->A,2.0->A,X:@(A)]", "Duplicate constant"),
    ("$[INNER:$[1.0->A],OUTER:@(A)]", "Undefined constant"),
    ("$[X:@(A),1.0->A]", "Undefined constant"),
])
def test_constant_errors(source, message):
    """Reject redefinitions, forward references and references out of scope."""
    with pytest.raises(ValueError, match=message):
        convert(source)


def test_constant_namespace():
    """Dictionary keys and constant names belong to different namespaces."""
    root = ElementTree.fromstring(convert("$[A:1.0,2.0->A,B:@(A)]"))
    assert root.find("A").text == "1.0"
    assert root.find("B").text == "2.0"
