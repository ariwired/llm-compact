import re

from .common import needs_space, signature
from .types import CompactOptions, CoreResult, Token, UnsafeSourceError

SYMS = set(
    """>>>= <<= >>= >>> ... ->* <=> ??= ++ -- && || == != <= >= += -= *= /=
%= &= |= ^= << >> -> :: .* ?? ?. => .. ## <: :> <% %> %: %:%:""".split()
)
ENC = {"L", "u", "U", "u8"}
RAW = {"R", "LR", "uR", "UR", "u8R"}


def _ident_start(ch: str) -> bool:
    return bool(ch) and (ch.isalpha() or ch in "_$" or ord(ch) > 127)


def _ident_part(ch: str) -> bool:
    return bool(ch) and (_ident_start(ch) or ch.isdigit())


def _quoted(s: str, at: int, vb: bool = False) -> int:
    q = s[at]
    k = at + 1
    while k < len(s):
        if s[k] == q:
            if vb and s[k : k + 2] == q * 2:
                k += 2
                continue
            return k + 1
        if s[k] == "\\" and not vb:
            k += 2
            continue
        if s[k] in "\r\n" and not vb:
            raise UnsafeSourceError("Incomplete literal or unsupported line continuation.")
        k += 1
    raise UnsafeSourceError("Unterminated literal.")


def _raw(s: str, at: int, lang: str) -> int:
    if lang == "cpp":
        lp = s.find("(", at + 1)
        tag = s[at + 1 : lp]
        if lp < 0 or len(tag) > 16 or re.search(r"[\s)\\]", tag):
            raise UnsafeSourceError("Invalid C++ raw string.")
        stop = ")" + tag + '"'
        e = s.find(stop, lp + 1)
        if e < 0:
            raise UnsafeSourceError("Incomplete C++ raw string.")
        return e + len(stop)
    w = 0
    while at + w < len(s) and s[at + w] == '"':
        w += 1
    tag = '"' * (3 if lang == "java" else w)
    k = at + len(tag)
    while k < len(s):
        if lang == "java" and s[k] == "\\":
            k += 2
        elif s.startswith(tag, k):
            return k + len(tag)
        else:
            k += 1
    raise UnsafeSourceError("Incomplete multiline literal.")


def _number(s: str, at: int, lang: str) -> int:
    k = at
    hx = s[at : at + 2].lower() == "0x"
    while k < len(s):
        ch = s[k]
        if ch.isascii() and (ch.isalnum() or ch in "_."):
            ex = ch in ("eEpP" if lang in ("c", "cpp") else ("pP" if hx else "eE"))
            k += 1
            if ex and k < len(s) and s[k] in "+-":
                k += 1
        elif ch == "'" and lang in ("c", "cpp") and k + 1 < len(s) and s[k + 1].isalnum():
            k += 2
        else:
            break
    return k


def lex_cfamily(s: str, lang: str) -> list[Token]:
    toks: list[Token] = []
    p = 0
    bol = True
    while p < len(s):
        ch = s[p]
        if ch in "\r\n":
            bol = True
            p += 1
            continue
        if ch.isspace():
            p += 1
            continue
        b = p
        kd = "punct"
        if s.startswith("//", p):
            e = s.find("\n", p)
            p = len(s) if e < 0 else e
            kd = "comment"
        elif s.startswith("/*", p):
            e = s.find("*/", p + 2)
            if e < 0:
                raise UnsafeSourceError("Incomplete block comment.")
            p = e + 2
            kd = "comment"
        elif ch == "#" and bol and lang != "java":
            while True:
                e = s.find("\n", p)
                if e < 0:
                    p = len(s)
                    break
                ln = s[p:e].rstrip("\r")
                if lang != "csharp" and ln.endswith("\\"):
                    p = e + 1
                else:
                    p = e
                    break
            kd = "directive"
            if lang in ("c", "cpp") and "/*" in s[b:p]:
                raise UnsafeSourceError(
                    "C/C++ directives containing '/*' need a preprocessor; original kept."
                )
        elif lang == "csharp" and (
            s.startswith('$"', p)
            or s.startswith('$@"', p)
            or s.startswith('@$"', p)
            or re.match(r'\${2,}"', s[p:])
        ):
            raise UnsafeSourceError(
                "C# string interpolation needs a dedicated parser; original kept."
            )
        elif lang == "csharp" and s.startswith('@"', p):
            p = _quoted(s, p + 1, vb=True)
            kd = "string"
        elif lang == "csharp" and ch == "\\" and s[p + 1 : p + 2] in ("u", "U"):
            raise UnsafeSourceError(
                "C# Unicode escapes outside literals and comments need a dedicated lexer; "
                "original kept."
            )
        elif ch in "\"'":
            if ch == '"' and lang in ("java", "csharp") and s.startswith('"""', p):
                p = _raw(s, p, lang)
            else:
                p = _quoted(s, p)
            kd = "string"
        elif _ident_start(ch) or (lang == "csharp" and ch == "@"):
            p += 1
            while p < len(s) and _ident_part(s[p]):
                p += 1
            nm = s[b:p]
            kd = "word"
            if lang in ("c", "cpp") and p < len(s):
                if nm in ENC and s[p] in "\"'":
                    p = _quoted(s, p)
                    kd = "string"
                elif lang == "cpp" and nm in RAW and s[p] == '"':
                    p = _raw(s, p, "cpp")
                    kd = "string"
        elif ch.isdigit() or (ch == "." and p + 1 < len(s) and s[p + 1].isdigit()):
            p = _number(s, p, lang)
            kd = "word"
        else:
            w = next((n for n in (4, 3, 2) if s[p : p + n] in SYMS), 1)
            p += w
        if kd == "string" and lang == "cpp" and p < len(s) and _ident_start(s[p]):
            p += 1
            while p < len(s) and _ident_part(s[p]):
                p += 1
        toks.append(Token(kd, s[b:p], b, p))
        if kd == "comment":
            bol = bol or "\n" in s[b:p]
        else:
            bol = False
    return toks


