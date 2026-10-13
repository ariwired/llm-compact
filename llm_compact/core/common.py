from collections.abc import Callable

from .types import Token


def signature(toks: list[Token], drop: bool = False) -> list[tuple[str, str]]:
    return [(k.kind, k.text) for k in toks if not (drop and k.kind == "comment")]


def needs_space(lx: Callable[[str], list[Token]], left: Token, right: Token) -> bool:
    solo = "(){}[];,"
    if left.kind == "punct" and left.text in solo:
        return False
    if right.kind == "punct" and right.text in solo:
        return False
    if left.kind == right.kind == "word":
        return True
    if {left.kind, right.kind} == {"word", "string"}:
        return True
    try:
        merged = lx(left.text + right.text)
        return signature(merged) != [(left.kind, left.text), (right.kind, right.text)]
    except ValueError:
        return True
