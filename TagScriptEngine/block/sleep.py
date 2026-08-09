from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from ..interface import Block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("SleepBlock",)


class SleepBlock(Block):
    """
    Pause a tag partway through, between the commands it runs.

    Like the :ref:`Command Block`, this block does not act while the tagscript is
    being parsed - the whole tagscript is read first, and the pause is recorded
    under the ``sleeps`` response action along with its position in the tag's
    command list.

    The host (e.g. a Red cog like `Tags <https://github.com/cool-aid-man/cool-cogs>`_)
    then replays commands and pauses in order, so a sleep placed between two
    command blocks delays the second one.

    .. important::
        - A sleep paces the tag's **command blocks**. Whether it can also delay
          the tag's *response* is up to the host: if the host posts its response
          **after** running the commands, a sleep written after the last command
          delays that response (and a tag with no commands simply answers later).
          If the host posts the response **first**, no sleep can move it, and a
          sleep with no command after it just idles.
        - The tag's **response** (text, embed, or components) is posted as a single
          message, either before or after all of the commands.
        - The **combined duration** of every sleep in one tag is capped at
          ``10 seconds``, and each sleep counts toward that budget.

    .. note::
        - For `Tags <https://github.com/cool-aid-man/cool-cogs>`_ cog, bot-owners
          can use the ``[p]tagset responsefirst`` command to toggle: whether the
          tag's **response** (text, embed, or components) lands **before** or
          **after** (the default) its **commands** (``{command}``/``{c}``).
        - For `Tags <https://github.com/cool-aid-man/cool-cogs>`_ cog,
          ``{command}``/``{c}`` blocks **always** run one after another
          (**sequentially**) in the order they appear in the tagscript.

    **Usage:** ``{sleep(<seconds>)}``

    **Aliases:** ``pause``, ``wait``

    **Payload:** seconds, if no parameter is given

    **Parameter:** seconds

    **Examples:**

    .. code-block:: yaml

        {c:ping}
        {sleep(3)}
        {c:help}
        # runs ping, waits 3 seconds, then runs help

        {sleep(1.5)}
        {c:ping}
        # waits 1.5 seconds, then runs ping

        {sleep:2}
        Sorry to keep you waiting!
        # the payload form works too
    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("sleep", "pause", "wait")

    def __init__(self, limit: float = 10.0) -> None:
        # Maximum total sleep time (in seconds) shared across all sleep blocks in a tag.
        self.limit: float = limit
        super().__init__()

    def process(self, ctx: Context) -> Optional[str]:
        raw = ctx.verb.parameter or ctx.verb.payload
        if not raw:
            # Consume it - None would echo the raw block into the message.
            return ""

        raw = raw.strip()
        try:
            seconds = float(raw)
        except ValueError:
            return f"Sleep Parse Error: `{raw}` is not a number."
        # nan/inf survive float(); nan poisons the budget check below, since
        # every comparison against it is False.
        if not math.isfinite(seconds):
            return f"Sleep Parse Error: `{raw}` is not a finite number."
        if seconds <= 0:
            return f"Sleep Parse Error: `{raw}` must be greater than 0."

        sleeps: List[Dict[str, Any]] = ctx.response.actions.setdefault("sleeps", [])
        if sum(sleep["seconds"] for sleep in sleeps) + seconds > self.limit:
            return f"`MAX SLEEP REACHED ({self.limit})`"

        # Blocks are processed in order, so the number of commands recorded so
        # far is exactly how many of them this sleep comes after.
        sleeps.append(
            {
                "index": len(ctx.response.actions.get("commands", [])),
                "seconds": seconds,
            }
        )
        return ""
