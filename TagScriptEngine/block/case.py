from __future__ import annotations

from typing import Optional, Tuple

from ..interface import Block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("UpperBlock", "LowerBlock")


class UpperBlock(Block):
    """Converts the given text to uppercase.

    **Usage:**  ``{upper([text])}``

    **Aliases:**  ``uppercase, upper``

    **Payload:**  None

    **Parameter:**  text

    **Examples:**  ::

        The text is {upper(ThIs Is A TeXt)}!
        # The text is THIS IS A TEXT!

        {=(args):Hello World}
        You have entered {upper({args})}!
        # You have entered HELLO WORLD!
    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("upper", "uppercase")

    def process(self, ctx: Context) -> Optional[str]:
        # Consume bare `{upper}` to prevent raw block leaks; variable name collisions are discouraged anyway.
        if ctx.verb.parameter is None:
            return ""
        return ctx.verb.parameter.upper()


class LowerBlock(Block):
    """Converts the given text to lowercase.

    **Usage:**  ``{lower([text])}``

    **Aliases:**  ``lowercase, lower``

    **Payload:**  None

    **Parameter:**  text

    **Examples:**  ::

        The text is {lower(ThIs Is A TeXt)}!
        # The text is this is a text!

        {=(args):HELLO WORLD}
        You have entered {lower({args})}!
        # You have entered hello world!
    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("lower", "lowercase")

    def process(self, ctx: Context) -> Optional[str]:
        # See UpperBlock.
        if ctx.verb.parameter is None:
            return ""
        return ctx.verb.parameter.lower()
