from __future__ import annotations

import random
from typing import Optional, Tuple, cast

from ..interface import verb_required_block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("RangeBlock",)


class RangeBlock(verb_required_block(True, payload=True)):  # type: ignore
    """
    The range block picks a random number from a range of numbers seperated by ``-``.
    The number range is inclusive, so it can pick the starting/ending number as well.
    Using the ``rangef`` block will pick a number to the tenth decimal place.

    **Seed:** the parameter is an optional *seed* - any text. Without a
    seed, a fresh random number is picked on every invocation. With a
    seed, the pick is **deterministic**: the same seed with the same
    range always returns the same number, every time, even across
    restarts. ``{range(5):10-20}`` will return the same number forever -
    that is by design, not a bug. Use a *variable* seed for results that
    are stable per-context but different across contexts, e.g.
    ``{range({user(id)}):1-100}`` gives each user their own fixed roll.
    Seeded rolls never affect other random blocks in the tag.

    **Usage:** ``{range([seed]):<lowest-highest>}``

    **Aliases:** ``rangef``

    **Payload:** number

    **Parameter:** seed, None

    **Examples:** ::

        Your lucky number is {range:10-30}!
        # Your lucky number is 14!
        # Your lucky number is 25!

        {=(height):{rangef:5-7}}
        I am guessing your height is {height}ft.
        # I am guessing your height is 5.3ft.
        # I am guessing your height is 6.5ft.

        {=(my_number):{range({user(id)}):1-100}}
        Your lucky number is {my_number}.
        # Your lucky number is 91.
        # Returns the same number for 776855156032798761, for the same range (1-100).

    .. note::
        The payload must be two numbers joined by ``-``. Anything else - a single
        number (``{range:10}``) or non-numeric bounds (``{range:a-b}``) - is
        declined, so the raw ``{range:...}`` stays in the message.
    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("rangef", "range")

    def process(self, ctx: Context) -> Optional[str]:
        try:
            spl = cast(str, ctx.verb.payload).split("-")
            # use a local RNG when seeded so the process-wide RNG is never reseeded
            rng = random.Random(ctx.verb.parameter) if ctx.verb.parameter is not None else random
            if cast(str, ctx.verb.declaration).lower() == "rangef":
                lower: float = float(spl[0])
                upper: float = float(spl[1])
                # Use `round(x * 10)` instead of `int(x)` to preserve decimal places (e.g. 5.5-7.5).
                low, high = sorted((round(lower * 10), round(upper * 10)))
                return str(rng.randint(low, high) / 10)
            else:
                # Use `sorted()` so reversed ranges (e.g. 10-1) work instead of failing `randint`.
                low, high = sorted((int(float(spl[0])), int(float(spl[1]))))
                return str(rng.randint(low, high))
        except Exception:
            return None
