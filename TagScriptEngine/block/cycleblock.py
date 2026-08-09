from __future__ import annotations

from typing import Optional, Tuple, cast

from ..interface import verb_required_block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("CycleBlock",)


class CycleBlock(verb_required_block(True, payload=True, parameter=True)):  # type: ignore
    """
    The cycle block returns the element in the payload that corresponds to the
    index value in the parameter. If the index is out of bounds, it loops around
    using modulo (``index % list_length``).

    List and Cycle blocks are another way to parse through a list of values in
    TagScript. They both strictly use either commas ``,`` or tildes ``~`` as the
    delimiters for the list placed in the block's payload. Use tildes when elements
    contain commas. These blocks only function in Tags.

    Cycles use ``0`` as the index for the first element. Negative values allow
    for backward parsing. The block will return an error message if the value in
    the parameter is not a number.

    **Usage:** ``{cycle(<index>):<elem>,<elem2>,...}``

    **Aliases:** ``None``

    **Payload:** list of elements (comma or tilde separated)

    **Parameter:** index

    **Examples:**

    .. code-block:: yaml

        {cycle(1):Cake,Candy,Chips,Cookies,Donut}
        # Candy

        {cycle(13):Cake,Candy,Chips,Cookies,Donut}
        # Cookies
        # (The list has 5 elements. 13 modulo 5 = 3. Index 3 is "Cookies".)

        {cycle(3):0,1,2}
        # 0
        # (3 modulo 3 = 0. Index 0 is "0".)

        Negative indices:
        {cycle(-1):Apple,Banana,Cherry}
        # Cherry

        {cycle(-69):Charlie,Aid,Bob,Dave,Eve,Phen,Steve,Tom,Wendy,Xavier}
        # Aid
        # (-69 modulo 10 = 1. Index 1 is "Aid".)

    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("cycle",)

    def process(self, ctx: Context) -> Optional[str]:
        try:
            index = int(cast(str, ctx.verb.parameter))
        except (ValueError, TypeError):
            return "Invalid index: parameter must be a number."

        payload = cast(str, ctx.verb.payload)
        if "~" in payload:
            items = payload.split("~")
        else:
            items = payload.split(",")

        return items[index % len(items)]