def _newlines(s: str) -> str:
    return "".join(re.findall(r"\r\n|\n|\r", s))


def compact_cfamily(src: str, lang: str, opt: CompactOptions) -> CoreResult:
    try:
        if lang == "java" and re.search(r"\\u+[0-9a-fA-F]{4}", src):
            raise UnsafeSourceError("Java Unicode escapes are processed before the lexer.")
        if lang in ("c", "cpp") and ("__LINE__" in src or "source_location" in src):
            raise UnsafeSourceError("The code depends on its position in the file.")
        toks = lex_cfamily(src, lang)
        if lang in ("c", "cpp"):
            for tk in toks:
                if tk.kind == "punct" and tk.text in ("%:", "%:%:"):
                    raise UnsafeSourceError("Digraph directives need a preprocessor.")
                if tk.kind != "directive" and re.search(r"\\\r?\n|\\$", tk.text):
                    raise UnsafeSourceError("Line continuation outside a directive.")
                if (
                    tk.kind == "directive"
                    and re.match(r"#\s*define\b", tk.text)
                    and "#" in tk.text[1:]
                ):
                    raise UnsafeSourceError(
                        "Macro with stringification or concatenation needs a preprocessor."
                    )
            bare = src
            for tk in reversed(toks):
                if tk.kind == "directive":
                    bare = bare[: tk.start] + bare[tk.end :]
            if re.search(r"\\\r?\n|\?\?[/=()'!<>-]", bare):
                raise UnsafeSourceError("Line splicing or trigraphs are not supported.")

        live = [tk for tk in toks if not (opt.strip_comments and tk.kind == "comment")]
        buf: list[str] = []
        prev: Token | None = None
        pos = 0

        def lx(s: str) -> list[Token]:
            return lex_cfamily(s, lang)

        for tk in live:
            sp = src[pos : tk.start]
            join = ""
            if opt.level == "light" and ("\n" in sp or "\r" in sp):
                join = _newlines(sp)
            elif prev is not None:
                if (
                    prev.kind == "directive"
                    or tk.kind == "directive"
                    or (prev.kind == "comment" and prev.text.startswith("//"))
                ):
                    join = "\n"
                elif sp and needs_space(lx, prev, tk):
                    join = " "
            buf.append(join + tk.text)
            prev = tk
            pos = tk.end
        rest = src[pos:]
        if opt.level == "light":
            buf.append(_newlines(rest))
        elif prev is not None and prev.kind in ("directive", "comment") and "\n" in rest:
            buf.append("\n")
        new = "".join(buf)
        if signature(lx(new), opt.strip_comments) != signature(toks, opt.strip_comments):
            raise UnsafeSourceError("The lexical sequence changed after the transformation.")
        if opt.level == "light" and new.count("\n") != src.count("\n"):
            raise UnsafeSourceError("The line count changed in light mode.")
        msgs = [
            "Lexical check: does not prove semantic equivalence and does not replace the compiler."
        ]
        if any(tk.kind == "directive" for tk in toks):
            msgs.append("Directives kept as they are. External macros are not expanded.")
        return CoreResult(new, "lexical", tuple(msgs))
    except UnsafeSourceError as err:
        return CoreResult(src, "not-validated", (str(err),), fallback=True)
