"""Check representative configurations from the three required domains."""

from pathlib import Path
from xml.etree import ElementTree

import pytest

from src.main import convert

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name,path,expected", [
    ("web", "HTTP/HOST", "api.example.test"),
    ("web", "DATABASE/POOL/MAX", "10.0"),
    ("laboratory", "SENSOR/MODEL", "T & H <logger>"),
    ("laboratory", "LIMITS/REFERENCE", "21.50"),
    ("game", "DISPLAY/WIDTH", "1280.0"),
    ("game", "PLAYER/MOVEMENT/SPEED", "100.0"),
])
def test_domain_example(name, path, expected):
    """Resolve nested data and constants in real checked-in examples."""
    source = (ROOT / "examples" / (name + ".conf")).read_text("utf-8")
    root = ElementTree.fromstring(convert(source))
    assert root.get("type") == "dictionary"
    assert root.find(path).text == expected
