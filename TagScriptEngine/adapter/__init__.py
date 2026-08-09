from __future__ import annotations

from typing import Tuple

from .discordadapters import (
    AttributeAdapter as AttributeAdapter,
)
from .discordadapters import (
    ChannelAdapter as ChannelAdapter,
)
from .discordadapters import (
    DiscordAttributeAdapter as DiscordAttributeAdapter,
)
from .discordadapters import (
    DiscordObjectAdapter as DiscordObjectAdapter,
)
from .discordadapters import (
    DMChannelAdapter as DMChannelAdapter,
)
from .discordadapters import (
    GuildAdapter as GuildAdapter,
)
from .discordadapters import (
    MemberAdapter as MemberAdapter,
)
from .discordadapters import (
    RoleAdapter as RoleAdapter,
)
from .discordadapters import (
    UserAdapter as UserAdapter,
)
from .functionadapter import (
    FunctionAdapter as FunctionAdapter,
)
from .intadapter import (
    IntAdapter as IntAdapter,
)
from .objectadapter import (
    SafeObjectAdapter as SafeObjectAdapter,
)
from .redbotadapters import (
    RedBotAdapter as RedBotAdapter,
)
from .redbotadapters import (
    RedCommandAdapter as RedCommandAdapter,
)
from .stringadapter import (
    StringAdapter as StringAdapter,
)

__all__: Tuple[str, ...] = (
    "SafeObjectAdapter",
    "StringAdapter",
    "IntAdapter",
    "FunctionAdapter",
    "AttributeAdapter",
    "DiscordAttributeAdapter",
    "UserAdapter",
    "MemberAdapter",
    "DMChannelAdapter",
    "ChannelAdapter",
    "GuildAdapter",
    "RoleAdapter",
    "DiscordObjectAdapter",
    "RedCommandAdapter",
    "RedBotAdapter",
)
