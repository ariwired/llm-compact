import shutil
import subprocess
from pathlib import Path

import pytest

from llm_compact.core.cfamily import compact_cfamily
from llm_compact.core.types import CompactOptions


@pytest.mark.parametrize(
    "lang,cc,fn",
    [
        ("c", "gcc", "sample.c"),
        ("cpp", "g++", "sample.cpp"),
    ],
)
@pytest.mark.parametrize("lv", ["full", "light"])
@pytest.mark.parametrize("drop", [False, True])
def test_fixture_compiles_and_has_identical_stdout(tmp_path, lang, cc, fn, lv, drop):
    if not shutil.which(cc):
        pytest.skip(f"{cc} not installed")
    src = (Path(__file__).parents[1] / "examples" / fn).read_text()
    new = compact_cfamily(src, lang, CompactOptions(lv, drop))
    assert not new.fallback, new.warnings
    outs = []
    for n, s in enumerate((src, new.code)):
        f = tmp_path / f"{n}.{lang}"
        exe = tmp_path / f"program{n}"
        f.write_text(s)
        subprocess.run([cc, str(f), "-o", str(exe)], check=True, capture_output=True, timeout=30)
        run = subprocess.run([str(exe)], check=True, capture_output=True, timeout=5)
        outs.append(run.stdout)
    assert outs[0] == outs[1]


@pytest.mark.parametrize("lang,cc", [("c", "gcc"), ("cpp", "g++")])
@pytest.mark.parametrize("lv", ["full", "light"])
@pytest.mark.parametrize("drop", [False, True])
def test_multiline_macro_comment_keeps_a_compilable_program(tmp_path, lang, cc, lv, drop):
    if not shutil.which(cc):
        pytest.skip(f"{cc} not installed")
    src = (
        "#define VALUE /* explanation\n"
        "continued */ 1\n"
        "int main(void) { return VALUE - 1; }\n"
    )
    result = compact_cfamily(src, lang, CompactOptions(lv, drop))
    assert result.fallback and result.code == src
    for label, code in (("original", src), ("output", result.code)):
        path = tmp_path / f"{label}.{lang}"
        executable = tmp_path / label
        path.write_text(code, encoding="utf-8")
        subprocess.run(
            [cc, str(path), "-o", str(executable)],
            check=True, capture_output=True, timeout=30,
        )
        subprocess.run([str(executable)], check=True, capture_output=True, timeout=5)
