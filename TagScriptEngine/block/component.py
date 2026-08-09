from __future__ import annotations

from inspect import ismethod
from typing import Any, Dict, List, Optional, Tuple

import discord

from ..exceptions import ComponentParseError
from ..interface import Block
from ..interpreter import Context
from .helpers import helper_split

__all__: Tuple[str, ...] = ("ComponentBlock", "build_components_v2_view")

# Discord components v2 text limit
TEXT_LIMIT: int = 4000

# Discord limits messages to 40 components (including nested).
# Reserve 1 slot for plain-text output folded in at send time.
MAX_COMPONENTS: int = 40

# A single media gallery holds at most 10 items.
MAX_MEDIA_ITEMS: int = 10

# Separator spacing keywords -> (visible, large)
SEPARATOR_KEYWORDS: Dict[str, Tuple[bool, bool]] = {
    "": (True, False),
    "small": (True, False),
    "large": (True, True),
    "big": (True, True),
    "hidden": (False, False),
    "invisible": (False, False),
    "blank": (False, False),
}


class ComponentBlock(Block):
    """
    The component block builds a `Components V2 <https://discord.com/developers/docs/components/reference>`_
    message in the tag response. It is the text-only counterpart of the embed
    block: it accepts manual attributes that are accumulated, in order, into a
    single layout stored under the ``components_v2`` response action.

    The accumulated layout is turned into a :class:`discord.ui.LayoutView` by
    :func:`build_components_v2_view`, which the host (e.g. a Red cog) calls at
    send time - passing any plain tag output as ``leading_content`` so it is
    folded in as the first text block rather than lost (a Components V2 message
    cannot carry a normal ``content`` field).

    .. important::
        - A Components V2 message **cannot** be combined with a normal embed
          (``{embed}``). If both are used, the component layout wins and the
          embed is dropped.
        - Any plain text output from the tag is folded in as the first text
          block of the layout so it is never lost.
        - The combined text across all blocks must not exceed 4000 characters.

    By default the text blocks render plainly. Wrapping them in a **container**
    gives the framed, embed-like look. The frame can be enabled with or without
    a colour:

    *   ``container`` (aliases ``box``, ``frame``) - wraps the whole layout in a
        framed container. The payload optionally accepts a colour, e.g.
        ``{component(container):#5865F2}``, to add an embed-like accent bar.
    *   ``color`` / ``colour`` - sets the accent bar colour and implies the
        container frame.

    Colours accept the same input as the embed block: a hex code
    (``#5865F2``, ``0x5865F2`` or ``5865F2``) or a colour name such as ``red``,
    ``blurple`` or ``dark blue``.

    The following attributes can be set manually:

    *   ``text`` - a markdown text block (repeatable). Standard Discord markdown
        works, including ``#`` / ``##`` / ``###`` headings and ``-#`` small text.
    *   ``separator`` - inserts a divider (``small`` is the default). The payload
        optionally accepts ``large`` / ``big`` (more spacing) or ``hidden`` /
        ``invisible`` / ``blank`` (spacing only, no line).
    *   ``thumbnail`` - attaches a thumbnail image to the most recent text
        block, turning it into a section.
    *   ``image`` - adds one or more images to a media gallery. Multiple URLs
        can be passed at once, separated by ``;;``, ``|`` or ``~`` (up to 10
        total). Repeatable.

    Blocks are processed in **order**, so the order of the attribute blocks is
    the order they appear in the message.

    **Usage:** ``{component(<attribute>):<value>}``

    **Aliases:** ``comp``, ``cv2``, ``c2``

    **Payload:** value

    **Parameter:** attribute

    **Examples:**

    .. code-block:: yaml

        Framed with an accent bar:
        {component(color):#5865F2}
        {component(text):# Server Rules}
        {component(text):Please read these **carefully**.}
        {component(separator)}
        {component(text):1. Be respectful.}
        {component(text):-# Last updated today.}

        Framed with no colour:
        {component(container)}
        {component(text):This shows up boxed, like an embed without the bar.}

        Plain text, no frame:
        {component(text):Every obstacle carries an unseen aid for those willing to endure.}

        Framed without an accent bar:
        {component(box)}
        {component(text):## Quote of the Day}
        {component(separator)}
        {component(text):Remember {author(mention)}!
        - Every obstacle carries an unseen aid for those willing to endure.}

    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("component", "comp", "cv2", "c2")

    ATTRIBUTES: Tuple[str, ...] = (
        "text",
        "container",
        "box",
        "frame",
        "color",
        "colour",
        "separator",
        "thumbnail",
        "image",
    )

    @classmethod
    def will_accept(cls, ctx: Context) -> bool:
        if not super().will_accept(ctx):
            return False
        return (ctx.verb.parameter or "").lower() in cls.ATTRIBUTES

    @staticmethod
    def _get_layout(ctx: Context) -> Dict[str, Any]:
        layout: Optional[Dict[str, Any]] = ctx.response.actions.get("components_v2")
        if layout is None:
            layout = {"framed": False, "accent_color": None, "items": []}
            ctx.response.actions["components_v2"] = layout
        return layout

    @staticmethod
    def _total_text(layout: Dict[str, Any]) -> int:
        total = 0
        for item in layout["items"]:
            if item["type"] in ("text", "section"):
                total += len(item["content"])
        return total

    @staticmethod
    def _component_count(layout: Dict[str, Any]) -> int:
        # Mirrors how the layout renders into discord components so the
        # 40-component cap can be enforced before the message is built.
        count = 1 if layout["framed"] else 0  # the wrapping container
        for item in layout["items"]:
            kind = item["type"]
            if kind == "section":
                count += 2  # section + its thumbnail accessory
            elif kind == "gallery":
                count += 1 + len(item["urls"])  # gallery + each media item
            else:
                count += 1  # text or separator
        return count

    def _at_component_limit(self, layout: Dict[str, Any], adding: int = 1) -> bool:
        # Reserve one slot for the plain-output text block folded in at send.
        return self._component_count(layout) + adding > MAX_COMPONENTS - 1

    def process(self, ctx: Context) -> Optional[str]:
        attribute = (ctx.verb.parameter or "").lower()
        payload = ctx.verb.payload
        layout = self._get_layout(ctx)

        if attribute == "text":
            if payload is None:
                # Consume it - None would echo the raw block into the message.
                return ""
            if self._total_text(layout) + len(payload) > TEXT_LIMIT:
                return f"`MAX COMPONENT TEXT LENGTH REACHED ({TEXT_LIMIT})`"
            if self._at_component_limit(layout):
                return f"`MAX COMPONENT COUNT REACHED ({MAX_COMPONENTS})`"
            layout["items"].append({"type": "text", "content": payload})
            return ""

        if attribute in ("container", "box", "frame"):
            if payload:
                try:
                    color = self._parse_color(payload)
                except ComponentParseError as error:
                    return self.return_error(error)
                layout["accent_color"] = color
            layout["framed"] = True
            return ""

        if attribute in ("color", "colour"):
            if not payload:
                # Consume it - None would echo the raw block into the message.
                return ""
            try:
                color = self._parse_color(payload)
            except ComponentParseError as error:
                return self.return_error(error)
            # A colour can only be shown via a container, so it implies framing.
            layout["framed"] = True
            layout["accent_color"] = color
            return ""

        if attribute == "separator":
            if self._at_component_limit(layout):
                return f"`MAX COMPONENT COUNT REACHED ({MAX_COMPONENTS})`"
            keyword = (payload or "").strip().lower()
            visible, large = SEPARATOR_KEYWORDS.get(keyword, (True, False))
            layout["items"].append({"type": "separator", "visible": visible, "large": large})
            return ""

        if attribute == "thumbnail":
            if not payload:
                # Consume it - None would echo the raw block into the message.
                return ""
            # Attach to the most recent text block, converting it to a section.
            for item in reversed(layout["items"]):
                if item["type"] == "text":
                    item["type"] = "section"
                    item["thumbnail"] = payload
                    break
            else:
                # A fresh section costs two components (section + thumbnail).
                if self._at_component_limit(layout, adding=2):
                    return f"`MAX COMPONENT COUNT REACHED ({MAX_COMPONENTS})`"
                layout["items"].append({"type": "section", "content": "", "thumbnail": payload})
            return ""

        if attribute == "image":
            if not payload:
                # Consume it - None would echo the raw block into the message.
                return ""
            # Delimiters: ;; takes priority (same as embed fields); when ;; is
            # present, | and ~ are not used. Otherwise split on | or ~.
            split = helper_split(payload, double_semicolon=True)
            raw = split if split is not None else [payload]
            urls = [url.strip() for url in raw if url.strip()]
            if not urls:
                return ""
            # Only coalesce into the previous gallery when it is the most recent
            # item, so images keep document order relative to other blocks.
            items = layout["items"]
            gallery: Dict[str, Any]
            if items and items[-1]["type"] == "gallery":
                gallery = items[-1]
            else:
                if self._at_component_limit(layout):
                    return f"`MAX COMPONENT COUNT REACHED ({MAX_COMPONENTS})`"
                gallery = {"type": "gallery", "urls": []}
                items.append(gallery)
            for url in urls:
                if len(gallery["urls"]) >= MAX_MEDIA_ITEMS:
                    return f"`MAX MEDIA GALLERY ITEMS REACHED ({MAX_MEDIA_ITEMS})`"
                if self._at_component_limit(layout):
                    return f"`MAX COMPONENT COUNT REACHED ({MAX_COMPONENTS})`"
                gallery["urls"].append(url)
            return ""

        return ""

    @staticmethod
    def return_error(error: Exception) -> str:
        return f"Component Parse Error: {error}"

    @staticmethod
    def _parse_color(argument: str) -> int:
        # Accepts hex literals or non-`from_*` `discord.Colour` classmethods (matches embed block colour).
        # Resolved dynamically at runtime to track discord.py updates.
        arg = argument.strip().replace("0x", "").lstrip("#").lower()
        if not arg:
            raise ComponentParseError(f'Colour "{argument}" is invalid.')
        try:
            value = int(arg, base=16)
        except ValueError:
            pass
        else:
            if not (0 <= value <= 0xFFFFFF):
                raise ComponentParseError(f'Colour "{argument}" is invalid.')
            return value

        method = getattr(discord.Colour, arg.replace(" ", "_"), None)
        if arg.startswith("from_") or method is None or not ismethod(method):
            raise ComponentParseError(f'Colour "{argument}" is invalid.')
        return method().value


def build_components_v2_view(
    layout: Dict[str, Any], leading_content: Optional[str] = None
) -> "discord.ui.LayoutView":
    """
    Render a ``components_v2`` layout (as accumulated by :class:`ComponentBlock`)
    into a :class:`discord.ui.LayoutView`.

    ``leading_content`` is the tag's plain output, folded in as the first text
    block. It counts toward the 4000-character Components V2 text budget and is
    trimmed to whatever room the layout's own text leaves. Requires a discord.py
    version with Components V2 support (2.6 or higher).
    """
    items: List[Dict[str, Any]] = []
    if leading_content:
        used = sum(len(i["content"]) for i in layout["items"] if i["type"] in ("text", "section"))
        remaining = TEXT_LIMIT - used
        if remaining <= 0:
            leading_content = None
        elif len(leading_content) > remaining:
            leading_content = leading_content[: max(0, remaining - 1)] + "…"
        if leading_content:
            items.append({"type": "text", "content": leading_content})
    items.extend(layout["items"])

    children: List["discord.ui.Item"] = []
    for item in items:
        kind = item["type"]
        if kind == "text":
            children.append(discord.ui.TextDisplay(item["content"]))
        elif kind == "section":
            text = item.get("content") or "​"
            children.append(
                discord.ui.Section(text, accessory=discord.ui.Thumbnail(item["thumbnail"]))
            )
        elif kind == "separator":
            spacing = (
                discord.SeparatorSpacing.large if item["large"] else discord.SeparatorSpacing.small
            )
            children.append(discord.ui.Separator(visible=item["visible"], spacing=spacing))
        elif kind == "gallery":
            children.append(
                discord.ui.MediaGallery(*[discord.MediaGalleryItem(url) for url in item["urls"]])
            )

    if not children:
        children.append(discord.ui.TextDisplay("​"))

    view = discord.ui.LayoutView(timeout=None)
    accent = layout.get("accent_color")
    if layout.get("framed") or accent is not None:
        view.add_item(discord.ui.Container(*children, accent_colour=accent))
    else:
        for child in children:
            view.add_item(child)
    return view
