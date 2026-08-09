from __future__ import annotations

from typing import Optional, Tuple

from ..adapter import StringAdapter
from ..interface import verb_required_block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("AssignmentBlock",)


class AssignmentBlock(verb_required_block(False, parameter=True)):  # type: ignore
    """
    Variables are useful for storing a value and referencing it later in a tag.
    Variables can be referenced using brackets as any other block.

    .. note::
        - Variables are not parsed by default. You must use the ``parse`` method to parse a variable.
        - They are one of the most versatile and powerful features of TagScript.
        - By default, a tag cannot store data between invocations. This is where ``variables`` come in.
        - They are the only way to **store** data. And later **retrieve** it within the same invocation.

    **Usage:** ``{=(<name>):<value>}``

    **Aliases:** ``assign, let, var``

    **Payload:** value

    **Parameter:** name

    **Examples:**

    .. code-block:: yaml

        {=(message1):Hi there! How are you?}
        {=(message2):It's a beautiful day today!}
        {=(message3):Did you know that TagScript is a powerful tool?}

        Now, call the variables by their names:
        {message1} # Hi there! How are you?
        {message2} # It's a beautiful day today!
        {message3} # Did you know that TagScript is a powerful tool?

        More example:
        {=(prefix):!}
        The prefix here is `{prefix}`.
        # The prefix here is `!`.

        {assign(day):Monday}
        {if({day}==Wednesday):It's Wednesday my dudes!|The day is {day}.}
        # The day is Monday.

    .. caution::
        **Don't name a variable after a block.** It looks like it works, but from
        then on that name sometimes gives you your text and sometimes runs the
        block - and you can't tell which by looking::

            {=(delete):Hi} {delete}     # Hi   - your text. The message is NOT
                                        #        deleted, the block never ran.
            {=(math):zzz} {math}        # zzz  - your text
            {=(math):zzz} {math:1+1}    # 2.0  - the block ran, not your text

        A few names can be set but **never** read back - you always get the
        block: ``50``, ``5050``, ``break``, ``short``, ``shortcircuit``, ``unix``.

        Pick a name no block uses - ``{=(may_delete):...}``, ``{=(total):...}`` -
        and none of this applies.

    .. raw:: html

        <hr>

    .. important:: How Argument Parsing Works - In Detail

    - A variable is essentially a string that can be treated as a sequence of elements (words, numbers, etc.) when accessed.
      These **elements** are split using ``delimiters`` (spaces by default) and are indexed sequentially starting from ``1``.
    - A delimiter is a sequence of one or more characters that are used to split a string into a sequence of elements.
    - Once a variable is assigned, its value can be referenced and ``parsed`` (split and indexed)
      to extract ``specific`` parts. Let's take a look at **how** it works.
    - Parsing out of bounds index will return the whole string.

    .. raw:: html

        <hr>

    .. rubric:: **Basic Argument Parsing**

    Example
        - "Coolaid is setting up the table. So, he grabbed - a cordless drill, some screws, a spirit level, and a pair of work gloves"

    - So, our ``argument`` or ``args`` in short, would be:

    .. code-block:: yaml

        {=(args):Coolaid is setting up the table. So, he grabbed - a cordless drill, some screws, a spirit level, and a pair of work gloves}

    .. note:: ``args`` is just a variable name, perhaps the most common name, but you can name it anything.

    - Since, the default delimiter is ``space``, so you can access the ``each element`` as follows:

    .. code-block:: yaml

        {args(1)}  -> Coolaid
        {args(2)}  -> is
        {args(3)}  -> setting
        {args(4)}  -> up
        {args(5)}  -> the
        {args(6)}  -> table.

        {args(31)} -> Would return the whole string since it doesn't exist (indexing 31st element is out of bounds).

    - ``0`` is special and returns the ``last`` element:

    .. code-block:: yaml

        {args(0)}  -> gloves

    - Negative indices allow you to access elements from the end of the sequence:

    .. code-block:: yaml

        {args(-1)}  -> work
        {args(-2)}  -> of
        {args(-3)}  -> pair
        {args(-4)}  -> a
        {args(-5)}  -> and
        {args(-6)}  -> level,

    .. rubric:: Prefix Range Access (``+n``)

    - Prefixing an index with ``+`` returns all elements from the start up to and including that position:

    .. code-block:: yaml

        {args(+3)}   -> Coolaid is setting
        {args(+7)}   -> Coolaid is setting up the table. So,
        {args(+13)}  -> Coolaid is setting up the table. So, he grabbed - a cordless drill,

    .. rubric:: Suffix Range Access (``n+``)

    - Suffixing an index with ``+`` returns all elements from that position (counting from the start) to the end:

    .. code-block:: yaml

        {args(3+)}   -> setting up the table. So, he grabbed - a cordless drill, some screws, a spirit level, and a pair of work gloves
        {args(7+)}   -> So, he grabbed - a cordless drill, some screws, a spirit level, and a pair of work gloves
        {args(13+)}  -> drill, some screws, a spirit level, and a pair of work gloves

    .. rubric:: Negative Range Access (``-n+``)

    - Appending ``+`` to an negative-index returns a range — all elements from that position to the end:
    - Negative indices are **first** resolved from the end of the sequence,
      then range access continues forward to the end.

    .. code-block:: yaml

        {args(-1+)}   -> work gloves # Since {args(0)} == gloves
        {args(-11+)}  -> drill, some screws, a spirit level, and a pair of work gloves

    .. tip::
        - ``+n``   → from start → n
        - ``n+``   → from n → end (index resolved first)
        - ``-n``   → nth element from end
        - ``-n+``  → nth element from end → then forward to end (index resolved first)

    .. raw:: html

        <hr>

    .. rubric:: **Advanced Argument Parsing**

    A **custom delimiter** can be passed as the payload to change how
    the value is split. The syntax is ``{variable(index):delimiter}``:

    .. code-block:: yaml

        # Using the same argument as before.
        {=(args):Coolaid is setting up the table. So, he grabbed - a cordless drill, some screws, a spirit level, and a pair of work gloves}

        1st Example:
        {args(1):.}  -> Coolaid is setting up the table
        {args(2):.}  -> So, he grabbed - a cordless drill, some screws, a spirit level, and a pair of work gloves
        {args(3):.}  -> Would return the entire string since there is no 3rd element.

        2nd Example:
        {args(1):-}  -> Coolaid is setting up the table. So, he grabbed
        {args(2):-}  -> a cordless drill, some screws, a spirit level, and a pair of work gloves

    .. note::
        - In the 1st example, the custom delimiter is ``.``, hence the string is split by ``.`` leaving 2 elements.
        - In the 2nd example, the custom delimiter is ``-``, hence the string is split by ``-`` leaving 2 elements.
        - Since in both the examples, there are ``2 elements``, so ``args(3)`` would  return the entire string.
          Because the index ``3rd`` element is out of bounds.

    .. rubric:: **Nested Variables**

    - Variables can be **nested** to perform multi-level parsing:

    .. code-block:: yaml

        {=(raw):A - B, C, D}
        {=(part):{raw(2):-}}

        # "{raw(2):-}" splits "raw" by "-" and returns the 2nd element -> "B, C, D" (1st element is "A")
        # Therefore, "part" == "B, C, D"

        {part(1):,}  -> B
        {part(2):,}  -> C

        Another Example:
        # What if you want to parse through the things that Coolaid grabbed?
        # If you look closely the "-" delimiter is placed conveniently to separate the items. So, we'll use it:

        {=(args):Coolaid is setting up the table. So, he grabbed - a cordless drill, some screws, a spirit level, and a pair of work gloves}
        {=(items):{args(2):-}}

        # "{args(2):-}" splits "args" by "-" and returns the 2nd element -> "a cordless drill, ... and a pair of work gloves"
        # Therefore, "items" == "a cordless drill, some screws, a spirit level, and a pair of work gloves"

        Items:
        {items(1):,}  -> a cordless drill
        {items(2):,}  -> some screws
        {items(3):,}  -> a spirit level
        {items(4):,}  -> and a pair of work gloves

    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("=", "assign", "let", "var")

    def process(self, ctx: Context) -> Optional[str]:
        if ctx.verb.parameter is None:
            return None
        payload = ctx.verb.payload if ctx.verb.payload is not None else ""
        ctx.response.variables[ctx.verb.parameter] = StringAdapter(payload)
        return ""
