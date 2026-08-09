from typing import ClassVar, Dict, List, Optional, Tuple, Union

from ..interface import Block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("AllowedMentionsBlock",)


class AllowedMentionsBlock(Block):
    """
    The "allowed mentions" block attempts to enable mentioning of roles.
    Passing no parameter enables mentioning of **ALL** roles within the message
    content.

    - However passing a role name or ID to the block parameter allows mentioning of that specific role only.

    - Multiple role name or IDs can be included, separated by a comma ",".

    - By default, mentioning is only triggered if the execution author has "manage server" permissions.

    - However, using the "override" keyword as a payload allows mentioning to be triggered by **anyone**.

    .. note::

        This block only records the request under the ``allowed_mentions``
        response action. Whether it is honoured, and what permissions are
        required, is up to the host. The permissions described here are the
        policy used by the `Tags <https://github.com/cool-aid-man/cool-cogs>`_
        cog.

    .. important::

        **Creating** (or editing) a tag that uses this block requires the
        **Manage Server** permission - tag authors without it can't add
        the block.

    **Usage:** ``{allowedmentions(<role, None>):["override", None]}``

    **Aliases:** ``allowedmention, mentions``

    **Payload:** "override", None

    **Parameter:** role, None

    .. note::
        The payload is case-sensitive: only lowercase ``override`` is accepted. Any
        other payload - including ``Override`` - is declined, so the raw
        ``{allowedmentions:...}`` stays in the message.

    **Behaviour Reference:**

    +---------------------------------------+---------------+-------------------+---------------------------+
    | Syntax                                | Override-Flag | Scope             | Invoke-time trigger       |
    +=======================================+===============+===================+===========================+
    | ``{allowedmentions}``                 | No            | All roles         | Manage Server / Bot Owner |
    +---------------------------------------+---------------+-------------------+---------------------------+
    | ``{allowedmentions:override}``        | Yes           | All roles         | Anyone                    |
    +---------------------------------------+---------------+-------------------+---------------------------+
    | ``{allowedmentions(@role)}``          | No            | Specified role(s) | Manage Server / Bot Owner |
    +---------------------------------------+---------------+-------------------+---------------------------+
    | ``{allowedmentions(@role):override}`` | Yes           | Specified role(s) | Anyone                    |
    +---------------------------------------+---------------+-------------------+---------------------------+

    **Examples:** ::

        {allowedmentions}
        {allowedmentions:override}
        {allowedmention:override}
        {allowedmentions(@Admin, Moderator):override}
        {allowedmentions(763522431151112265, 812949167190048769)}
        {mentions(763522431151112265, 812949167190048769):override}
    """

    ACCEPTED_NAMES: ClassVar[Tuple[str, ...]] = ("allowedmentions", "allowedmention", "mentions")
    PAYLOADS: ClassVar[Tuple[str, ...]] = ("override",)

    @classmethod
    def will_accept(cls, ctx: Context) -> bool:
        if ctx.verb.payload and ctx.verb.payload not in cls.PAYLOADS:
            return False
        return super().will_accept(ctx)

    def process(self, ctx: Context) -> Optional[str]:
        actions: Optional[Dict[str, Union[bool, List[str]]]] = ctx.response.actions.get(
            "allowed_mentions"
        )
        if actions:
            # First one wins, but still consume it - None would echo the raw
            # block into the message.
            return ""
        if not (param := ctx.verb.parameter):
            ctx.response.actions["allowed_mentions"] = {
                "mentions": True,
                "override": True if ctx.verb.payload else False,
            }
            return ""
        ctx.response.actions["allowed_mentions"] = {
            "mentions": [r.strip() for r in param.split(",")],
            "override": True if ctx.verb.payload else False,
        }
        return ""
