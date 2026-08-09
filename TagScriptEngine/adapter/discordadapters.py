from __future__ import annotations

import datetime
from random import choice
from typing import Any, Dict, Optional, Tuple, Union, cast

import discord

from .._warnings import deprecated
from ..interface import SimpleAdapter

__all__: Tuple[str, ...] = (
    "AttributeAdapter",
    "DiscordAttributeAdapter",
    "UserAdapter",
    "MemberAdapter",
    "DMChannelAdapter",
    "ChannelAdapter",
    "GuildAdapter",
    "RoleAdapter",
    "DiscordObjectAdapter",
)


def _base_defaults(base: Any) -> Dict[str, Any]:
    """The id/created_at/timestamp/name every Discord object adapter exposes."""
    created_at: datetime.datetime = getattr(
        base, "created_at", None
    ) or discord.utils.snowflake_time(base.id)
    return {
        "id": base.id,
        "created_at": created_at,
        "timestamp": int(created_at.timestamp()),
        "name": getattr(base, "name", str(base)),
    }


class AttributeAdapter(SimpleAdapter[Union[discord.TextChannel, discord.Member, discord.Guild]]):
    """
    .. deprecated:: 3.2.0
        AttributeAdapter has been deprecated and will be removed in favor of
        ``TagScriptEngine.adapter.discordadapters.DiscordAttributeAdapter`` or
        consider using ``TagScriptEngine.interface.adapter.SimpleAdapter`` instead.
    """

    __slots__: Tuple[str, ...] = ()

    @deprecated(
        name="TagScriptEngine.adapter.discordadapters.AttributeAdapter",
        reason=(
            "AttributeAdapter has been deprecated and will be removed in favor of "
            "``TagScriptEngine.adapter.discordadapters.DiscordAttributeAdapter`` or "
            "consider using ``TagScriptEngine.interface.adapter.SimpleAdapter`` instead."
        ),
        version="3.2.0",
    )
    def __init__(self, base: Union[discord.TextChannel, discord.Member, discord.Guild]) -> None:
        super().__init__(base=base, defaults=_base_defaults(base))


class DiscordAttributeAdapter(
    SimpleAdapter[
        Union[
            discord.TextChannel,
            discord.DMChannel,
            discord.User,
            discord.Member,
            discord.Guild,
            discord.Role,
        ]
    ]
):
    """
    Base adapter for Discord objects. Exposes ``id``, ``name``, ``created_at``
    and ``timestamp``; subclasses add their own in :meth:`update_attributes`.
    """

    __slots__: Tuple[str, ...] = ()

    def __init__(
        self,
        base: Union[
            discord.TextChannel,
            discord.DMChannel,
            discord.User,
            discord.Member,
            discord.Guild,
            discord.Role,
        ],
    ) -> None:
        # Passed as defaults, not applied afterwards, so update_attributes() in
        # a subclass can override them instead of being silently clobbered.
        super().__init__(base=base, defaults=_base_defaults(base))


class UserAdapter(DiscordAttributeAdapter):
    """
    The ``{user}`` block with no parameters returns the user's full username,
    but passing the attributes listed below to the block payload will return
    that attribute instead.

    **Usage:** ``{user([attribute])}``

    **Payload:** None

    **Parameter:** attribute, None

    Attributes
    ----------
    id
        The user's Discord ID.
    name
        The user's username.
    nick
        The user's nickname, if they have one, else their username.
    avatar
        A link to the user's avatar, which can be used in embeds.
    created_at
        The user's account creation date.
    timestamp
        The user's account creation date as UTC timestamp.
    mention
        A formatted text that ping's the user.
    bot
        Wheather or not the user is a bot.
    accent_color
        The user's accent color if banner is not present, otherwise empty.
        Only delivered on a fetched user, so it is usually empty.
    avatar_decoration
        A link to the user's avatar decoration, or empty if they have none.

    """

    def update_attributes(self) -> None:
        object: discord.User = cast(discord.User, self.object)
        avatar_url: str = object.display_avatar.url
        asset = getattr(object, "avatar_decoration", None)
        additional_attributes: Dict[str, Any] = {
            "nick": object.display_name,
            "mention": object.mention,
            "avatar": (avatar_url, False),
            "bot": object.bot,
            # Only populated on a fetched user, not a cached one.
            "accent_color": getattr(object, "accent_color", None) or "",
            "avatar_decoration": asset.with_format("png").url if asset else "",
        }
        self._attributes.update(additional_attributes)


