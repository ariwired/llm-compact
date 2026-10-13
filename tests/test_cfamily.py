from pathlib import Path

import pytest

from llm_compact.core.cfamily import compact_cfamily, lex_cfamily
from llm_compact.core.common import signature
from llm_compact.core.types import CompactOptions


def run(src, lang, lv="full", drop=False):
    return compact_cfamily(src, lang, CompactOptions(lv, drop))


@pytest.mark.parametrize(
    "lang,src,want",
    [
        ("java", "int   x  =  1 ;", "int x=1;"),
        ("java", "a = b - -c;", "a=b- -c;"),
        ("java", "a = b + +c;", "a=b+ +c;"),
        ("cpp", "x = a - --b;", "x=a- --b;"),
        ("cpp", "vector<vector<int> > v;", "vector<vector<int> >v;"),
        ("java", "a = b / /* c */ d;", "a=b/ /* c */d;"),
        ("cpp", "while (k --> 0) {}", "while(k-->0){}"),
        ("java", 'return   "x" ;', 'return "x";'),
        ("csharp", "x = 1 .ToString();", "x=1 .ToString();"),
        ("c", 'puts( "a   b" );', 'puts("a   b");'),
        ("cpp", 'auto s = R"x(  a   b\n  c )x" ;', 'auto s=R"x(  a   b\n  c )x";'),
        ("csharp", 'var s = @"a  ""b""  c" ;', 'var s=@"a  ""b""  c";'),
        ("cpp", 'auto s = "x"s ;', 'auto s="x"s;'),
    ],
)
def test_ports_original_rules(lang, src, want):
    r = run(src, lang)
    assert not r.fallback, r.warnings
    assert r.code == want


@pytest.mark.parametrize("lv", ["full", "light"])
def test_directives_and_macro_continuation_are_intact(lv):
    src = "#include <stdio.h>\n#define ADD(x) \\\n    ((x) + 1)\nint a; // note\nint b;\n"
    r = run(src, "cpp", lv)
    assert "#define ADD(x) \\\n    ((x) + 1)\n" in r.code
    assert "// note\n" in r.code
    assert signature(lex_cfamily(src, "cpp")) == signature(lex_cfamily(r.code, "cpp"))


def test_light_keeps_all_line_numbers_including_removed_comments():
    src = "\nint f() {\n    /* first\n       second */ int a = 1;\n\n\n    return a;\n}\n"
    r = run(src, "java", "light", True)
    assert r.code.count("\n") == src.count("\n")
    for nm in ["int f", "int a", "return a"]:
        assert src[: src.index(nm)].count("\n") == r.code[: r.code.index(nm)].count("\n")


def test_strip_comment_prevents_token_merge():
    assert run("a/* x */b", "java", drop=True).code == "a b"


@pytest.mark.parametrize(
    "lang,src",
    [
        ("java", r"int x; \u002f\u002f comment"),
        ("cpp", "#define S(x) #x\nauto s = S(a + b);"),
        ("c", "int x = __LINE__;"),
        ("c", "int x = 1 + \\\n    2;"),
        ("cpp", "// note \\\nint hidden;"),
        ("cpp", "/* no end"),
        ("java", 'String x = "no end'),
        ("csharp", 'var s = $"{d["key"]}";'),
        ("csharp", 'var s = $$$""" {{{d}}} """;'),
    ],
)
def test_unsupported_constructs_preserve_original(lang, src):
    r = run(src, lang)
    assert r.code == src
    assert r.fallback


@pytest.mark.parametrize(
    "fn,lang", [("Sample.java", "java"), ("sample.cpp", "cpp"), ("sample.c", "c")]
)
@pytest.mark.parametrize("lv", ["full", "light"])
def test_fixtures_lexical_equality(fn, lang, lv):
    src = (Path(__file__).parents[1] / "examples" / fn).read_text()
    r = run(src, lang, lv)
    assert not r.fallback, r.warnings
    assert signature(lex_cfamily(src, lang)) == signature(lex_cfamily(r.code, lang))


def test_java_text_block_preserved():
    lit = '"""\n    a  b\n    """'
    assert lit in run(f"String s = {lit} ;", "java").code


def test_pairwise_rule_does_not_silently_form_ellipsis():
    src = "a . . . b;"
    r = run(src, "java")
    assert r.fallback or signature(lex_cfamily(src, "java")) == signature(
        lex_cfamily(r.code, "java")
    )


def test_hex_literal_does_not_become_invalid_pp_number():
    assert run("unsigned x = 0xE + 1;", "cpp").code == "unsigned x=0xE +1;"


def test_digraph_directive_falls_back():
    src = "%:define X 1\nint value = X;"
    assert run(src, "cpp").fallback


@pytest.mark.parametrize("lang", ["c", "cpp"])
@pytest.mark.parametrize("lv", ["full", "light"])
@pytest.mark.parametrize("drop", [False, True])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_multiline_comment_in_directive_preserves_original(lang, lv, drop, newline):
    src = newline.join([
        "#define VALUE /* explanation",
        "continued */ 1",
        "int main(void) { return VALUE - 1; }",
        "",
    ])
    result = run(src, lang, lv, drop)
    assert result.fallback
    assert result.validation == "not-validated"
    assert result.code == src
    assert "preprocessor" in result.warnings[0]


@pytest.mark.parametrize("src", [
    "#define VALUE /* inline */ 1\nint value = VALUE;",
    '#define MARKER "/*"\nconst char *value = MARKER;',
])
def test_directive_guard_is_deliberately_conservative(src):
    result = run(src, "c")
    assert result.fallback
    assert result.code == src


@pytest.mark.parametrize("lv", ["full", "light"])
@pytest.mark.parametrize("drop", [False, True])
@pytest.mark.parametrize("name", [r"\u0061", r"\U00000061", r"@\u0061", r"a\u0062"])
def test_csharp_escaped_identifiers_preserve_original(lv, drop, name):
    src = f"class A {{ static int {name} = 1; }}\n"
    result = run(src, "csharp", lv, drop)
    assert result.fallback
    assert result.validation == "not-validated"
    assert result.code == src
    assert "Unicode" in result.warnings[0]


@pytest.mark.parametrize("src", [
    r'class A { string value = "\u0061"; }',
    r'class A { string value = @"\u0061"; }',
    r"class A { char value = '\u0061'; }",
    r'class A { /* \u0061 */ int value = 1; }',
])
def test_csharp_unicode_text_inside_literals_and_comments_is_preserved(src):
    result = run(src, "csharp")
    assert not result.fallback
    assert r"\u0061" in result.code


def test_lexical_validation_does_not_claim_syntax_validation():
    result = run("int main( {", "c")
    assert result.validation == "lexical"
    assert any("does not prove semantic equivalence" in warning for warning in result.warnings)
