from __future__ import annotations

import base64
from typing import Any

from . import keyboard, mouse, screen
from .types import ActionResult, ActionType, MouseButton, Point, ScreenRegion


class Controller:
    """统一控制器：组合 截图 + 鼠标 + 键盘 操作"""

    # ---- 屏幕 ----

    def screenshot(self, region: ScreenRegion | None = None) -> bytes:
        return screen.screenshot(region)

    def screenshot_base64(self, region: ScreenRegion | None = None) -> str:
        """返回 base64 data URL，可直接喂给多模态模型"""
        data = screen.screenshot(region)
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"

    def screen_size(self) -> tuple[int, int]:
        return screen.screen_size()

    def locate(self, image_path: str, confidence: float = 0.9) -> Point | None:
        return screen.locate_on_screen(image_path, confidence)

    def pixel(self, x: int, y: int) -> tuple[int, int, int]:
        return screen.pixel_color(x, y)

    # ---- 鼠标 ----

    def move_to(self, x: int, y: int, duration: float = 0.3) -> None:
        mouse.move_to(x, y, duration)

    def move_rel(self, dx: int, dy: int, duration: float = 0.3) -> None:
        mouse.move_rel(dx, dy, duration)

    def position(self) -> Point:
        return mouse.position()

    def click(self, x: int | None = None, y: int | None = None) -> None:
        mouse.click(x, y)

    def right_click(self, x: int | None = None, y: int | None = None) -> None:
        mouse.right_click(x, y)

    def double_click(self, x: int | None = None, y: int | None = None) -> None:
        mouse.double_click(x, y)

    def drag(self, start: tuple[int, int], end: tuple[int, int], duration: float = 0.5) -> None:
        mouse.drag(start[0], start[1], end[0], end[1], duration)

    def scroll_up(self, clicks: int = 3) -> None:
        mouse.scroll_up(clicks)

    def scroll_down(self, clicks: int = 3) -> None:
        mouse.scroll_down(clicks)

    # ---- 键盘 ----

    def type(self, text: str, interval: float = 0.02) -> None:
        keyboard.type_text(text, interval)

    def press(self, key: str) -> None:
        keyboard.press(key)

    def hotkey(self, *keys: str) -> None:
        keyboard.hotkey(*keys)

    def key_down(self, key: str) -> None:
        keyboard.key_down(key)

    def key_up(self, key: str) -> None:
        keyboard.key_up(key)

    def paste(self) -> None:
        keyboard.paste()

    def enter(self) -> None:
        keyboard.enter()

    def wait(self, seconds: float) -> None:
        keyboard.wait(seconds)

    # ---- 组合操作 ----

    def click_at_text(
        self,
        image_path: str,
        confidence: float = 0.9,
    ) -> bool:
        """在屏幕上查找图片并点击"""
        loc = self.locate(image_path, confidence)
        if loc is None:
            return False
        self.click(loc.x, loc.y)
        return True

    def type_to_field(
        self,
        field_image: str,
        text: str,
        confidence: float = 0.9,
    ) -> bool:
        """找到输入框图片 → 点击 → 键入文本"""
        if not self.click_at_text(field_image, confidence):
            return False
        self.hotkey("ctrl", "a")
        self.type(text)
        return True

    def execute(self, action: dict[str, Any]) -> ActionResult:
        """根据字典执行单个动作，便于 AI 生成结构化指令"""
        action_type = action["type"]
        params: dict[str, Any] = action.get("params", {})

        try:
            before = self.screenshot()

            if action_type == "screenshot":
                result_data = None

            elif action_type == "mouse_move":
                self.move_to(params["x"], params["y"], params.get("duration", 0.3))
                result_data = None

            elif action_type == "left_click":
                self.click(params.get("x"), params.get("y"))
                result_data = None

            elif action_type == "right_click":
                self.right_click(params.get("x"), params.get("y"))
                result_data = None

            elif action_type == "double_click":
                self.double_click(params.get("x"), params.get("y"))
                result_data = None

            elif action_type == "drag":
                self.drag(
                    (params["start_x"], params["start_y"]),
                    (params["end_x"], params["end_y"]),
                    params.get("duration", 0.5),
                )
                result_data = None

            elif action_type == "scroll":
                amount = params.get("amount", 3)
                if amount > 0:
                    self.scroll_up(amount)
                else:
                    self.scroll_down(-amount)
                result_data = None

            elif action_type == "type":
                self.type(params["text"], params.get("interval", 0.02))
                result_data = None

            elif action_type == "key_press":
                self.press(params["key"])
                result_data = None

            elif action_type == "key_combo":
                self.hotkey(*params["keys"])
                result_data = None

            elif action_type == "wait":
                self.wait(params.get("seconds", 1.0))
                result_data = None

            elif action_type == "cursor_position":
                pos = self.position()
                result_data = pos.to_tuple()

            else:
                return ActionResult(False, ActionType(action_type), f"未知动作类型: {action_type}")

            after = self.screenshot()
            return ActionResult(
                True,
                ActionType(action_type),
                screenshot_before=before,
                screenshot_after=after,
                data=result_data,
            )

        except Exception as e:
            return ActionResult(False, ActionType(action_type), str(e))

    def execute_batch(self, actions: list[dict[str, Any]]) -> list[ActionResult]:
        """批量执行动作序列"""
        results: list[ActionResult] = []
        for action in actions:
            result = self.execute(action)
            results.append(result)
            if not result.success:
                break
            if action["type"] == "wait":
                continue
        return results