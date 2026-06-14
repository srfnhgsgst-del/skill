from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from .controller import Controller
from .types import ActionResult


class ComputerUseAgent(ABC):
    """Computer Use Agent 抽象基类

    子类需要实现 _ask_model()，对接具体的 AI 后端。
    """

    def __init__(self, controller: Controller | None = None):
        self.controller = controller or Controller()

    @abstractmethod
    def _ask_model(self, screenshot_b64: str, task: str, history: list[dict[str, Any]]) -> dict[str, Any]:
        """调用 AI 模型，返回下一步动作字典。

        返回格式:
            {
                "thought": "当前思考",
                "action": {"type": "...", "params": {...}},
                "done": false
            }
        """
        ...

    def run(self, task: str, max_steps: int = 20) -> list[ActionResult]:
        """执行一个完整的 Computer Use 任务"""
        results: list[ActionResult] = []
        history: list[dict[str, Any]] = []

        for step in range(max_steps):
            screenshot_b64 = self.controller.screenshot_base64()

            try:
                response = self._ask_model(screenshot_b64, task, history)
            except Exception as e:
                results.append(ActionResult(False, "screenshot", f"模型调用失败: {e}"))
                break

            thought = response.get("thought", "")
            action = response.get("action", {})
            done = response.get("done", False)

            print(f"[Step {step + 1}] {thought}")
            print(f"  动作: {json.dumps(action, ensure_ascii=False)}")

            result = self.controller.execute(action)
            results.append(result)

            history.append({
                "step": step + 1,
                "thought": thought,
                "action": action,
                "success": result.success,
                "message": result.message,
            })

            if done:
                print(f"[完成] {thought}")
                break

            if not result.success:
                print(f"[错误] {result.message}")

        return results

    def take_screenshot(self) -> bytes:
        return self.controller.screenshot()

    def get_state(self) -> dict[str, Any]:
        """获取当前状态（供 AI 决策用）"""
        pos = self.controller.position()
        size = self.controller.screen_size()
        screenshot_b64 = self.controller.screenshot_base64()

        return {
            "screenshot": screenshot_b64,
            "cursor_position": pos.to_tuple(),
            "screen_size": size,
        }

    @staticmethod
    def parse_response(raw_text: str) -> dict[str, Any]:
        """从 LLM 原始输出中解析动作 JSON"""
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        brace_match = re.search(r"\{[\s\S]*\}", raw_text)
        if brace_match:
            return json.loads(brace_match.group(0))

        return {"thought": raw_text, "action": {"type": "wait", "params": {"seconds": 1}}, "done": False}


class MockAgent(ComputerUseAgent):
    """测试用 Agent，执行预定义的动作序列"""

    def __init__(self, actions: list[dict[str, Any]], controller: Controller | None = None):
        super().__init__(controller)
        self._actions = actions
        self._index = 0

    def _ask_model(self, screenshot_b64: str, task: str, history: list[dict[str, Any]]) -> dict[str, Any]:
        if self._index >= len(self._actions):
            return {
                "thought": "所有动作已执行完毕",
                "action": {"type": "wait", "params": {"seconds": 0}},
                "done": True,
            }
        action = self._actions[self._index]
        self._index += 1
        done = self._index >= len(self._actions)
        return {
            "thought": f"执行预设动作 {self._index}/{len(self._actions)}",
            "action": action,
            "done": done,
        }