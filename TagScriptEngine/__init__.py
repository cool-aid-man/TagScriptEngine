from __future__ import annotations

from typing import Final, NamedTuple, Tuple

from ._warnings import (
    TagScriptEngineDeprecationWarning as TagScriptEngineDeprecationWarning,
)
from .adapter import (
    AttributeAdapter as AttributeAdapter,
)
from .adapter import (
    ChannelAdapter as ChannelAdapter,
)
from .adapter import (
    DiscordAttributeAdapter as DiscordAttributeAdapter,
)
from .adapter import (
    DiscordObjectAdapter as DiscordObjectAdapter,
)
from .adapter import (
    DMChannelAdapter as DMChannelAdapter,
)
from .adapter import (
    FunctionAdapter as FunctionAdapter,
)
from .adapter import (
    GuildAdapter as GuildAdapter,
)
from .adapter import (
    IntAdapter as IntAdapter,
)
from .adapter import (
    MemberAdapter as MemberAdapter,
)
from .adapter import (
    RedBotAdapter as RedBotAdapter,
)
from .adapter import (
    RedCommandAdapter as RedCommandAdapter,
)
from .adapter import (
    RoleAdapter as RoleAdapter,
)
from .adapter import (
    SafeObjectAdapter as SafeObjectAdapter,
)
from .adapter import (
    StringAdapter as StringAdapter,
)
from .adapter import (
    UserAdapter as UserAdapter,
)
from .block import (
    AllBlock as AllBlock,
)
from .block import (
    AllowedMentionsBlock as AllowedMentionsBlock,
)
from .block import (
    AnyBlock as AnyBlock,
)
from .block import (
    AssignmentBlock as AssignmentBlock,
)
from .block import (
    BlacklistBlock as BlacklistBlock,
)
from .block import (
    BreakBlock as BreakBlock,
)
from .block import (
    CommandBlock as CommandBlock,
)
from .block import (
    ComponentBlock as ComponentBlock,
)
from .block import (
    CooldownBlock as CooldownBlock,
)
from .block import (
    CountBlock as CountBlock,
)
from .block import (
    CycleBlock as CycleBlock,
)
from .block import (
    EmbedBlock as EmbedBlock,
)
from .block import (
    FiftyFiftyBlock as FiftyFiftyBlock,
)
from .block import (
    IfBlock as IfBlock,
)
from .block import (
    JoinBlock as JoinBlock,
)
from .block import (
    LengthBlock as LengthBlock,
)
from .block import (
    ListBlock as ListBlock,
)
from .block import (
    LooseVariableGetterBlock as LooseVariableGetterBlock,
)
from .block import (
    LowerBlock as LowerBlock,
)
from .block import (
    MathBlock as MathBlock,
)
from .block import (
    OrdinalBlock as OrdinalBlock,
)
from .block import (
    OverrideBlock as OverrideBlock,
)
from .block import (
    PythonBlock as PythonBlock,
)
from .block import (
    RandomBlock as RandomBlock,
)
from .block import (
    RangeBlock as RangeBlock,
)
from .block import (
    RedirectBlock as RedirectBlock,
)
from .block import (
    ReplaceBlock as ReplaceBlock,
)
from .block import (
    RequireBlock as RequireBlock,
)
from .block import (
    SequentialGather as SequentialGather,
)
from .block import (
    ShortCutRedirectBlock as ShortCutRedirectBlock,
)
from .block import (
    SleepBlock as SleepBlock,
)
from .block import (
    StopBlock as StopBlock,
)
from .block import (
    StrfBlock as StrfBlock,
)
from .block import (
    StrictVariableGetterBlock as StrictVariableGetterBlock,
)
from .block import (
    SubstringBlock as SubstringBlock,
)
from .block import (
    UpperBlock as UpperBlock,
)
from .block import (
    URLEncodeBlock as URLEncodeBlock,
)
from .block import (
    build_components_v2_view as build_components_v2_view,
)
from .block import (
    helper_parse_if as helper_parse_if,
)
from .block import (
    helper_parse_list_if as helper_parse_list_if,
)
from .block import (
    helper_split as helper_split,
)
from .block import (
    implicit_bool as implicit_bool,
)
from .exceptions import (
    BadColourArgument as BadColourArgument,
)
from .exceptions import (
    ComponentParseError as ComponentParseError,
)
from .exceptions import (
    CooldownExceeded as CooldownExceeded,
)
from .exceptions import (
    EmbedParseError as EmbedParseError,
)
from .exceptions import (
    ProcessError as ProcessError,
)
from .exceptions import (
    StopError as StopError,
)
from .exceptions import (
    TagScriptError as TagScriptError,
)
from .exceptions import (
    WorkloadExceededError as WorkloadExceededError,
)
from .interface import (
    Adapter as Adapter,
)
from .interface import (
    Block as Block,
)
from .interface import (
    SimpleAdapter as SimpleAdapter,
)
from .interface import (
    verb_required_block as verb_required_block,
)
from .interpreter import (
    AsyncInterpreter as AsyncInterpreter,
)
from .interpreter import (
    Context as Context,
)
from .interpreter import (
    Interpreter as Interpreter,
)
from .interpreter import (
    Node as Node,
)
from .interpreter import (
    Response as Response,
)
from .interpreter import (
    build_node_tree as build_node_tree,
)
from .utils import (
    escape_content as escape_content,
)
from .utils import (
    maybe_await as maybe_await,
)
from .utils import (
    truncate as truncate,
)
from .verb import (
    Verb as Verb,
)

