===============
Getting Started
===============

Install
-------

.. code-block:: bash

    pip install AdvancedTagScript

``orjson`` is used for faster embed JSON parsing when available:

.. code-block:: bash

    pip install AdvancedTagScript[all]

Your first interpreter
----------------------

An interpreter is a list of blocks. Nothing is registered by default, so you
choose exactly which features your users get:

.. code-block:: python

    import TagScriptEngine as tse

    interpreter = tse.Interpreter([
        tse.MathBlock(),
        tse.RandomBlock(),
        tse.StrfBlock(),
    ])

    response = interpreter.process("{random:hi,hello} - {math:2^8}")
    print(response.body)      # "hello - 256.0"

Giving tags some context
------------------------

Most useful tags need data. Pass adapters as ``seed_variables``:

.. code-block:: python

    interpreter = tse.Interpreter([
        tse.MathBlock(),
        tse.LooseVariableGetterBlock(),   # resolves seeded names - keep last
    ])

    seed = {"name": tse.StringAdapter("Coolaid")}
    interpreter.process("Hello {name}!", seed).body    # "Hello Coolaid!"

.. important::
    Anything a *user* typed should be seeded with ``escape=True``
    (``tse.StringAdapter(args, escape=True)``). Unescaped brackets in user input
    can corrupt the block that contains them.

Handling actions
----------------

Blocks that do more than produce text write to ``response.actions`` and return
an empty string. The host decides what to do with them:

.. code-block:: python

    interpreter = tse.Interpreter([tse.EmbedBlock(), tse.RedirectBlock()])
    response = interpreter.process('{embed({"title":"Rules"})}{redirect(dm)}')

    response.body                    # ""
    response.actions["embed"]        # a discord.Embed
    response.actions["target"]       # "dm"

Sending that embed, honouring the redirect, running ``{command}`` blocks -- all
of that is yours to implement. The engine never touches Discord.

Protecting your host
--------------------

Two things are worth doing from day one:

.. code-block:: python

    response = interpreter.process(script, charlimit=100_000)

``charlimit`` bounds how much text processing may build. Without it a short
script can still produce megabytes and block your event loop.

And cap the blocks that cost you something -- ``CommandBlock(limit=3)``,
``SleepBlock(limit=10.0)`` -- since anyone who can invoke a tag triggers every
one of them.

Where to next
-------------

- :doc:`the_interpreter` -- sync vs async, block ordering, the Response object.
- :doc:`blocks_and_adapters` -- writing your own.
- :doc:`user_blocks` -- what ships in the box.

A full production implementation lives in the
`Tags cog <https://github.com/cool-aid-man/cool-cogs/blob/main/tags/mixins/processor.py>`_.
