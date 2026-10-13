import pytest

from llm_compact.core import CompactOptions, compact


@pytest.mark.parametrize("lang", ["javascript", "", "typescript"])
def test_unsupported_language(lang):
    with pytest.raises(ValueError):
        compact("code", lang)


def test_bad_options_and_size():
    with pytest.raises(ValueError):
        CompactOptions("invalid")
    with pytest.raises(ValueError):
        compact("x" * 1_000_001, "python")
    with pytest.raises(TypeError):
        compact(None, "python")


@pytest.mark.parametrize(
    "lang,src,want",
    [("python", "x = 1\n", "x=1\n"), ("java", "int x = 1 ;", "int x=1;")],
)
def test_language_dispatch(lang, src, want):
    assert compact(src, lang).code == want
