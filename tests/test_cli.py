"""Exercise stdin, stdout, stderr and return codes through real processes."""

import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXIT_SUCCESS = 0
EXIT_ERROR = 1
ARGUMENT_ERROR_EXIT_CODE = 2


def run_cli(source: str, *arguments):
    """Run from the repository root with UTF-8 text input."""
    return subprocess.run(
        [sys.executable, "-m", "src.main", *arguments], cwd=ROOT,
        input=source, text=True, encoding="utf-8", capture_output=True,
        timeout=10,
    )


def test_successful_cli():
    """Emit only parseable XML, without status banners or debug output."""
    result = run_cli("'Привет' -> NAME $[TITLE:@(NAME),RATE:+1.25]")
    assert result.returncode == EXIT_SUCCESS
    assert result.stderr == ""
    root = ElementTree.fromstring(result.stdout)
    assert root.find("TITLE").text == "Привет"
    assert root.find("RATE").text == "1.25"


@pytest.mark.parametrize("source", [
    "", "$[A:1.0", "$[A:1.0,A:2.0]", "@(UNKNOWN)",
    "1.0->A $[GOOD:@(A),BAD:@(MISSING)]", "'\x00'",
])
def test_cli_errors(source):
    """Keep stdout empty even if an error occurs after valid constructs."""
    result = run_cli(source)
    assert result.returncode == EXIT_ERROR
    assert result.stdout == ""
    assert result.stderr.startswith("Error:")
    assert "Line " in result.stderr
    assert "Traceback" not in result.stderr


def test_error_context():
    """Print the offending line and a caret for a nested syntax error."""
    result = run_cli("$[\nVALID:1.0,\ninvalid:2.0\n]")
    assert result.returncode == EXIT_ERROR
    assert "Line 3" in result.stderr
    assert "^" in result.stderr


def test_unknown_option():
    """Reject undeclared command-line settings using argparse's status."""
    result = run_cli("1.0", "--input", "not-used.conf")
    assert result.returncode == ARGUMENT_ERROR_EXIT_CODE
    assert result.stdout == ""


def test_help():
    """Describe the translator without attempting to parse empty stdin."""
    result = run_cli("", "--help")
    assert result.returncode == EXIT_SUCCESS
    assert "variant 21" in result.stdout
    assert result.stderr == ""


def test_invalid_utf8():
    """Reject invalid byte input without writing an invalid XML document."""
    result = subprocess.run(
        [sys.executable, "-m", "src.main"], cwd=ROOT,
        input=b"'\xff'", capture_output=True, timeout=10,
    )
    assert result.returncode == EXIT_ERROR
    assert result.stdout == b""
    assert b"Traceback" not in result.stderr
