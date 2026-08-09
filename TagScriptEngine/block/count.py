from __future__ import annotations

from typing import Optional, Tuple, cast

from ..interface import verb_required_block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("CountBlock", "LengthBlock")


class CountBlock(verb_required_block(True, payload=True)):  # type: ignore
    """
    The count block counts occurrences of a substring within a message.
    The search is case sensitive and counts **non-overlapping** matches, so
    ``{count(aa):aaaa}`` returns ``2``, not ``3``.

    A payload (the message to search in) is **required**. Optionally,
    pass the text to search for as a parameter. If no parameter is
    provided, the block counts the number of words in the message
    (spaces + 1).

    **Usage:** ``{count([text]):<message>}``

    **Aliases:** ``None``

    **Payload:** ``message`` (required)

    **Parameter:** ``text`` (optional, the substring to count)

    **Examples:** ::

        {count(Tag):TagScriptEngine}
        # 1

        {count(Tag):Tag Script Engine TagScriptEngine}
        # 2

        {count:hello world}
        # 2 (word count: 1 space + 1)

        {count(123)}
        # Returns {count(123)} — rejected because no payload was provided
    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("count",)

    def process(self, ctx: Context) -> Optional[str]:
        if ctx.verb.parameter:
            payload: str = cast(str, ctx.verb.payload)
            return str(payload.count(ctx.verb.parameter))
        return str(cast(str, ctx.verb.payload).count(" ") + 1)


class LengthBlock(verb_required_block(True, parameter=True)):  # type: ignore
    """
    The length block returns the character count of the given text.

    **Usage:** ``{length(<text>)}``

    **Aliases:** ``len``

    **Payload:** ``None``

    **Parameter:** ``text`` (required)

    **Examples:** ::

        {len(TagScriptEngine)}
        # 15

        {len(hello world)}
        # 11
    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("length", "len")

    def process(self, ctx: Context) -> Optional[str]:
        # verb_required_block(True, parameter=True) guarantees a truthy
        # parameter, so there is no "-1" case to fall back to.
        return str(len(cast(str, ctx.verb.parameter)))
