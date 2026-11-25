"""Serialize typed configuration values using the standard XML library."""

from decimal import Decimal
from xml.etree import ElementTree

XML_WHITESPACE = {9, 10, 13}
XML_RANGES = ((0x20, 0xD7FF), (0xE000, 0xFFFD), (0x10000, 0x10FFFF))


def is_xml_character(character: str) -> bool:
    """Accept exactly the character ranges allowed by XML 1.0."""
    code = ord(character)
    return code in XML_WHITESPACE or any(
        start <= code <= end for start, end in XML_RANGES
    )


def make_element(name: str, value) -> ElementTree.Element:
    """Retain types so empty dictionaries and empty strings differ."""
    element = ElementTree.Element(name)
    if isinstance(value, dict):
        element.set("type", "dictionary")
        for key, item in value.items():
            element.append(make_element(key, item))
    elif isinstance(value, Decimal):
        element.set("type", "number")
        element.text = format(value, "f")
    else:
        element.set("type", "string")
        element.text = value
    return element


def to_xml(value) -> str:
    """Produce UTF-8 XML with stable field ordering and escaped text."""
    root = make_element("config", value)
    ElementTree.indent(root, space="  ")
    binary = ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)
    return binary.decode("utf-8").replace("\r", "&#13;") + "\n"
