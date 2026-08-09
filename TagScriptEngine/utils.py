from __future__ import annotations

import builtins
import re
from inspect import isawaitable
from typing import Any, Awaitable, Callable, Optional, Tuple, TypeVar, Union

__all__: Tuple[str, ...] = ("truncate", "escape_content", "maybe_await")

T = TypeVar("T")

pattern: re.Pattern[str] = re.compile(r"(?<!\\)([{():|}])")


def _sub_match(match: re.Match) -> str:
    return "\\" + match[1]


def truncate(text: str, *, max: int = 2000, var: str = "...") -> str:
    """
    Truncate the given string to avoid hitting the character limit.

    Parameters
    ----------
    text
        The string to be truncated.
    max
        On what character length the string should be truncated.
    var
        The custom string used for trunication (defaults to '...').

    Returns
    -------
    str
        The truncated content.
    """
    if len(text) <= max:
        return text
    # Reserve room for `var` itself; hardcoding 3 only suits the default "...".
    truncated: str = text[: builtins.max(0, max - len(var))]
    return truncated + var


def escape_content(string: Optional[str]) -> Optional[str]:
    """
    Escapes given input to avoid tampering with engine/block behavior.

    Returns
    -------
    Optional[str]
        The escaped content, or ``None`` if ``None`` was passed.
    """
    if string is None:
        return None
    return pattern.sub(_sub_match, string)


async def maybe_await(
    func: Callable[..., Union[T, Awaitable[T]]], *args: Any, **kwargs: Any
) -> Union[T, Any]:
    """
    Await the given function if it is awaitable or call it synchronously.

    Returns
    -------
    Any
        The result of the awaitable function.
    """
    value: Union[T, Awaitable[T]] = func(*args, **kwargs)
    return await value if isawaitable(value) else value
