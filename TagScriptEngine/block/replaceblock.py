from __future__ import annotations

from typing import Optional, Tuple, cast

from ..interface import verb_required_block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("ReplaceBlock", "PythonBlock")


class ReplaceBlock(verb_required_block(True, payload=True, parameter=True)):  # type: ignore
    """
    The replace block will replace specific characters in a string.
    The parameter should split by a ``,``, containing the characters to find
    before the command and the replacements after.

    **Usage:** ``{replace(<original,new>):<message>}``

    **Aliases:** ``None``

    **Payload:** message

    **Parameter:** original, new

    **Examples:** ::

        {replace(o,i):welcome to the server}
        # welcime ti the server

        {replace(1,6):{args}}
        # if {args} is 1637812
        # 6637862

        {replace(, ):Test}
        # T e s t
    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("replace",)

    def process(self, ctx: Context) -> Optional[str]:
        try:
            before, after = cast(str, ctx.verb.parameter).split(",", 1)
        except ValueError:
            return "Replace Error: parameter must be <original>,<new>"

        return cast(str, ctx.verb.payload).replace(before, after)


class PythonBlock(verb_required_block(True, parameter=True)):  # type: ignore
    """
    The in block serves three different purposes depending on the alias that is used.

    The ``in`` alias checks if the parameter is anywhere in the payload.

    The ``contains`` alias strictly checks if the parameter is in the payload, split by whitespace.

    The ``index`` alias finds the location/index of the parameter in the payload, split by whitespace.
    If the parameter string is not found in the payload, it returns -1.

    .. note::

        Both ``contains`` and ``index`` perform **exact** matching on whitespace-split words.
        For example, ``food`` will **not** match ``food.`` (with trailing punctuation).

        An **empty payload** is answered, not declined - ``{contains(x):}`` is
        ``false`` and ``{index(x):}`` is ``-1``. This matters when the payload is
        a variable that resolved to nothing, e.g. ``{contains(|):{args(7+)}}``
        with fewer than 7 arguments. Omitting the payload entirely
        (``{contains(x)}``) is still not a usable form and is left alone.

    **Usage:** ``{in(<string>):<payload>}``

    **Aliases:** ``in``, ``contains``, ``index``

    **Payload:** payload

    **Parameter:** string

    **Examples:** ::

        {in(apple pie):banana pie apple pie and other pie}
        # true
        {in(mute):How does it feel to be muted?}
        # true
        {in(a):How does it feel to be muted?}
        # false

        {contains(mute):How does it feel to be muted?}
        # false
        {contains(muted?):How does it feel to be muted?}
        # true

        {index(food):I love to eat food. everyone does.}
        # -1 # because of the period. "food" != "food."
        {index(food):I love to eat food everyone does}
        # 4 # because "food" is the 4th word in the payload
        {index(love):I love to eat food}
        # 1 # because "love" is the 2nd word in the payload
        {index(pie):I love to eat food}
        # -1 # because "pie" is not in the payload
    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("in", "contains", "index")

    @classmethod
    def will_accept(cls, ctx: Context) -> bool:
        # Allow empty payloads: checking against `""` is a valid evaluation.
        # Declining would leak raw block text if a payload variable resolves to empty.
        return ctx.verb.payload is not None and super().will_accept(ctx)

    def process(self, ctx: Context) -> str:
        dec: str = cast(str, ctx.verb.declaration).lower()
        if dec == "contains":
            return str(bool(ctx.verb.parameter in cast(str, ctx.verb.payload).split())).lower()
        elif dec == "in":
            return str(bool(cast(str, ctx.verb.parameter) in cast(str, ctx.verb.payload))).lower()
        else:
            try:
                return str(
                    cast(str, ctx.verb.payload)
                    .strip()
                    .split()
                    .index(cast(str, ctx.verb.parameter))
                )
            except ValueError:
                return "-1"
