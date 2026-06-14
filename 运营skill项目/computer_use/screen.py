from __future__ import annotations

import io
from typing import Any

import mss
import mss.tools
import pyautogui
from PIL import Image

from .types import Point, ScreenRegion

# pyautogui 默认有 0.1 秒的安全间隔，可调
pyautogui.PAUSE = 0.05
pyautogui.FAILSAFE = True


def screenshot(region: ScreenRegion | None = None) -> bytes:
    """截屏并返回 PNG 格式的 bytes"""
    if region is None:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            raw = sct.grab(monitor)
            return mss.tools.to_png(raw.rgb, raw.size)

    with mss.mss() as sct:
        monitor = {
            "left": region.left,
            "top": region.top,
            "width": region.width or sct.monitors[1]["width"],
            "height": region.height or sct.monitors[1]["height"],
        }
        raw = sct.grab(monitor)
        return mss.tools.to_png(raw.rgb, raw.size)


def screenshot_pil(region: ScreenRegion | None = None) -> Image.Image:
    """截屏并返回 PIL Image 对象"""
    data = screenshot(region)
    return Image.open(io.BytesIO(data))


def screen_size() -> tuple[int, int]:
    size = pyautogui.size()
    return (size.width, size.height)


def locate_on_screen(
    image_path: str,
    confidence: float = 0.9,
    region: ScreenRegion | None = None,
) -> Point | None:
    """在屏幕上查找图片位置"""
    kwargs: dict[str, Any] = {"confidence": confidence}
    if region:
        kwargs["region"] = (region.left, region.top, region.width or 0, region.height or 0)

    try:
        loc = pyautogui.locateOnScreen(image_path, **kwargs)
        if loc is None:
            return None
        return Point(x=loc.left + loc.width // 2, y=loc.top + loc.height // 2)
    except pyautogui.ImageNotFoundException:
        return None


def pixel_color(x: int, y: int) -> tuple[int, int, int]:
    return pyautogui.pixel(x, y)