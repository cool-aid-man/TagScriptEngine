from __future__ import annotations

from typing import Optional, Tuple, cast

from ..interface import verb_required_block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("SubstringBlock",)


class SubstringBlock(verb_required_block(True, parameter=True)):  # type: ignore
    """
    The substring block extracts a specific portion of the payload text using ``0``-based indexing.
    It supports both a single starting index and a specific range of characters.

    .. important::

        **Behavior:**

        - If a single ``index`` is provided, it returns all characters from that position to the end
          (counting from the start).
        - From ``nth`` position (index) to end.

        - If a range is provided using ``-`` (e.g., ``0-5``), it returns the characters from
          the ``start`` index to the ``end`` index but **without** including the ``end`` th index.

    **Usage:** ``{substr(<start[-end]>):<text>}``

    **Aliases:** ``substring``

    **Payload:** text (to extract from)

    **Parameter:** A single integer for start, or a hyphenated range (``start-end``).

    **Examples:**

    .. code-block:: yaml

        {substr(7):Hello, World!}
        # World!
        Explanation:
        # - Skips up to index 7 ("Hello, ") and starts at "W" (index 7). As 7th index is inclusive.

        {substr(1-4):Hello}
        # ell
        Explanation:
        # - Skips the first character ("H" at index 0) and starts at "e" (index 1).
        # - Stops at index 4 (exclusive), so it doesn't include "o" (index 4).

        {substr(7-12):Hello, World!}
        # World

        {substr(7):TagScript is powerful}
        # pt is powerful
        Explanation:
        # - Skips up to index 7 ("TagScri") and starts at "pt" (index 7).
        # - Indexing: T(0)a(1)g(2)S(3)c(4)r(5)i(6)p(7). So at 7 it starts at pt.

    .. note::

        - For Single Index: Starting index is ``inclusive`` to the end of the string.
        - For Range: Starting index is ``inclusive``, while the ending index is ``exclusive``.
        - Negative indices are not supported. A negative index (``{substr(-3):Hello}``)
          is declined, so the raw ``{substr(...)}`` stays in the message.

    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("substr", "substring")

    def process(self, ctx: Context) -> Optional[str]:
        try:
            if "-" not in cast(str, ctx.verb.parameter):
                return cast(str, ctx.verb.payload)[int(float(cast(str, ctx.verb.parameter))) :]

            spl = cast(str, ctx.verb.parameter).split("-")
            start = int(float(spl[0]))
            end = int(float(spl[1]))
            return cast(str, ctx.verb.payload)[start:end]
        except Exception:
            return
