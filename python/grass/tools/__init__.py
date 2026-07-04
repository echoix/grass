from __future__ import annotations
from tools.session_tools import Tools
from tools.session_tools import ToolError
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from typing import Literal
    from .session_tools import Tools
    from .session_tools import ToolError


@overload
def __getattr__(name: Literal["Tools"]) -> type[Tools]:
    pass


@overload
def __getattr__(name: Literal["ToolError"]) -> type[ToolError]:
    pass


def __getattr__(name) -> type[ToolError | Tools]:
    if name == "Tools":
        from .session_tools import Tools

        return Tools
    if name == "ToolError":
        from .session_tools import ToolError

        return ToolError
    msg = f"module {__name__} has no attribute {name}"
    raise AttributeError(msg)


__all__ = ["Tools"]  # pylint: disable=undefined-all-variable
