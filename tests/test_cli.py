import pytest

from llm_compact.cli import main


def test_cli_writes_compacted_file_and_reports_tokens(tmp_path, capsys):
    src = tmp_path / "a.c"
    out = tmp_path / "b.c"
    src.write_text("int   main( void )\n{\n    return 0;\n}\n")
    assert main([str(src), "-o", str(out)]) == 0
    assert out.read_text() == "int main(void){return 0;}"
    err = capsys.readouterr().err
    assert "validation: lexical" in err and "o200k_base:" in err and "saved" in err


def test_cli_unknown_extension_needs_language(tmp_path, capsys):
    f = tmp_path / "a.txt"
    f.write_text("x")
    assert main([str(f)]) == 2
    assert "--language" in capsys.readouterr().err


def test_cli_reads_stdin(monkeypatch, capsys):
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO("x  =  1\n"))
    assert main(["-", "-l", "python", "--no-stats"]) == 0
    assert capsys.readouterr().out == "x=1\n"


def test_cli_rejects_unknown_language():
    with pytest.raises(SystemExit):
        main(["a.c", "-l", "rust"])
