from __future__ import annotations

import pyautogui

from .types import MouseButton, Point


def move_to(x: int, y: int, duration: float = 0.3, tween: str = "easeInOutQuad") -> None:
    pyautogui.moveTo(x, y, duration=duration, tween=tween)


def move_rel(dx: int, dy: int, duration: float = 0.3) -> None:
    pyautogui.moveRel(dx, dy, duration=duration)


def position() -> Point:
    pos = pyautogui.position()
    return Point(x=pos.x, y=pos.y)


def click(x: int | None = None, y: int | None = None, button: MouseButton = MouseButton.LEFT) -> None:
    if x is not None and y is not None:
        move_to(x, y)
    pyautogui.click(button=button.value)


def double_click(x: int | None = None, y: int | None = None) -> None:
    if x is not None and y is not None:
        move_to(x, y)
    pyautogui.doubleClick()


def right_click(x: int | None = None, y: int | None = None) -> None:
    click(x, y, MouseButton.RIGHT)


def drag(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration: float = 0.5,
    button: MouseButton = MouseButton.LEFT,
) -> None:
    move_to(start_x, start_y)
    pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration, button=button.value)


def scroll(clicks: int, x: int | None = None, y: int | None = None) -> None:
    if x is not None and y is not None:
        move_to(x, y)
    pyautogui.scroll(clicks)


def scroll_up(clicks: int = 3) -> None:
    scroll(clicks)


def scroll_down(clicks: int = 3) -> None:
    scroll(-clicks)