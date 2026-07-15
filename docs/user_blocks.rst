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

--------------
Contains Block
--------------

The ``contains`` block strictly checks if the parameter is in the payload,
split by whitespace. This performs **exact** matching on whitespace-split words.

**Usage:** ``{contains(<string>):<payload>}``

**Examples:** ::

    {contains(mute):How does it feel to be muted?}
    # false
    {contains(muted?):How does it feel to be muted?}
    # true

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

--------
In Block
--------

The ``in`` block checks if the parameter string is anywhere in the payload as a substring.

**Usage:** ``{in(<string>):<payload>}``

**Examples:** ::

    {in(apple pie):banana pie apple pie and other pie}
    # true
    {in(mute):How does it feel to be muted?}
    # true

-----------
Index Block
-----------

The ``index`` block finds the location/index of the parameter in the payload,
split by whitespace. Returns ``-1`` if not found. Performs **exact** matching.

**Usage:** ``{index(<string>):<payload>}``

**Examples:** ::

    {index(food):I love to eat food everyone does}
    # 4
    {index(pie):I love to eat food}
    # -1

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
