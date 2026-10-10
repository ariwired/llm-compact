import ast
from pathlib import Path

import pytest

from llm_compact.core.python import compact_python
from llm_compact.core.types import CompactOptions

EXAMPLES = Path(__file__).parents[1] / "examples"


def run(src, lv="full", drop=False):
    return compact_python(src, CompactOptions(lv, drop))


def same_ast(x, y):
    assert ast.dump(ast.parse(x), include_attributes=False) == ast.dump(
        ast.parse(y), include_attributes=False
    )


@pytest.mark.parametrize("lv", ["full", "light"])
@pytest.mark.parametrize(
    "src",
    [
        "def f(a, b):\n    x = a + b   \n\n    return x\n",
        "values = [\n    1,  # first\n    2,\n]\n",
        "x = 1 + \\\n    2\n",
        's = "text  with  spaces"\nt = r"C:\\tmp\\test"\n',
        'def f():\n    """  Docstring\n      spaces  kept\n    """\n    return 1\n',
        'x = 3\ns = f"{x = }"\n',
        'd = {"name": "ann"}\ns = f"{d["name"]} {{ }}"\n',
        'x = "a" "b"\ny = - - 1\nz = 1 if y else 2\n',
        "# top\n\nif True:\n\tvalue = 1\n\tprint(value)\n",
        "x = [1,\n     2]\n\nprint(x)\n",
        'x = "a  b"\r\n\r\nprint( x )\r\n',
        "",
    ],
)
def test_valid_programs_keep_ast(src, lv):
    r = run(src, lv)
    assert r.validation == "python-ast"
    assert not r.fallback, r.warnings
    same_ast(src, r.code)
    if lv == "light":
        assert r.code.count("\n") == src.count("\n")


def test_python_compacts_real_whitespace():
    r = run("def f(a, b):\n    x = a + b\n\n    return x\n")
    assert r.code == "def f(a,b):\n    x=a+b\n    return x\n"


def test_full_joins_brackets():
    assert run("x = [\n    1,\n    2,\n]\n").code == "x=[1,2,]\n"


def test_comment_inside_brackets_keeps_newline():
    assert run("x = [1,  # note\n  2]").code == "x=[1,# note\n2]"


@pytest.mark.parametrize(
    "src", ["foo(\n    a,\n    b", 'x = "unclosed', "    return 1", "return 1"]
)
def test_invalid_or_partial_source_is_unchanged(src):
    r = run(src)
    assert r.code == src
    assert r.fallback
    assert r.validation == "not-validated"


def test_comments_opt_in_and_docstrings_stay():
    src = '#!/usr/bin/env python3\n# coding: utf-8\n# comment\n"""doc"""\nx = 1 # end\n'
    r = run(src, drop=True)
    assert "# comment" not in r.code and "# end" not in r.code
    assert '"""doc"""' in r.code
    assert "#!/usr/bin/env python3" in r.code and "# coding: utf-8" in r.code
    same_ast(src, r.code)


@pytest.mark.parametrize("lv", ["full", "light"])
def test_original_python_fixture(lv):
    src = (EXAMPLES / "sample.py").read_text()
    r = run(src, lv)
    assert not r.fallback, r.warnings
    same_ast(src, r.code)


def test_fstring_debug_preserves_runtime_output():
    src = 'x = 7\nvalue = f"{x = }"\n'
    r = run(src)
    g1, g2 = {}, {}
    exec(src, g1)
    exec(r.code, g2)
    assert g1["value"] == g2["value"] == "x = 7"


def test_full_idempotent():
    src = (EXAMPLES / "sample.py").read_text()
    once = run(src).code
    assert run(once).code == once

@pytest.mark.parametrize("lv", ["full", "light"])
@pytest.mark.parametrize(
    "src",
    [
        "x = 1\x0c\ny = 2\nz = f'{x}'\n",
        "\x0c\nx = 1\n\x0c\ny = f'{x} {x!r}'\n",
        "x = '\x1c'\ny = f'{x}'\n",
        "x = 1  # a\x85b\ny = f'{x}'\n",
        "x = 1  # a\u2028b\ny = f'{x}'\n",
        "s = '\u2029'\nt = f'{s}'\n",
    ],
)
def test_tokenizer_line_boundaries_are_not_splitlines(src, lv):
    r = run(src, lv)
    assert not r.fallback, r.warnings
    same_ast(src, r.code)
 
 
@pytest.mark.parametrize(
    ("src", "comment", "kept"),
    [
        ("#!/usr/bin/env python3\nx = 1\n", "#!/usr/bin/env python3", True),
        ("# coding: utf-8\nx = 1\n", "# coding: utf-8", True),
        ("# -*- coding: latin-1 -*-\nx = 1\n", "# -*- coding: latin-1 -*-", True),
        ("# vim: set fileencoding=utf-8 :\nx = 1\n", "# vim: set fileencoding=utf-8 :", True),
        ("#!/usr/bin/env python3\n# coding=utf-8\nx = 1\n", "# coding=utf-8", True),
        ("\n# coding: utf-8\nx = 1\n", "# coding: utf-8", True),
        ("# coding design patterns is my passion\nx = 1\n", "# coding design", False),
        ("#!/usr/bin/env python3\n# coding design patterns\nx = 1\n", "# coding design", False),
        ("x = 1\n# coding design patterns\n", "# coding design", False),
        ("x = 1\n# coding: utf-8\n", "# coding: utf-8", False),
        ("x = 1  # coding: utf-8\n", "# coding: utf-8", False),
        ("x = 1\ny = 2\n# coding: utf-8\n", "# coding: utf-8", False),
    ],
)
def test_strip_comments_keeps_only_real_coding_headers(src, comment, kept):
    r = run(src, drop=True)
    assert not r.fallback, r.warnings
    assert (comment in r.code) is kept
    same_ast(src, r.code)
 
 
@pytest.mark.parametrize("lv", ["full", "light"])
@pytest.mark.parametrize(
    "pragma",
    [
        "# type: ignore",
        "# type: ignore[arg-type]",
        "# type: int",
        "# noqa",
        "# noqa: E501",
        "# NOQA:E501,F401",
        "# fmt: off",
        "# fmt: on",
        "# fmt: skip",
        "# isort: skip",
        "# pylint: disable=unused-import",
        "# mypy: ignore-errors",
        "# pyright: ignore",
        "# ruff: noqa",
        "# nosec",
        "# pragma: no cover",
        "# some explanation  # noqa: E501",
    ],
)
def test_strip_comments_keeps_tool_pragmas(pragma, lv):
    src = f"import os  {pragma}\n{pragma}\nx = [1,  2]  # plain note\n"
    r = run(src, lv, drop=True)
    assert not r.fallback, r.warnings
    assert r.code.count(pragma) == 2
    assert "plain note" not in r.code
    same_ast(src, r.code)
 
 
def test_strip_comments_removes_regular_comments():
    src = "# just a comment\nx = 1  # trailing note\n# nothing special\ny = 2\n"
    r = run(src, drop=True)
    assert r.code == "x=1\ny=2\n"
    same_ast(src, r.code)