class MemberAdapter(DiscordAttributeAdapter):
    """
    The ``{author}`` block with no parameters returns the tag invoker's full username
    and discriminator, but passing the attributes listed below to the block payload
    will return that attribute instead.

    **Aliases:** ``user``

    **Usage:** ``{author([attribute])``

    **Payload:** None

    **Parameter:** attribute, None

    Attributes
    ----------
    id
        The author's Discord ID.
    name
        The author's username.
    nick
        The author's nickname, if they have one, else their username.
    avatar
        A link to the author's avatar, which can be used in embeds.
    discriminator
        The author's discriminator.
    created_at
        The author's account creation date.
    timestamp
        The author's account creation date as a UTC timestamp.
    joined_at
        The date the author joined the server.
    joinstamp
        The author's join date as a UTC timestamp.
    mention
        A formatted text that pings the author.
    bot
        Whether or not the author is a bot.
    color
        The author's top role's color as a hex code.
    top_role
        The author's top role.
    roleids
        A list of the author's role IDs, split by spaces.
    boost
        If the user has boosted, this will be the UTC timestamp of when they did,
        if not this will be empty.
    timed_out
        If the user is currently timed out, the datetime of when the timeout ends;
        otherwise empty.
    banner
        The user's banner url, if available. A banner is not delivered over the
        gateway, so the bare engine only sees it when the member was retrieved
        via an explicit REST fetch - otherwise this is empty for cached members.
        The Tags cog resolves it lazily (fetching only when a tag uses ``banner``,
        with caching and a per-user cooldown), so there it is populated on demand.
    """

    def update_attributes(self) -> None:
        object: discord.Member = cast(discord.Member, self.object)
        avatar_url: str = object.display_avatar.url
        # `or`, not a getattr default: Member.joined_at always exists but is
        # Optional, so the default never fired and None reached .timestamp().
        joined_at: datetime.datetime = getattr(object, "joined_at", None) or self.object.created_at
        # So ``timed_out_until`` must be compared against the current time. 
        # And Returns ``False`` when the member isn't currently timed out.
        timed_out_until: Any = getattr(object, "timed_out_until", None)
        is_timed_out: bool = bool(timed_out_until) and timed_out_until > discord.utils.utcnow()
        # ``Member.banner``/``display_banner`` is now explicitly fetched.
        banner: Any = getattr(object, "display_banner", None) or getattr(object, "banner", None)
        additional_attributes: Dict[str, Any] = {
            "color": object.color,
            "colour": object.color,
            "nick": object.display_name,
            "avatar": (avatar_url, False),
            "discriminator": object.discriminator,
            "joined_at": joined_at,
            "joinstamp": int(joined_at.timestamp()),
            "mention": object.mention,
            "bot": object.bot,
            "top_role": getattr(object, "top_role", ""),
            "boost": getattr(object, "premium_since", ""),
            "timed_out": timed_out_until if is_timed_out else "",
            "banner": banner.url if banner else "",
            # Always present, so a member with no roles renders empty rather
            # than leaking the raw {author(roleids)} into the message.
            "roleids": " ".join(str(r) for r in getattr(self.object, "_roles", None) or ()),
        }
        self._attributes.update(additional_attributes)


class DMChannelAdapter(DiscordAttributeAdapter):
    """
    The ``{channel}`` block with no parameters returns the channel's full name
    but passing the attributes listed below to the block payload will return
    the attribute instead.

    **Usage:** ``{channel([attribute])``

    **Payload:** None

    **Parameter:** attribute, None

    Attributes
    ----------
    id
        The channel's ID.
    name
        The channel's name.
    created_at
        The channel's creation date.
    timestamp
        The channel's creation date as a UTC timestamp.
    jump_url
        A link to the channel.

    """

    def update_attributes(self) -> None:
        self._attributes.update({"jump_url": getattr(self.object, "jump_url", "")})


class ChannelAdapter(DiscordAttributeAdapter):
    """
    The ``{channel}`` block with no parameters returns the channel's full name
    but passing the attributes listed below to the block payload
    will return that attribute instead.

    **Usage:** ``{channel([attribute])``

    **Payload:** None

    **Parameter:** attribute, None

    Attributes
    ----------
    id
        The channel's ID.
    name
        The channel's name.
    created_at
        The channel's creation date.
    timestamp
        The channel's creation date as a UTC timestamp.
    nsfw
        Whether the channel is nsfw.
    mention
        A formatted text that pings the channel.
    topic
        The channel's topic.
    category_id
        The category the channel is associated with.
        If no category channel, this will return empty.
    jump_url
        A link to the channel.
    """

    def update_attributes(self) -> None:
        channel: Any = self.object
        source: Any = getattr(channel, "parent", None) or channel
        additional_attributes: Dict[str, Any] = {
            "nsfw": getattr(source, "nsfw", False),
            "mention": getattr(channel, "mention", ""),
            "topic": getattr(source, "topic", "") or "",
            "slowmode": getattr(channel, "slowmode_delay", 0),
            "category_id": getattr(channel, "category_id", "") or "",
            "jump_url": getattr(channel, "jump_url", ""),
        }
        self._attributes.update(additional_attributes)


