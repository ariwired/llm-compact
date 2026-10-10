from dataclasses import dataclass
from typing import Literal

Language = Literal["python", "java", "c", "cpp", "csharp"]
Level = Literal["full", "light"]
SUPPORTED_LANGUAGES: tuple[Language, ...] = ("python", "java", "c", "cpp", "csharp")
MAX_SOURCE_BYTES = 1_000_000


@dataclass(frozen=True)
class CompactOptions:
    level: Level = "full"
    strip_comments: bool = False

    def __post_init__(self) -> None:
        if self.level not in ("full", "light"):
            raise ValueError("Level must be 'full' or 'light'.")
        if not isinstance(self.strip_comments, bool):
            raise ValueError("strip_comments must be a boolean.")


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class CoreResult:
    code: str
    validation: Literal["python-ast", "lexical", "not-validated"]
    warnings: tuple[str, ...] = ()
    fallback: bool = False


class UnsafeSourceError(ValueError):
    pass
