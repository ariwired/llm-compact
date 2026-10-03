import ast
import io
import token
import tokenize
import warnings

from .types import CompactOptions, CoreResult


def ast_signature(src: str) -> str:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        node = ast.parse(src)
        compile(node, "<llm-compact-validation>", "exec")
    return ast.dump(node, include_attributes=False)


def _tokens(src: str) -> list[tokenize.TokenInfo]:
    toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    rows = src.splitlines(keepends=True)
    cum = [0]
    for row in rows:
        cum.append(cum[-1] + len(row))

    def at(p: tuple[int, int]) -> int:
        return cum[min(p[0] - 1, len(cum) - 1)] + p[1]

    res: list[tokenize.TokenInfo] = []
    n = 0
    opens = {getattr(token, "FSTRING_START", -1), getattr(token, "TSTRING_START", -2)}
    closes = {getattr(token, "FSTRING_END", -3), getattr(token, "TSTRING_END", -4)}
    while n < len(toks):
        tk = toks[n]
        if tk.type in opens:
            lvl = 1
            m = n + 1
            while m < len(toks) and lvl:
                lvl += int(toks[m].type in opens) - int(toks[m].type in closes)
                m += 1
            if lvl:
                raise tokenize.TokenError("Incomplete interpolated literal", tk.start)
            tail = toks[m - 1]
            res.append(
                tokenize.TokenInfo(
                    token.STRING,
                    src[at(tk.start) : at(tail.end)],
                    tk.start,
                    tail.end,
                    tk.line,
                )
            )
            n = m
        else:
            res.append(tk)
            n += 1
    return res


def _pair_signature(s: str) -> list[tuple[int, str]]:
    acc = []
    try:
        for k in tokenize.generate_tokens(io.StringIO(s).readline):
            if k.type not in (token.ENDMARKER, token.NEWLINE, token.NL, token.INDENT, token.DEDENT):
                acc.append((k.type, k.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return acc


def _space(left: tokenize.TokenInfo, right: tokenize.TokenInfo) -> bool:
    if left.type in (token.NAME, token.NUMBER) and right.type in (token.NAME, token.NUMBER):
        return True
    if left.type == token.STRING or right.type == token.STRING:
        return left.type in (token.NAME, token.NUMBER, token.STRING) and right.type in (
            token.NAME,
            token.NUMBER,
            token.STRING,
        )
    return _pair_signature(left.string + right.string) != [
        (left.type, left.string),
        (right.type, right.string),
    ]


def _emit(src: str, opt: CompactOptions) -> str:
    buf: list[str] = []
    prev: tokenize.TokenInfo | None = None
    ev: tokenize.TokenInfo | None = None
    bol = True
    lvl = 0
    rows = src.splitlines(keepends=True)
    for tk in _tokens(src):
        if tk.type in (token.ENDMARKER, token.ENCODING, token.INDENT, token.DEDENT):
            continue
        if tk.type == token.COMMENT and opt.strip_comments:
            hdr = (tk.start[0] == 1 and tk.string.startswith("#!")) or (
                tk.start[0] <= 2 and "coding" in tk.string
            )
            if not hdr:
                ev = tk
                continue
        if tk.type in (token.NEWLINE, token.NL):
            keep = (
                opt.level == "light"
                or tk.type == token.NEWLINE
                or (prev is not None and prev.type == token.COMMENT)
            )
            if keep and (opt.level == "light" or not bol):
                buf.append(tk.string)
                bol = True
                prev = None
            ev = tk
            continue

        joined = False
        
        if ev is not None and tk.start[0] > ev.end[0]:
            rest = rows[ev.end[0] - 1][ev.end[1] :]
            mid = "".join(rows[ev.end[0] : tk.start[0] - 1])
            lead = rows[tk.start[0] - 1][: tk.start[1]]
            span = rest + mid + lead
            if "\\\n" in span or "\\\r\n" in span:
                if opt.level == "light":
                    buf.append(span)
                    joined = True
        if bol:
            pre = rows[tk.start[0] - 1][: tk.start[1]]
            if lvl == 0 and not pre.strip():
                buf.append(pre)
            elif opt.level == "light" and not pre.strip():
                buf.append(pre)
        elif prev is not None and not joined and _space(prev, tk):
            buf.append(" ")
        buf.append(tk.string)
        bol = False
        prev = tk
        ev = tk
        if tk.type == token.OP:
            if tk.string in ("(", "[", "{"):
                lvl += 1
            elif tk.string in (")", "]", "}"):
                lvl -= 1
    return "".join(buf)


def compact_python(src: str, opt: CompactOptions) -> CoreResult:
    try:
        base = ast_signature(src)
    except (SyntaxError, ValueError, RecursionError) as err:
        return CoreResult(
            src,
            "not-validated",
            (f"Invalid, partial or incompatible Python for this version: {err}. Original kept.",),
            fallback=True,
        )
    try:
        new = _emit(src, opt)
        if ast_signature(new) != base:
            raise ValueError("the AST changed")
        if opt.level == "light" and new.count("\n") != src.count("\n"):
            raise ValueError("the line count changed in light mode")
    except (SyntaxError, ValueError, tokenize.TokenError, RecursionError) as err:
        return CoreResult(
            src,
            "python-ast",
            (f"Transformation rejected ({err}); original kept.",),
            fallback=True,
        )
    return CoreResult(new, "python-ast")
