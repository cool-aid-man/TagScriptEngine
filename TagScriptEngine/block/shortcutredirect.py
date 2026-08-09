from typing import Optional, Tuple, cast

from ..interface import Block
from ..interpreter import Context
from ..verb import Verb

__all__: Tuple[str, ...] = ("ShortCutRedirectBlock",)


class ShortCutRedirectBlock(Block):
    """
    Rewrites a bare numeric block into an indexed lookup on a named variable,
    so ``{1}`` behaves as ``{args(1)}``.

    This block never produces output itself: it swaps the verb and returns
    ``None`` so a later variable getter resolves the rewritten verb. It must
    therefore be registered *before* those getters.

    **Usage:** ``{<index>([delimiter])}``

    **Payload:** delimiter, None

    **Parameter:** None

    **Examples:** ::

        {1}
        # with args "hello world" -> hello

        {2:,}
        # with args "a,b,c" -> b
    """

    def __init__(self, var_name: str) -> None:
        self.redirect_name: str = var_name

    @classmethod
    def will_accept(cls, ctx: Context) -> bool:
        return cast(str, ctx.verb.declaration).isdigit()

    def process(self, ctx: Context) -> Optional[str]:
        redirect: Verb = Verb()
        redirect.declaration = self.redirect_name
        redirect.parameter = ctx.verb.declaration
        # Keep the payload: it is the adapter's delimiter, so dropping it made
        # `{1:,}` silently split on spaces instead.
        redirect.payload = ctx.verb.payload
        ctx.verb = redirect
        return None
