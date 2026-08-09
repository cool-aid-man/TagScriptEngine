from __future__ import annotations

from typing import Optional, Tuple, cast

from ..interface import verb_required_block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("JoinBlock",)


class JoinBlock(verb_required_block(False, payload=True, parameter=True)):  # type: ignore
    """
    The join block replaces every space in the payload with the parameter string.
    These blocks only function in Tags.

    The parameter must be set, even if it is an empty string.
    Cannot use the symbols ``)`` or ``}`` as parameters.

    **Usage:** ``{join(<string>):<payload>}``

    **Aliases:** ``None``

    **Payload:** payload

    **Parameter:** string (required, can be empty)

    **Examples:** ::

        {join(_):hello friends}
        # hello_friends

        {join():an example sentence}
        # anexamplesentence

        {join(-):cool aid man}
        # cool-aid-man
    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("join",)

    def process(self, ctx: Context) -> Optional[str]:
        return cast(str, ctx.verb.payload).replace(" ", cast(str, ctx.verb.parameter))
