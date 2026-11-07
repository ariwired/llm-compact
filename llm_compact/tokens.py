from dataclasses import dataclass
from functools import lru_cache

DEFAULT_ENCODINGS = ("o200k_base", "cl100k_base")


@dataclass(frozen=True)
class TokenReport:
    encoding: str
    before: int
    after: int

    @property
    def saved(self) -> int:
        return self.before - self.after

    @property
    def percent(self) -> float:
        return 100.0 * self.saved / self.before if self.before else 0.0


@lru_cache(maxsize=None)
def _encoding(name: str):
    import tiktoken

    return tiktoken.get_encoding(name)


def count_tokens(text: str, encoding: str = DEFAULT_ENCODINGS[0]) -> int:
    return len(_encoding(encoding).encode(text, disallowed_special=()))


def compare_tokens(
    before: str, after: str, encodings: tuple[str, ...] = DEFAULT_ENCODINGS
) -> list[TokenReport]:
    return [
        TokenReport(name, count_tokens(before, name), count_tokens(after, name))
        for name in encodings
    ]
