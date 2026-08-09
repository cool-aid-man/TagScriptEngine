from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Generic, Optional, Tuple, TypeVar

from ..utils import escape_content

if TYPE_CHECKING:
    from ..verb import Verb


_T = TypeVar("_T", bound=object)

_log: logging.Logger = logging.getLogger(__name__)


__all__: Tuple[str, ...] = ("Adapter", "SimpleAdapter")

# Default for missing attributes. Uses "" rather than None (leaks raw block) or False (renders "False").
MISSING: str = ""


class Adapter:
    """
    The base class for TagScript adapters.

    Implementations must subclass this to create adapters.
    """

    __slots__: Tuple[str, ...] = ()

    def __repr__(self) -> str:
        return f"<{type(self).__qualname__} at {hex(id(self))}>"

    def get_value(self, ctx: Verb) -> Optional[str]:
        """
        Processes the adapter's actions for a given :class:`~TagScriptEngine.verb.Verb`.

        Subclasses must implement this.

        Parameters
        ----------
        ctx: Verb
            The context object containing the TagScript :class:`~TagScriptEngine.verb.Verb`.

        Returns
        -------
        Optional[str]
            The adapters's processed value.

        Raises
        ------
        NotImplementedError
            The subclass did not implement this required method.
        """
        raise NotImplementedError


class SimpleAdapter(Adapter, Generic[_T]):
    """
    An adapter backed by a dict of attributes and a dict of zero-argument
    methods, resolved by the verb's parameter.

    Subclasses populate them in :meth:`update_attributes` /
    :meth:`update_methods` and normally do not override :meth:`get_value`.
    """

    __slots__: Tuple[str, ...] = ("object", "_attributes", "_methods")

    def __init__(self, *, base: _T, defaults: Optional[Dict[str, Any]] = None) -> None:
        self.object: _T = base
        # Seeded before update_attributes() so a subclass can override them.
        self._attributes: Dict[str, Any] = dict(defaults) if defaults else {}
        self._methods: Dict[str, Any] = {}
        self.update_attributes()
        self.update_methods()

    def __repr__(self) -> str:
        return f"<{type(self).__qualname__} object={self.object!r}>"

    def update_attributes(self) -> None:
        pass

    def update_methods(self) -> None:
        pass

    def default_value(self) -> str:
        """The value for a verb with no parameter, e.g. a bare ``{user}``."""
        return str(self.object)

    def resolve(self, parameter: str) -> Any:
        """
        Look a parameter up. Returns ``None`` when the name is unknown, which
        the caller renders as :data:`MISSING`.

        Override to gate or lazily compute particular names.
        """
        if parameter in self._attributes:
            return self._attributes[parameter]
        if method := self._methods.get(parameter):
            return method()
        _log.debug("No parameter named %r on the %s adapter.", parameter, type(self).__name__)
        return None

    def get_value(self, ctx: Verb) -> Optional[str]:
        if ctx.parameter is None:
            return self.default_value()
        value = self.resolve(ctx.parameter)
        should_escape = False
        # An attribute may declare its own escaping as a (value, escape) pair.
        if isinstance(value, tuple):
            value, should_escape = value
        if value is None:
            return MISSING
        return escape_content(str(value)) if should_escape else str(value)
