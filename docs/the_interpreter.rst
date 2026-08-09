===============
The Interpreter
===============

The interpreter turns a TagScript string into a :class:`~TagScriptEngine.Response`.

Choosing one
------------

:class:`~TagScriptEngine.Interpreter` is synchronous. Use it when every block
you register is synchronous.

:class:`~TagScriptEngine.AsyncInterpreter` is a subclass that awaits blocks
returning awaitables. Synchronous blocks still work unchanged. Its
``process`` is a coroutine.

Passing a synchronous ``Interpreter`` a block whose ``process`` returns a
coroutine raises :class:`~TagScriptEngine.ProcessError`, rather than silently
printing a coroutine repr into the output.

Basic use
---------

.. code-block:: python

    import TagScriptEngine as tse

    interpreter = tse.Interpreter([tse.MathBlock(), tse.RandomBlock()])
    response = interpreter.process("{math:1+1} and {random:a,b,c}")
    print(response.body)

Seeding variables
-----------------

``seed_variables`` maps names to adapters, which blocks such as
:class:`~TagScriptEngine.LooseVariableGetterBlock` resolve:

.. code-block:: python

    seed = {"args": tse.StringAdapter("hello world", escape=True)}
    interpreter.process("{args(1)}", seed)   # -> "hello"

.. important::
    Pass ``escape=True`` for anything a user typed. The interpreter re-reads a
    block's text after its inner blocks are substituted, so an unescaped ``(``
    or ``)`` in user input can corrupt the *enclosing* block and leak the raw
    tagscript into your output.

Limiting the workload
---------------------

``charlimit`` caps the total characters produced while processing. Without it a
small script can still build megabytes -- ``{=(a):<5000 chars>}`` followed by a
few hundred ``{a}`` is only a couple of thousand characters of source.
Exceeding the cap raises :class:`~TagScriptEngine.WorkloadExceededError`.

.. code-block:: python

    try:
        response = interpreter.process(script, charlimit=100_000)
    except tse.WorkloadExceededError:
        ...

Block ordering matters
----------------------

Blocks are tried in list order and the first to return a non-``None`` value
wins. :class:`~TagScriptEngine.LooseVariableGetterBlock` accepts *every*
declaration, so it must be registered **last** -- anything after it loses to a
variable of the same name.

:class:`~TagScriptEngine.ShortCutRedirectBlock` rewrites ``{1}`` into a lookup
on a named variable and then defers, so it belongs immediately before the
getters.

The Response
------------

- ``body`` -- the processed text.
- ``actions`` -- a dict blocks write to for the host to act on afterwards
  (``commands``, ``embed``, ``delete``, ``sleeps``, ``components_v2`` ...).
- ``variables`` -- the adapters available during processing.
- ``extra_kwargs`` -- anything extra passed to ``process``.

A block that does something outside the text (running a command, setting an
embed) records it in ``actions`` and returns ``""``. Acting on those is the
host's job.

.. seealso::
    :doc:`interpreter` for the full API reference.
