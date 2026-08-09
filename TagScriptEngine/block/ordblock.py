from __future__ import annotations

from typing import Optional, Tuple, cast

from ..interface import verb_required_block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("OrdinalBlock",)


def _ordinal(n: int) -> str:
    """Return the ordinal string for an integer (e.g. 1 -> '1st')."""
    if 11 <= abs(n) % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(abs(n) % 10, "th")
    return f"{n}{suffix}"


class OrdinalBlock(verb_required_block(True, payload=True)):  # type: ignore
    """
    The ordinal block returns the number in the payload with the correct ordinal
    abbreviation following it.

    **Usage:** ``{ordinal:<number>}``

    **Aliases:** ``ord``

    **Payload:** number

    **Parameter:** None

    **Examples:** ::

        {ordinal:101}
        # 101st

        {ord:22}
        # 22nd

        {ordinal:3}
        # 3rd

        {ord:456}
        # 456th

        {ordinal:11}
        # 11th

        {ord:12}
        # 12th
    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("ordinal", "ord")

    def process(self, ctx: Context) -> Optional[str]:
        raw = cast(str, ctx.verb.payload).strip()
        try:
            number = int(raw)
        except (ValueError, TypeError):
            return f'Ordinal Error: "{raw}" is not a number'
        return _ordinal(number)
