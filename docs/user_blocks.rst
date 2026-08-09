======
Blocks
======

----------------------
Allowed Mentions Block
----------------------

.. autoclass:: TagScriptEngine.block.AllowedMentionsBlock

---------
All Block
---------

.. autoclass:: TagScriptEngine.block.AllBlock

---------
Any Block
---------

.. autoclass:: TagScriptEngine.block.AnyBlock

----------------
Assignment Block
----------------

.. autoclass:: TagScriptEngine.block.AssignmentBlock

---------------
Blacklist Block
---------------

.. autoclass:: TagScriptEngine.block.BlacklistBlock

-----------
Break Block
-----------

.. autoclass:: TagScriptEngine.block.BreakBlock

-------------
Command Block
-------------

.. autoclass:: TagScriptEngine.block.CommandBlock

---------------
Component Block
---------------

.. autoclass:: TagScriptEngine.block.ComponentBlock

.. rubric:: Rendering the layout

A Components V2 message cannot carry a normal ``content`` field, so the block
only *accumulates* a layout under the ``components_v2`` response action. The
host turns it into a view at send time:

.. code-block:: python

    layout = response.actions.get("components_v2")
    if layout:
        view = tse.build_components_v2_view(layout, leading_content=response.body)
        await channel.send(view=view)

.. autofunction:: TagScriptEngine.block.build_components_v2_view

---------------------------
In / Contains / Index Block
---------------------------

.. autoclass:: TagScriptEngine.block.PythonBlock

-----------
Count Block
-----------

.. autoclass:: TagScriptEngine.block.CountBlock

--------------
Cooldown Block
--------------

.. autoclass:: TagScriptEngine.block.CooldownBlock

-----------
Cycle Block
-----------

.. autoclass:: TagScriptEngine.block.CycleBlock

-----------
Embed Block
-----------

.. autoclass:: TagScriptEngine.block.EmbedBlock

-----------------
Fifty Fifty Block
-----------------

.. autoclass:: TagScriptEngine.block.FiftyFiftyBlock

--------
If Block
--------

.. autoclass:: TagScriptEngine.block.IfBlock

.. note::
    ``in``, ``contains`` and ``index`` are three aliases of one block -- see
    `In / Contains / Index Block`_ above.

----------
Join Block
----------

.. autoclass:: TagScriptEngine.block.JoinBlock

------------
Length Block
------------

.. autoclass:: TagScriptEngine.block.LengthBlock

----------
List Block
----------

.. autoclass:: TagScriptEngine.block.ListBlock

--------------------
Loose Variable Block
--------------------

.. autoclass:: TagScriptEngine.block.LooseVariableGetterBlock

-----------
Lower Block
-----------

.. autoclass:: TagScriptEngine.block.LowerBlock

----------
Math Block
----------

.. autoclass:: TagScriptEngine.block.MathBlock

-------------
Ordinal Block
-------------

.. autoclass:: TagScriptEngine.block.OrdinalBlock

--------------
Override Block
--------------

.. autoclass:: TagScriptEngine.block.OverrideBlock

------------
Random Block
------------

.. autoclass:: TagScriptEngine.block.RandomBlock

-----------
Range Block
-----------

.. autoclass:: TagScriptEngine.block.RangeBlock

--------------
Redirect Block
--------------

.. autoclass:: TagScriptEngine.block.RedirectBlock

-------------
Replace Block
-------------

.. autoclass:: TagScriptEngine.block.ReplaceBlock

-------------
Require Block
-------------

.. autoclass:: TagScriptEngine.block.RequireBlock

----------------------
ShortCutRedirect Block
----------------------

.. autoclass:: TagScriptEngine.block.ShortCutRedirectBlock

-----------
Sleep Block
-----------

.. autoclass:: TagScriptEngine.block.SleepBlock

----------
STRF Block
----------

.. autoclass:: TagScriptEngine.block.StrfBlock

----------
Stop Block
----------

.. autoclass:: TagScriptEngine.block.StopBlock

---------------------
Strict Variable Block
---------------------

.. autoclass:: TagScriptEngine.block.StrictVariableGetterBlock

--------------------
SubstringBlock Block
--------------------

.. autoclass:: TagScriptEngine.block.SubstringBlock

----------------
URL Encode Block
----------------

.. autoclass:: TagScriptEngine.block.URLEncodeBlock

-----------
Upper Block
-----------

.. autoclass:: TagScriptEngine.block.UpperBlock