class GuildAdapter(DiscordAttributeAdapter):
    """
    The ``{server}`` block with no parameters returns the server's name
    but passing the attributes listed below to the block payload
    will return that attribute instead.

    **Aliases:** ``guild``

    **Usage:** ``{server([attribute])``

    **Payload:** None

    **Parameter:** attribute, None

    Attributes
    ----------
    id
        The server's ID.
    name
        The server's name.
    icon
        A link to the server's icon, which can be used in embeds.
    created_at
        The server's creation date.
    timestamp
        The server's creation date as a UTC timestamp.
    member_count
        The server's member count.
    bots
        The number of bots in the server.
    humans
        The number of humans in the server.
    description
        The server's description if one is set, otherwise empty.
    random
        A random member from the server.
    vanity
        If guild has a vanity, this returns the vanity else empty.
    owner_id
        The server owner's id.
    mfa
        The server's mfa level.
    boosters
        The server's active booster count.
    boost_level
        The server's current boost level/tier.
    discovery_splash
        A link to the server's discovery splash, or empty if it has none.
    invite_splash
        A link to the server's invite splash, or empty if it has none.
    banner
        A link to the server's banner, or empty if it has none.

    .. note::
        Every attribute above is **empty** when the server does not have it -
        never ``False`` or the raw block. Test one with ``{if({server(banner)}==):
        no banner|{server(banner)}}``; see :class:`.AssignmentBlock` for why
        ``==False`` is not the right check.
    """

    def update_attributes(self) -> None:
        guild: discord.Guild = cast(discord.Guild, self.object)
        member_count: int = getattr(guild, "member_count", 0)
        icon_url: str = getattr(guild.icon, "url", "")
        additional_attributes: Dict[str, Any] = {
            "icon": (icon_url, False),
            "member_count": member_count,
            "members": member_count,
            "description": guild.description or "",
            "vanity": guild.vanity_url_code or "",
            "owner_id": guild.owner_id or "",
            "mfa": guild.mfa_level,
            "boosters": guild.premium_subscription_count,
            "boost_level": guild.premium_tier,
            "discovery_splash": getattr(guild.discovery_splash, "url", "") or "",
            "invite_splash": getattr(guild.splash, "url", "") or "",
            "banner": getattr(guild.banner, "url", "") or "",
        }
        self._attributes.update(additional_attributes)

    def update_methods(self) -> None:
        # bots/humans scan the whole member cache, so they are resolved on
        # demand rather than on every tag invocation that touches {server}.
        additional_methods: Dict[str, Any] = {
            "random": self.random_member,
            "bots": self.count_bots,
            "humans": self.count_humans,
        }
        self._methods.update(additional_methods)

    def random_member(self) -> Optional[discord.Member]:
        object: discord.Guild = cast(discord.Guild, self.object)
        # the member cache can be empty (no members intent / not chunked yet)
        return choice(object.members) if object.members else None

    def count_bots(self) -> int:
        return sum(1 for m in cast(discord.Guild, self.object).members if m.bot)

    def count_humans(self) -> int:
        return sum(1 for m in cast(discord.Guild, self.object).members if not m.bot)


class RoleAdapter(DiscordAttributeAdapter):
    """
    The ``{role}`` block with no parameters returns the role's full name
    but passing the attributes listed below to the block payload will
    return that attribute instead.

    **Usage:** ``{role([attribute])}``

    **Payload:** None

    **Parameter:** attribute, None

    Attributes
    ----------
    id
        The role's ID.
    name
        The role's name.
    created_at
        The role's creation date.
    timestamp
        The role's creation date as a UTC timestamp.
    color
        The role's color.
    display_icon
        A link to the role's icon, or empty if it has none.
    hoist
        Wheather the role is hoisted or not.
    managed
        Wheather the role is managed or not.
    mention
        A formatted text that pings the role.
    position
        The role's position.

    """

    def update_attributes(self) -> None:
        object: discord.Role = cast(discord.Role, self.object)
        additional_attributes: Dict[str, Any] = {
            "color": object.color,
            "display_icon": getattr(object.display_icon, "url", "") or "",
            "hoist": object.hoist,
            "managed": object.managed,
            "mention": object.mention,
            "position": object.position,
        }
        self._attributes.update(additional_attributes)


class DiscordObjectAdapter(SimpleAdapter[discord.Object]):
    """
    The ``{object}`` block with no parameters returns the discord object's ID,
    but passing the attributes listed below to the block payload will return
    that attribute instead.

    **Usage:** ``{object([attribute])}``

    **Payload:** None

    **Parameter:** attribute, None

    Attributes
    ----------
    id
        The object's Discord ID.
    created_at
        The object's creation date.
    timestamp
        The object's creation date as a UTC timestamp.

    """

    __slots__: Tuple[str, ...] = ()

    def __init__(self, base: discord.Object) -> None:
        defaults = _base_defaults(base)
        # A bare discord.Object has no name.
        defaults.pop("name", None)
        super().__init__(base=base, defaults=defaults)

    def default_value(self) -> str:
        return str(self.object.id)
