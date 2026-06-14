from __future__ import annotations

import time

import pyautogui


def type_text(text: str, interval: float = 0.02) -> None:
    pyautogui.typewrite(text, interval=interval)


def press(key: str) -> None:
    pyautogui.press(key)


def hotkey(*keys: str) -> None:
    pyautogui.hotkey(*keys)


def key_down(key: str) -> None:
    pyautogui.keyDown(key)


def key_up(key: str) -> None:
    pyautogui.keyUp(key)


def write(text: str, interval: float = 0.0) -> None:
    pyautogui.write(text, interval=interval)


def paste() -> None:
    hotkey("ctrl", "v")


def select_all() -> None:
    hotkey("ctrl", "a")


def copy() -> None:
    hotkey("ctrl", "c")


def enter() -> None:
    press("enter")


def escape() -> None:
    press("esc")


def tab() -> None:
    press("tab")


def wait(seconds: float) -> None:
    time.sleep(seconds)