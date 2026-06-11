from enum import Enum
from typing import Optional


class ThinkingMode(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"


class ReasoningEffort(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAX = "max"


THINKING_CONFIG = {
    "flash": {
        "disabled": {"extra_body": {"thinking": {"type": "disabled"}}},
        "low": {"reasoning_effort": "low", "extra_body": {"thinking": {"type": "enabled"}}},
        "high": {"reasoning_effort": "high", "extra_body": {"thinking": {"type": "enabled"}}},
        "max": {"reasoning_effort": "max", "extra_body": {"thinking": {"type": "enabled"}}},
    },
    "pro": {
        "disabled": {"extra_body": {"thinking": {"type": "disabled"}}},
        "low": {"reasoning_effort": "low", "extra_body": {"thinking": {"type": "enabled"}}},
        "high": {"reasoning_effort": "high", "extra_body": {"thinking": {"type": "enabled"}}},
        "max": {"reasoning_effort": "max", "extra_body": {"thinking": {"type": "enabled"}}},
    },
}


def get_optimal_thinking_config(
    task_complexity: str = "medium",
    task_type: str = "chat",
    model_variant: str = "flash",
) -> dict:
    """
    Return the optimal thinking mode config for a given task.

    task_complexity: "simple" | "medium" | "complex" | "agent"
    task_type: "chat" | "code" | "analysis" | "agent"
    model_variant: "flash" | "pro"
    """
    recommendations = {
        "simple": "disabled",
        "medium": "low",
        "complex": "high",
        "agent": "high",
    }
    effort = recommendations.get(task_complexity, "low")

    if task_type == "code" and task_complexity == "medium":
        effort = "low"

    variant = "flash" if model_variant == "flash" else "pro"
    return THINKING_CONFIG[variant][effort]


class MessageOptimizer:
    THINKING_DISABLED = {"extra_body": {"thinking": {"type": "disabled"}}}

    REASONING_EFFORTS = {
        "low": {"reasoning_effort": "low", "extra_body": {"thinking": {"type": "enabled"}}},
        "high": {"reasoning_effort": "high", "extra_body": {"thinking": {"type": "enabled"}}},
        "max": {"reasoning_effort": "max", "extra_body": {"thinking": {"type": "enabled"}}},
    }

    @staticmethod
    def disable_thinking(params: dict) -> dict:
        params.pop("reasoning_effort", None)
        params["extra_body"] = {"thinking": {"type": "disabled"}}
        return params

    @staticmethod
    def set_thinking_effort(params: dict, effort: str) -> dict:
        effort_map = {
            "low": "low",
            "medium": "low",
            "high": "high",
            "max": "max",
            "xhigh": "max",
        }
        mapped = effort_map.get(effort, "low")
        params["reasoning_effort"] = mapped
        params["extra_body"] = {"thinking": {"type": "enabled"}}
        return params

    @staticmethod
    def strip_reasoning_from_context(messages: list, last_was_tool_call: bool = False) -> list:
        if last_was_tool_call:
            return messages

        stripped = []
        for msg in messages:
            if msg.get("role") == "assistant":
                cleaned = {"role": "assistant", "content": msg.get("content", "")}
                if msg.get("tool_calls"):
                    cleaned["tool_calls"] = msg["tool_calls"]
                stripped.append(cleaned)
            else:
                stripped.append(msg)
        return stripped

    @staticmethod
    def estimate_tokens(text: str) -> int:
        if not text:
            return 0
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 0.6 + other_chars * 0.3)

    @staticmethod
    def estimate_message_tokens(messages: list) -> int:
        total = 0
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, str):
                total += MessageOptimizer.estimate_tokens(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        total += MessageOptimizer.estimate_tokens(part.get("text", ""))
            reasoning = msg.get("reasoning_content", "")
            if reasoning:
                total += MessageOptimizer.estimate_tokens(reasoning)
        return total

    @staticmethod
    def should_summarize(messages: list, threshold_tokens: int = 16000) -> bool:
        return MessageOptimizer.estimate_message_tokens(messages) > threshold_tokens