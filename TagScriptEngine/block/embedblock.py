from __future__ import annotations

import json
from inspect import ismethod
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from discord import Colour, Embed

from ..exceptions import BadColourArgument, EmbedParseError
from ..interface import Block
from ..interpreter import Context
from ..utils import truncate
from .helpers import helper_split, implicit_bool

try:
    import orjson  # noqa: F401
except ModuleNotFoundError:
    _has_orjson: bool = False
else:
    _has_orjson: bool = True


__all__: Tuple[str, ...] = ("EmbedBlock",)


if _has_orjson:
    _from_json = orjson.loads  # type: ignore
else:
    _from_json = json.loads


def string_to_color(argument: str) -> Colour:
    arg = argument.replace("0x", "").lower()

    # startswith, not arg[0]: an empty arg (e.g. a payload of "0x") indexed out
    # of range and only got caught by an unrelated handler upstream.
    if arg.startswith("#"):
        arg = arg[1:]
    try:
        value = int(arg, base=16)
        if not (0 <= value <= 0xFFFFFF):
            raise BadColourArgument(arg)
        return Colour(value=value)
    except ValueError:
        arg = arg.replace(" ", "_")
        method = getattr(Colour, arg, None)
        if arg.startswith("from_") or method is None or not ismethod(method):
            # `from None`: the ValueError just means "not hex, try a name" and
            # is noise in the traceback.
            raise BadColourArgument(arg) from None
        return method()


def set_color(embed: Embed, attribute: str, value: str) -> None:
    value = string_to_color(value)  # type: ignore
    setattr(embed, attribute, value)


def set_dynamic_url(embed: Embed, attribute: str, value: str) -> None:
    method = getattr(embed, f"set_{attribute}")
    method(url=value)


def add_field(embed: Embed, _: str, payload: str) -> None:
    if (data := helper_split(payload, maxsplit=2, double_semicolon=True)) is None:  # type: ignore
        raise EmbedParseError(
            "`add_field` payload was not split by `;;` (double semicolon), `|` (pipe), or `~` (tilde)"
        )
    try:
        name, value, _inline = data
        inline = implicit_bool(_inline)
        if inline is None:
            raise EmbedParseError(
                f"`inline` argument for `add_field` is not a boolean value ({_inline})"
            )
    except ValueError:
        name, value = cast(
            List[str],
            helper_split(payload, maxsplit=1, double_semicolon=True),
        )
        inline = False
    name = truncate(name, max=FIELD_LIMITS["field.name"])
    value = truncate(value, max=FIELD_LIMITS["field.value"])
    embed.add_field(name=name, value=value, inline=inline)


def set_footer(embed: Embed, _: str, payload: str) -> None:
    data = helper_split(payload, maxsplit=1, double_semicolon=True)  # type: ignore
    if data is None:
        embed.set_footer(text=truncate(payload, max=FIELD_LIMITS["footer.text"]))
    else:
        text, icon_url = data
        embed.set_footer(text=truncate(text, max=FIELD_LIMITS["footer.text"]), icon_url=icon_url)


def set_author(embed: Embed, _: str, payload: str) -> None:
    data = helper_split(payload, maxsplit=1, double_semicolon=True)  # type: ignore
    if data is None:
        embed.set_author(name=truncate(payload, max=FIELD_LIMITS["author.name"]))
    else:
        name, icon_url = data
        embed.set_author(name=truncate(name, max=FIELD_LIMITS["author.name"]), icon_url=icon_url)


# Discord embed field character limits
# https://docs.discord.com/developers/resources/message#embed-object-embed-limits
FIELD_LIMITS: Dict[str, int] = {
    "title": 256,
    "description": 4096,
    "footer.text": 2048,
    "author.name": 256,
    "field.name": 256,
    "field.value": 1024,
}


