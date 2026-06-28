from __future__ import annotations

import datetime
from typing import Any, Optional, Tuple, cast

import discord

from ..verb import Verb
from ..interface import SimpleAdapter
from ..utils import escape_content

try:
    import redbot  # noqa: F401
except ModuleNotFoundError:
    _has_redbot = False
else:
    _has_redbot = True

    from redbot.core.bot import Red
    from redbot.core.commands import Command
    from redbot.core.utils.chat_formatting import humanize_number, humanize_list
    

__all__: Tuple[str, ...] = ("RedCommandAdapter", "RedBotAdapter")


class RedCommandAdapter(SimpleAdapter["Command"]):
    """
    The ``{commandinfo}`` block reads a command's metadata and returns it as
    text. Unlike the :ref:`Command Block`, it does **not** run the command.
    See the attribute list below.

    **Usage:** ``{commandinfo([attribute]):<command>}``

    **Payload:** command (supplied by the block)

    **Parameter:** attribute, None

    Attributes
    ----------
    name
        The command's name.
    qualified_name
        The command's full name, including any parent groups.
    cog_name
        The name of the cog the command belongs to.
    description
        The command's description. Most commands leave this unset, so it falls
        back to the help text's first line (``short_doc``) when empty.
    short_doc
        The first line of the command's help text.
    help
        The command's full help text (its docstring).
    aliases
        The command's aliases, or ``None`` if it has none.
    signature
        The command's argument signature. Empty for commands that take no
        arguments.
    """

    def __init__(self, base: Command, *, signature: Optional[str] = None) -> None:
        if not _has_redbot:
            raise ImportError(
                "A Red-DiscordBot instance is required to use this.", name="redbot"
            )
        self.signature: Optional[str] = signature
        super().__init__(base=base)

    def update_attributes(self) -> None:
        command: Command = self.object
        # As no command sets ``description`` so the docstring goes to ``help`` (and ``short_doc`` is its first line).
        short_doc: str = getattr(command, "short_doc", "") or ""
        description: str = getattr(command, "description", "") or short_doc
        self._attributes.update(
            {
                "name": command.name,
                "cog_name": getattr(command, "cog_name", None),
                "description": description,
                "short_doc": short_doc,
                "help": getattr(command, "help", None),
                "aliases": humanize_list(list(getattr(command, "aliases", []))) or "None",
                "qualified_name": command.qualified_name,
                "signature": self.signature,
            }
        )

    def get_value(self, ctx: Verb) -> str:
        should_escape: bool = False
        if ctx.parameter is None:
            return_value: str = self.object.qualified_name
        else:
            try:
                value: Any = self._attributes[ctx.parameter]
            except KeyError:
                return  # type: ignore
            if isinstance(value, tuple):
                value, should_escape = value
            return_value: str = str(value) if value is not None else None  # type: ignore
        return escape_content(return_value) if should_escape else return_value


class RedBotAdapter(SimpleAdapter["Red"]):
    """
    The ``{bot}`` block with no parameters returns the bot's name & discriminator,
    but passing the attributes listed below to the block payload will return that attribute instead.

    **Usage:** ``{bot([attribute])}``

    **Payload:** None

    **Parameter:** attribute, None

    Attributes
    ----------
    id
        The bot's Discord ID.
    name
        The bot's username.
    discriminator
        The bot's discriminator.
    nick
        The bot's global display name. This is not a per-server nickname: the
        bot user has no guild context here, so a server-specific nick is not
        available through this block.
    created_at
        The bot's creation date.
    timestamp
        The bot's creation date as a UTC timestamp.
    mention
        A formatted text that pings the bot.
    avatar
        A link to the bot's avatar, which can be used in embeds.
    verified
        If the bot is verified or not.
    shard_count (*)
        The bot's total shard count.
    servers (*)
        Total server/guild count of the bot.
    channels (*)
        Total number of channels visible to the bot.
    visible_users (*)
        Total number of users visible to the bot.
    total_users (*)
        The bot's total user count.
    unique_users (*)
        The bot's unique user count.
    percentage_chunked (*)
        Percentage of the bot's members that are cached/chunked (rounded to two
        decimals); ``0`` when no member counts are available.

    Attributes marked ``(*)`` are owner-only and return nothing for other users.
    """
 
    # Bot-Owner Only attributes since these require iterating the whole guild/member cache.
    OWNER_ATTRIBUTES: Tuple[str, ...] = (
        "shard_count",
        "servers",
        "channels",
        "visible_users",
        "total_users",
        "unique_users",
        "percentage_chunked",
    )

    def __init__(self, base: Red, *, owner: bool = True) -> None:
        if not _has_redbot:
            raise ImportError("A Red-DiscordBot instance is required to use this.")
        self.is_owner: bool = owner
        super().__init__(base=base)

    def update_attributes(self) -> None:
        self.user: discord.ClientUser = cast(discord.ClientUser, self.object.user)
        created_at: datetime.datetime = getattr(
            self.user, "created_at", None
        ) or discord.utils.snowflake_time(self.user.id)
        self._attributes.update(
            {
                "id": self.user.id,
                "name": self.user.name,
                "discriminator": self.user.discriminator,
                "nick": self.user.display_name,
                "mention": self.user.mention,
                "avatar": (self.user.display_avatar.url, False),
                "created_at": created_at,
                "timestamp": int(created_at.timestamp()),
                "verified": self.user.verified,
            }
        )

    def _compute_owner_attribute(self, name: str) -> Any:
        bot: Red = self.object
        if name == "shard_count":
            # ``shard_count`` is None on an unsharded bot.
            return humanize_number(bot.shard_count or 1)
        if name == "servers":
            return humanize_number(len(bot.guilds))
        if name == "channels":
            return humanize_number(sum(len(g.channels) for g in bot.guilds))
        if name == "unique_users":
            return humanize_number(len(bot.users))
        visible_users: int = sum(len(g.members) for g in bot.guilds)
        if name == "visible_users":
            return humanize_number(visible_users)
        total_users: int = sum(g.member_count or 0 for g in bot.guilds)
        if name == "total_users":
            return humanize_number(total_users)
        if name == "percentage_chunked":
            # Guard against a bot in no guilds / with no counted members.
            return round(visible_users / total_users * 100, 2) if total_users else 0
        return None

    def get_value(self, ctx: Verb) -> str:
        should_escape: bool = False
        if ctx.parameter is None:
            return_value: str = "{0.name}#{0.discriminator}".format(self.user)
        else:
            parameter: str = ctx.parameter
            if parameter in self.OWNER_ATTRIBUTES:
                # Owner-only: hidden from non-owners, computed on demand (and
                # cached in ``_attributes``) the first time an owner asks for it.
                if not self.is_owner:
                    return  # type: ignore
                if parameter not in self._attributes:
                    self._attributes[parameter] = self._compute_owner_attribute(parameter)
            try:
                value: Any = self._attributes[parameter]
            except KeyError:
                return  # type: ignore
            if isinstance(value, tuple):
                value, should_escape = value
            return_value: str = str(value) if value is not None else None  # type: ignore
        return escape_content(return_value) if should_escape else return_value
