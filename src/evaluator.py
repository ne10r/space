"""Convert parsed numbers, strings and nested dictionaries to values."""

from decimal import Decimal

from lark import Tree

from .xml_writer import is_xml_character


def source_error(message: str, node: Tree) -> ValueError:
    """Attach a parsed construct's source position to a semantic error."""
    position = f"Line {node.meta.line}, column {node.meta.column}"
    return ValueError(f"{position}: {message}")


def evaluate_value(node: Tree, scopes: list[dict]):
    """Keep decimal precision and interpret quote contents literally."""
    if node.data == "number":
        return Decimal(str(node.children[0]))
    if node.data == "string":
        return evaluate_string(node)
    if node.data == "reference":
        return resolve_constant(node, scopes)
    return evaluate_dictionary(node, scopes)


def evaluate_string(node: Tree) -> str:
    """Reject text that would make the serialized XML document invalid."""
    value = str(node.children[0])[1:-1]
    for character in value:
        if not is_xml_character(character):
            message = f"Character U+{ord(character):04X} is not allowed in XML"
            raise source_error(message, node)
    return value


def resolve_constant(node: Tree, scopes: list[dict]):
    """Look up a previously declared name from the nearest lexical scope."""
    name = str(node.children[0])
    for scope in reversed(scopes):
        if name in scope:
            return scope[name]
    raise source_error(f"Undefined constant: {name}", node)


def define_constant(node: Tree, scopes: list[dict]) -> None:
    """Evaluate before binding, preventing forward and self references."""
    value, token = node.children
    name = str(token)
    if name in scopes[-1]:
        raise source_error(f"Duplicate constant: {name}", node)
    scopes[-1][name] = evaluate_value(value, scopes)


def evaluate_dictionary(node: Tree, scopes: list[dict]) -> dict:
    """Use a local scope without leaking nested constant declarations."""
    result = {}
    local = [*scopes, {}]
    for pair in node.children:
        if pair.data == "declaration":
            define_constant(pair, local)
            continue
        name = str(pair.children[0])
        if name in result:
            raise source_error(f"Duplicate dictionary key: {name}", pair)
        result[name] = evaluate_value(pair.children[1], local)
    return result


def evaluate_document(tree: Tree):
    """Process document declarations before the single final root value."""
    scopes = [{}]
    for declaration in tree.children[:-1]:
        define_constant(declaration, scopes)
    return evaluate_value(tree.children[-1], scopes)