class EmbedBlock(Block):
    """
    An embed block will send an embed in the tag response.
    There are two ways to use the embed block, either by using properly
    formatted embed JSON from an embed generator or manually inputting
    the accepted embed attributes.

    **JSON**

    Using JSON to create an embed offers complete embed customization.
    Multiple embed generators are available online to visualize and generate
    embed JSON.

    .. important::
        - `Embed Limits are: <https://docs.discord.com/developers/resources/message#embed-object-embed-limits>`_
            - Title: 256 characters
            - Description: 4096 characters
            - Footer: 2048 characters
            - Author: 256 characters
            - Field name: 256 characters
            - Field value: 1024 characters
        - The total length of the embed must not exceed 6000 characters.

    **Usage:** ``{embed(<json>)}``

    **Payload:** None

    **Parameter:** json

    **Examples:**

    .. code-block:: yaml

        Example 1:
        {embed({"title":"Hello!", "description":"This is a test embed."})}

        Example 2:
        {embed({
            "title":"Here's a random duck!",
            "image":{"url":"https://random-d.uk/api/randomimg"},
            "color":15194415,
            "fields": [
                {
                    "name": "Fun Fact",
                    "value": "Ducks are birds that are well-adapted to life in and around water.",
                    "inline": false
                }
            ]
        })}

    **Manual**

    The following embed attributes can be set manually:

    *   ``title``
    *   ``description``
    *   ``color``
    *   ``url``
    *   ``thumbnail``
    *   ``image``
    *   ``author``
    *   ``footer``
    *   ``field`` - (See below)

    Adding a field to an embed requires the payload to be split by ``;;``,
    ``|`` or ``~`` into either 2 or 3 parts. The first part is the name
    of the field, the  second is the text of the field, and the third
    optionally specifies  whether the field should be inline.

    **Usage:** ``{embed(<attribute>):<value>}``

    **Payload:** value

    **Parameter:** attribute

    **Examples:** ::

        {embed(color):#37b2cb}
        {embed(title):Rules}
        {embed(description):Follow these rules to ensure a good experience in our server!}
        {embed(field):Rule 1|Respect everyone you speak to.|false}
        {embed(author):Mod Team|{author(avatar)}}
        {embed(footer):Thanks for reading!|{guild(icon)}}

    Both methods can be combined to create an embed in a tag.
    The following tagscript uses JSON to create an embed with fields and later
    set the embed title.

    .. caution::
        - The ``JSON`` block acts as a base for the embed.
        - Since blocks are processed in **order**, the ``JSON`` block **must** come **before** any manual attribute blocks.
        - The manual attributes are used to ``modify`` or ``add`` to the embed created by the ``JSON`` block.

    .. code-block:: yaml

        {embed({
            "description": "This is a test description.",
            "fields": [
                {
                    "name": "Field 1",
                    "value": "field description",
                    "inline": false
                }
            ]
        })}
        {embed(title):My embed title}

    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("embed",)

    ATTRIBUTE_HANDLERS: Dict[str, Any] = {
        "description": setattr,
        "title": setattr,
        "color": set_color,
        "colour": set_color,
        "url": setattr,
        "thumbnail": set_dynamic_url,
        "image": set_dynamic_url,
        "field": add_field,
        "author": set_author,
        "footer": set_footer,
    }

    @staticmethod
    def get_embed(ctx: Context) -> Embed:
        return ctx.response.actions.get("embed", Embed())

    @staticmethod
    def value_to_color(value: Optional[Union[int, str]]) -> Colour:
        if value is None or isinstance(value, Colour):
            return value  # type: ignore
        if isinstance(value, int):
            return Colour(value)
        elif isinstance(value, str):
            return string_to_color(value)
        else:
            raise EmbedParseError("Received invalid type for color key (expected string or int)")

    def text_to_embed(self, text: str) -> Embed:
        try:
            data = _from_json(text)
        except (json.decoder.JSONDecodeError, ValueError) as error:
            raise EmbedParseError(error) from error

        if not isinstance(data, dict):
            raise EmbedParseError("The embed JSON must be an object.")
        if data.get("embed"):
            data = data["embed"]
            if not isinstance(data, dict):
                raise EmbedParseError('The "embed" key must be an object.')
        if timestamp := data.get("timestamp"):
            if not isinstance(timestamp, str):
                raise EmbedParseError('The "timestamp" key must be a string.')
            # removesuffix, not strip: strip("Z") also eats a leading Z.
            data["timestamp"] = timestamp.removesuffix("Z")

        color = data.pop("color", data.pop("colour", None))

        try:
            embed = Embed.from_dict(data)
        except Exception as error:
            raise EmbedParseError(error) from error
        else:
            if color := self.value_to_color(color):
                embed.color = color
            self._truncate_embed_fields(embed)
            return embed

    @classmethod
    def update_embed(cls, embed: Embed, attribute: str, value: str) -> Embed:
        # Truncate value to Discord's per-field limit before setting
        if attribute in FIELD_LIMITS:
            value = truncate(value, max=FIELD_LIMITS[attribute])
        handler = cls.ATTRIBUTE_HANDLERS[attribute]
        try:
            handler(embed, attribute, value)
        except Exception as error:
            raise EmbedParseError(error) from error
        return embed

    @staticmethod
    def _truncate_embed_fields(embed: Embed) -> None:
        """Truncate embed fields to Discord's per-field character limits."""
        if embed.title and len(embed.title) > FIELD_LIMITS["title"]:
            embed.title = truncate(embed.title, max=FIELD_LIMITS["title"])
        if embed.description and len(embed.description) > FIELD_LIMITS["description"]:
            embed.description = truncate(embed.description, max=FIELD_LIMITS["description"])
        if (
            embed.footer
            and embed.footer.text
            and len(embed.footer.text) > FIELD_LIMITS["footer.text"]
        ):
            embed.set_footer(
                text=truncate(embed.footer.text, max=FIELD_LIMITS["footer.text"]),
                icon_url=embed.footer.icon_url,
            )
        if (
            embed.author
            and embed.author.name
            and len(embed.author.name) > FIELD_LIMITS["author.name"]
        ):
            embed.set_author(
                name=truncate(embed.author.name, max=FIELD_LIMITS["author.name"]),
                url=embed.author.url,
                icon_url=embed.author.icon_url,
            )
        # Update fields once by index: `set_field_at` replaces the field, invalidating subsequent index lookups.
        for idx, field in enumerate(embed.fields):
            name, value = field.name, field.value
            over_name = bool(name) and len(name) > FIELD_LIMITS["field.name"]
            over_value = bool(value) and len(value) > FIELD_LIMITS["field.value"]
            if not (over_name or over_value):
                continue
            if over_name:
                name = truncate(name, max=FIELD_LIMITS["field.name"])
            if over_value:
                value = truncate(value, max=FIELD_LIMITS["field.value"])
            embed.set_field_at(idx, name=name, value=value, inline=field.inline)

    @staticmethod
    def return_error(error: Exception) -> str:
        return f"Embed Parse Error: {error}"

    @staticmethod
    def return_embed(ctx: Context, embed: Embed) -> str:
        try:
            length = len(embed)
        except Exception as error:
            return str(error)
        if length > 6000:
            return f"`MAX EMBED LENGTH REACHED ({length}/6000)`"
        # Skip registering empty embeds to prevent Discord API rejection.
        # Must check non-text attributes (color, image, etc.) so sequential embed blocks
        # (e.g. `{embed(color):red}`) aren't lost before text is added.
        if not (
            length
            or embed.colour
            or embed.url
            or embed.timestamp
            or embed.image
            or embed.thumbnail
        ):
            return ""
        ctx.response.actions["embed"] = embed
        return ""

    def process(self, ctx: Context) -> Optional[str]:
        if not ctx.verb.parameter:
            return self.return_embed(ctx, self.get_embed(ctx))

        lowered = ctx.verb.parameter.lower()
        try:
            if ctx.verb.parameter.startswith("{") and ctx.verb.parameter.endswith("}"):
                embed = self.text_to_embed(ctx.verb.parameter)
            elif lowered in self.ATTRIBUTE_HANDLERS and ctx.verb.payload:
                embed = self.get_embed(ctx)
                embed = self.update_embed(embed, lowered, ctx.verb.payload)
            else:
                # Unknown attribute, or a known one with no value. Consume it -
                # None would echo the raw block into the message.
                return ""
        except EmbedParseError as error:
            return self.return_error(error)

        return self.return_embed(ctx, embed)
