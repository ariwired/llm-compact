import pytest

from llm_compact.core import compact
from llm_compact.tokens import compare_tokens, count_tokens

try:
    count_tokens("x")
except Exception:
    pytest.skip("tiktoken tables unavailable", allow_module_level=True)


def test_special_looking_text_is_counted_as_text():
    assert count_tokens("<|endoftext|>") > 1


def test_empty_input_reports_zero_percent():
    for r in compare_tokens("", ""):
        assert (r.before, r.after, r.percent) == (0, 0, 0.0)


@pytest.mark.parametrize("lang", ["java", "c", "cpp", "csharp"])
def test_compaction_does_not_increase_tokens_on_formatted_code(lang):
    src = "class A {\n    int f(int x) {\n        return x + 1;\n    }\n}\n"
    out = compact(src, lang)
    for r in compare_tokens(src, out.code):
        assert r.after <= r.before and r.saved == r.before - r.after
