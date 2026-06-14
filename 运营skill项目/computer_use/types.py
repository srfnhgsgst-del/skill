from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


@dataclass
class Point:
    x: int
    y: int

    def to_tuple(self) -> tuple[int, int]:
        return (self.x, self.y)


class MouseButton(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class ActionType(str, Enum):
    SCREENSHOT = "screenshot"
    MOUSE_MOVE = "mouse_move"
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    MIDDLE_CLICK = "middle_click"
    DOUBLE_CLICK = "double_click"
    DRAG = "drag"
    SCROLL = "scroll"
    TYPE = "type"
    KEY_PRESS = "key_press"
    KEY_COMBO = "key_combo"
    WAIT = "wait"
    CURSOR_POSITION = "cursor_position"


@dataclass
class ActionResult:
    success: bool
    action_type: ActionType
    message: str = ""
    screenshot_before: bytes | None = None
    screenshot_after: bytes | None = None
    data: Any = None


@dataclass
class ScreenRegion:
    left: int = 0
    top: int = 0
    width: int | None = None
    height: int | None = None