from .cfamily import compact_cfamily
from .python import compact_python
from .types import MAX_SOURCE_BYTES, SUPPORTED_LANGUAGES, CompactOptions, CoreResult

__all__ = ["SUPPORTED_LANGUAGES", "CompactOptions", "CoreResult", "compact"]


def compact(source: str, language: str, options: CompactOptions | None = None,) -> CoreResult:
    if not isinstance(source, str):
        raise TypeError("The code must be a string.")

    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")

    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise ValueError(f"The code exceeds {MAX_SOURCE_BYTES:,} bytes.")

    opt = options or CompactOptions()

    if language == "python":
        return compact_python(source, opt)

    return compact_cfamily(source, language, opt)