__all__: Tuple[str, ...] = (
    "implicit_bool",
    "helper_parse_if",
    "helper_parse_list_if",
    "helper_split",
    "AllowedMentionsBlock",
    "AllBlock",
    "AnyBlock",
    "AssignmentBlock",
    "BlacklistBlock",
    "BreakBlock",
    "SequentialGather",
    "CommandBlock",
    "ComponentBlock",
    "build_components_v2_view",
    "CooldownBlock",
    "EmbedBlock",
    "FiftyFiftyBlock",
    "IfBlock",
    "LooseVariableGetterBlock",
    "MathBlock",
    "OverrideBlock",
    "PythonBlock",
    "RandomBlock",
    "RangeBlock",
    "RedirectBlock",
    "ReplaceBlock",
    "RequireBlock",
    "ShortCutRedirectBlock",
    "SleepBlock",
    "StopBlock",
    "StrfBlock",
    "StrictVariableGetterBlock",
    "SubstringBlock",
    "URLEncodeBlock",
    "UpperBlock",
    "LowerBlock",
    "CountBlock",
    "LengthBlock",
    "JoinBlock",
    "ListBlock",
    "CycleBlock",
    "OrdinalBlock",
    "SafeObjectAdapter",
    "StringAdapter",
    "IntAdapter",
    "FunctionAdapter",
    "RedCommandAdapter",
    "RedBotAdapter",
    "AttributeAdapter",
    "DiscordAttributeAdapter",
    "UserAdapter",
    "MemberAdapter",
    "DMChannelAdapter",
    "ChannelAdapter",
    "GuildAdapter",
    "RoleAdapter",
    "DiscordObjectAdapter",
    "Adapter",
    "SimpleAdapter",
    "Block",
    "verb_required_block",
    "TagScriptEngineDeprecationWarning",
    "TagScriptError",
    "WorkloadExceededError",
    "ProcessError",
    "EmbedParseError",
    "BadColourArgument",
    "ComponentParseError",
    "StopError",
    "CooldownExceeded",
    "Interpreter",
    "AsyncInterpreter",
    "Context",
    "Response",
    "Node",
    "build_node_tree",
    "truncate",
    "escape_content",
    "maybe_await",
    "Verb",
    "__version__",
    "VersionInfo",
    "version_info",
)


__version__: Final[str] = "3.4.0"


class VersionNamedTuple(NamedTuple):
    major: int
    minor: int
    micro: int


class VersionInfo(VersionNamedTuple):
    """
    Version information.

    Attributes
    ----------
    major: int
        Major version number.
    minor: int
        Minor version number.
    micro: int
        Micro version number.
    """

    __slots__: Tuple[str, ...] = ()

    def __str__(self) -> str:
        """
        Returns a string representation of the version information.

        Returns
        -------
        str
            String representation of the version information.
        """
        return "{major}.{minor}.{micro}".format(**self._asdict())

    @classmethod
    def from_str(cls, version: str) -> "VersionInfo":
        """
        Returns a VersionInfo instance from a string.

        Parameters
        ----------
        version: str
            String representation of the version information.

        Returns
        -------
        VersionInfo
            Version information.
        """
        return cls(*map(int, version.split(".")))


version_info: VersionInfo = VersionInfo.from_str(__version__)
