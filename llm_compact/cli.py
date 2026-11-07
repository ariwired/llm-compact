import argparse
import sys
from pathlib import Path

from .core import SUPPORTED_LANGUAGES, CompactOptions, compact
from .tokens import DEFAULT_ENCODINGS, compare_tokens

EXTENSIONS = {
    ".py": "python",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="llm-compact",
        description="Compact source code before sending it to an LLM and report the token saving.",
    )
    ap.add_argument("file", help="source file, or - to read standard input")
    ap.add_argument("-l", "--language", choices=SUPPORTED_LANGUAGES, help="default: from extension")
    ap.add_argument("--level", choices=("full", "light"), default="full")
    ap.add_argument("--strip-comments", action="store_true")
    ap.add_argument("-o", "--output", help="write the result here instead of standard output")
    ap.add_argument("--no-stats", action="store_true", help="do not print the token report")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.file == "-":
        source = sys.stdin.read()
        lang = args.language
    else:
        path = Path(args.file)
        source = path.read_text(encoding="utf-8")
        lang = args.language or EXTENSIONS.get(path.suffix.lower())
    if lang is None:
        print("error: could not infer the language, use --language", file=sys.stderr)
        return 2

    result = compact(source, lang, CompactOptions(args.level, args.strip_comments))
    if args.output:
        Path(args.output).write_text(result.code, encoding="utf-8")
    else:
        sys.stdout.write(result.code)

    if not args.no_stats:
        print(f"validation: {result.validation}", file=sys.stderr)
        for w in result.warnings:
            print(f"warning: {w}", file=sys.stderr)
        if result.fallback:
            print("original kept (no change was applied)", file=sys.stderr)
        for r in compare_tokens(source, result.code, DEFAULT_ENCODINGS):
            print(
                f"{r.encoding}: {r.before} -> {r.after} ({r.percent:.1f}% saved)", file=sys.stderr
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
