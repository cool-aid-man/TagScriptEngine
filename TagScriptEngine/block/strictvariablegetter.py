from __future__ import annotations

from typing import Optional, Tuple, cast

from ..interface import Block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("StrictVariableGetterBlock",)


class StrictVariableGetterBlock(Block):
    """
    The strict variable block represents the adapters for any seeded or defined variables.
    This variable implementation is considered "strict" since it checks whether the variable is
    valid during :meth:`will_accept` and is only processed if the declaration refers to a valid
    variable.

    **Usage:** ``{<variable_name>([parameter]):[payload]}``

    **Aliases:** This block is valid for any variable name in `Response.variables`.

    **Payload:** Depends on the variable's underlying adapter.

    **Parameter:** Depends on the variable's underlying adapter.

    **Examples:** ::

        {=(var):This is my variable.}
        {var}
        # This is my variable.
    """

    def will_accept(self, ctx: Context) -> bool:  # type: ignore
        return ctx.verb.declaration in ctx.response.variables

    def process(self, ctx: Context) -> Optional[str]:
        # Re-check variable as ShortCutRedirectBlock may rewrite verbs post-approval (e.g., `{1}` -> `{args}`).
        # Returning None safely leaves the raw block if the target variable is undefined.
        adapter = ctx.response.variables.get(cast(str, ctx.verb.declaration))
        if adapter is None:
            return None
        return adapter.get_value(ctx.verb)
