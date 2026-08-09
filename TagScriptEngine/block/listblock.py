from __future__ import annotations

from typing import Optional, Tuple, cast

from ..interface import verb_required_block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("ListBlock",)


class ListBlock(verb_required_block(True, payload=True, parameter=True)):  # type: ignore
    """
    The list block returns the element in the payload that corresponds to the
    index value in the parameter. The block returns null if the index is out of bounds.

    List and Cycle blocks are another way to parse through a list of values in
    TagScript. They both strictly use either commas ``,`` or tildes ``~`` as the
    delimiters for the list placed in the block's payload. Use tildes when elements
    contain commas. These blocks only function in Tags.

    Lists use ``0`` as the index for the first element. Negative values allow
    for backward parsing. The block will return an error message if the value in
    the parameter is not a number.

    **Usage:** ``{list(<index>):<elem>,<elem2>,...}``

    **Aliases:** ``None``

    **Payload:** list of elements (comma or tilde separated)

    **Parameter:** index

    **Examples:** ::

        {list(0):Pizza~Burger~Pie~Chips~Lasagna}
        # Pizza

        {list(3):Pizza~Burger~Pie~Chips~Lasagna}
        # Chips

        {list(-1):Apple,Banana,Cherry}
        # Cherry

        {list(10):Apple,Banana,Cherry}
        # (returns null — index out of bounds)
    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("list",)

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

        try:
            return items[index]
        except IndexError:
            # Documented as returning null - render nothing rather than
            # echoing the raw block.
            return ""
