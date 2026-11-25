"""Parse the complete input with the specialized Lark LALR parser."""

from pathlib import Path

from lark import Lark, Tree
from lark.exceptions import UnexpectedInput

GRAMMAR = Path(__file__).with_name("grammar.lark")
PARSER = Lark(
    GRAMMAR.read_text(encoding="utf-8"), parser="lalr",
    propagate_positions=True, maybe_placeholders=False,
)


def parse_source(source: str) -> Tree:
    """Reject syntax errors with their source line, column and context."""
    text = source.removeprefix("\ufeff")
    try:
        return PARSER.parse(text)
    except UnexpectedInput as error:
        context = error.get_context(text, span=40).rstrip()
        message = f"Line {error.line}, column {error.column}: syntax error"
        raise ValueError(f"{message}\n{context}") from error
