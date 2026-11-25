"""Translate standard input to XML, keeping all diagnostics on stderr."""

import argparse
import sys

from .evaluator import evaluate_document
from .parser import parse_source
from .xml_writer import to_xml

EXIT_SUCCESS = 0
EXIT_ERROR = 1


def convert(source: str) -> str:
    """Fully parse and evaluate input before emitting any XML."""
    try:
        return to_xml(evaluate_document(parse_source(source)))
    except RecursionError as error:
        raise ValueError("Configuration nesting is too deep") from error


def main() -> int:
    """Read stdin, validate the configuration and return a CLI status."""
    parser = argparse.ArgumentParser(
        description="Configuration language to XML, variant 21"
    )
    parser.parse_args()
    try:
        output = convert(sys.stdin.read())
        sys.stdout.write(output)
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
