from __future__ import annotations

import random
from typing import Optional, Tuple, cast

from ..interface import verb_required_block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("RandomBlock",)


class RandomBlock(verb_required_block(True, payload=True)):  # type: ignore
    """
    Pick a random item from a list of strings, split by either ``~``
    or ``,``.

    **Seed:** the parameter is an optional *seed* - any text. Without a
    seed, a fresh random pick is made on every invocation. With a seed,
    the pick is **deterministic**: the same seed with the same list
    always returns the same item, every time, even across restarts.
    ``{random(5):a,b,c}`` will return the same letter forever - that is
    by design, not a bug. Use a *variable* seed to get results that are
    stable per-context but different across contexts, e.g.
    ``{random({user(id)}):a,b,c}`` gives each user their own fixed pick.
    Seeded picks never affect other random blocks in the tag.

    **Usage:** ``{random([seed]):<list>}``

    **Aliases:** ``#, rand``

    **Payload:** list

    **Parameter:** seed, None

    **Examples:** ::

        {random:Carl,Harold,Josh} attempts to pick the lock!
        # Possible Outputs:
        # Josh attempts to pick the lock!
        # Carl attempts to pick the lock!
        # Harold attempts to pick the lock!

        {=(insults):You're so ugly that you went to the salon and it took 3 hours just to get an estimate.~I'll never forget the first time we met, although I'll keep trying.~You look like a before picture.}
        {=(insult):{#:{insults}}}
        {insult}
        # Assigns a random insult to the insult variable
    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("random", "#", "rand")

    def process(self, ctx: Context) -> Optional[str]:
        spl = []
        if "~" in (payload := cast(str, ctx.verb.payload)):
            spl = payload.split("~")
        else:
            spl = payload.split(",")
        # use a local RNG when seeded so the process-wide RNG is never reseeded
        rng = random.Random(ctx.verb.parameter) if ctx.verb.parameter is not None else random

        return rng.choice(spl)
