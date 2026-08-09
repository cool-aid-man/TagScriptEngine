===================
Blocks and Adapters
===================

A **block** handles a whole verb -- ``{name(parameter):payload}``. An
**adapter** resolves an object behind a *variable* name, so ``{author(nick)}``
is the loose-variable block asking the ``author`` adapter for ``nick``.

Writing a block
---------------

Subclass :class:`~TagScriptEngine.Block`, set ``ACCEPTED_NAMES``, implement
``process``:

.. code-block:: python

    from typing import Optional, Tuple
    import TagScriptEngine as tse

    class ShoutBlock(tse.Block):
        ACCEPTED_NAMES: Tuple[str, ...] = ("shout",)

        def process(self, ctx: tse.Context) -> Optional[str]:
            if ctx.verb.payload is None:
                return None          # decline - see below
            return ctx.verb.payload.upper() + "!"

``{shout:hello}`` renders ``HELLO!``.

Returning ``None`` vs ``""``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is the single most important detail, and the easiest to get wrong.

- ``None`` means **"I did not handle this"**. The interpreter moves on to the
  next block that accepts the verb; if none do, the raw ``{shout:...}`` text is
  left in the output.
- ``""`` means **"handled, contributes no text"**. Use it for blocks whose work
  is a side effect recorded in ``ctx.response.actions``.

Returning ``None`` when you meant ``""`` is what makes raw tagscript leak into
a message. Returning ``""`` when you meant ``None`` silently swallows the block
so a same-named variable can never be read.

Requiring a parameter or payload
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:func:`~TagScriptEngine.verb_required_block` builds a base class that declines
the verb unless the parts you need are present, so ``process`` doesn't have to
check:

.. code-block:: python

    class ShoutBlock(tse.verb_required_block(True, payload=True)):
        ACCEPTED_NAMES: Tuple[str, ...] = ("shout",)

        def process(self, ctx: tse.Context) -> Optional[str]:
            return ctx.verb.payload.upper() + "!"

The first argument is ``implicit``: ``True`` requires a non-empty value,
``False`` also accepts an empty one (so ``{block()}`` is allowed).

Side-effect blocks
^^^^^^^^^^^^^^^^^^

Blocks cannot talk to Discord themselves. They record intent in
``ctx.response.actions`` and return ``""``; the host acts on it after
processing:

.. code-block:: python

    def process(self, ctx: tse.Context) -> Optional[str]:
        if "delete" in ctx.response.actions:
            return ""            # already set - consume, don't leak
        ctx.response.actions["delete"] = True
        return ""

Note the repeat guard returns ``""``, not ``None``.

Writing an adapter
------------------

Subclass :class:`~TagScriptEngine.SimpleAdapter` and fill ``_attributes`` /
``_methods``. You normally do **not** override ``get_value``:

.. code-block:: python

    class PointsAdapter(tse.SimpleAdapter):
        def update_attributes(self) -> None:
            self._attributes.update({
                "total": self.object.total,
                "rank": self.object.rank,
            })

        def update_methods(self) -> None:
            # Called only when asked for, so expensive lookups stay lazy.
            self._methods["percentile"] = self.compute_percentile

``{points(total)}`` resolves the attribute; ``{points}`` alone calls
``default_value()``, which defaults to ``str(self.object)``.

Attributes that don't exist resolve to an **empty string**, so a typo or a
missing value renders as nothing rather than leaking the raw block.

Hooks worth knowing:

``default_value()``
    What a bare ``{name}`` returns.
``resolve(parameter)``
    Look up one name. Override to gate or lazily compute particular ones --
    :class:`~TagScriptEngine.RedBotAdapter` uses it to hide owner-only stats.
``defaults=``
    Passed to ``__init__``, seeded *before* ``update_attributes()`` so a
    subclass can override them.

Escaping
^^^^^^^^

An attribute may return a ``(value, escape)`` tuple; when ``escape`` is true
the value is passed through :func:`~TagScriptEngine.escape_content` so braces
in it can't be parsed as further blocks.

Registering
-----------

.. code-block:: python

    interpreter = tse.Interpreter([
        ShoutBlock(),
        # ... every other real block ...
        tse.ShortCutRedirectBlock("args"),
        tse.LooseVariableGetterBlock(),      # must be last
    ])

.. seealso::
    :doc:`the_interpreter` for why that order matters, and :doc:`interface` for
    the full API.
