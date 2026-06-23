import json
from enum import Enum
from typing import Optional, NamedTuple


class ThinkingMode(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"


class ReasoningEffort(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAX = "max"


class TokenBudget(NamedTuple):
    should_summarize: bool
    estimated_tokens: int
    threshold_tokens: int
    message_count: int
    reason: str


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

TASK_EFFORT_MAP = {
    ("simple", "chat"): "disabled",
    ("simple", "code"): "disabled",
    ("simple", "analysis"): "disabled",
    ("simple", "agent"): "disabled",
    ("medium", "chat"): "low",
    ("medium", "code"): "low",
    ("medium", "analysis"): "high",
    ("medium", "agent"): "high",
    ("complex", "chat"): "high",
    ("complex", "code"): "high",
    ("complex", "analysis"): "high",
    ("complex", "agent"): "max",
    ("agent", "chat"): "high",
    ("agent", "code"): "high",
    ("agent", "analysis"): "max",
    ("agent", "agent"): "max",
}


def get_optimal_thinking_config(
    task_complexity: str = "medium",
    task_type: str = "chat",
    model_variant: str = "flash",
) -> dict:
    effort = TASK_EFFORT_MAP.get(
        (task_complexity, task_type),
        TASK_EFFORT_MAP.get((task_complexity, "chat"), "low"),
    )
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
        effort_map = {"low": "low", "medium": "low", "high": "high", "max": "max", "xhigh": "max"}
        mapped = effort_map.get(effort, "low")
        params["reasoning_effort"] = mapped
        params["extra_body"] = {"thinking": {"type": "enabled"}}
        return params

    @staticmethod
    def is_thinking_enabled(params: dict) -> bool:
        extra = params.get("extra_body", {})
        thinking = extra.get("thinking", {})
        return thinking.get("type") != "disabled"

    @staticmethod
    def strip_reasoning_smart(messages: list) -> list:
        stripped = []
        for msg in messages:
            if msg.get("role") == "assistant":
                has_tool_calls = bool(msg.get("tool_calls"))
                cleaned = {"role": "assistant", "content": msg.get("content", "")}
                if has_tool_calls:
                    cleaned["reasoning_content"] = msg.get("reasoning_content", "")
                    cleaned["tool_calls"] = msg["tool_calls"]
                stripped.append(cleaned)
            else:
                stripped.append(msg)
        return stripped

    @staticmethod
    def estimate_tokens(text: str) -> int:
        if not text:
            return 0
        cjk_ranges = [
            (0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0xAC00, 0xD7AF),
            (0x3040, 0x30FF), (0x31F0, 0x31FF),
        ]
        tokens = 0.0
        consecutive = 0
        for c in text:
            cp = ord(c)
            is_cjk = any(lo <= cp <= hi for lo, hi in cjk_ranges)
            if is_cjk:
                if consecutive:
                    tokens += consecutive * 0.3; consecutive = 0
                tokens += 0.6
            else:
                consecutive += 1
        if consecutive:
            tokens += consecutive * 0.3
        return max(1, int(tokens))

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
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    total += MessageOptimizer.estimate_tokens(
                        json.dumps(tc.get("function", {}), ensure_ascii=False)
                    )
        return total

    @staticmethod
    def should_summarize(
        messages: list,
        threshold_tokens: int = 16000,
        threshold_messages: int = 12,
    ) -> TokenBudget:
        tokens = MessageOptimizer.estimate_message_tokens(messages)
        msg_count = len(messages)
        reasons = []
        if tokens > threshold_tokens:
            reasons.append(f"token count {tokens} > {threshold_tokens}")
        if msg_count > threshold_messages:
            reasons.append(f"message count {msg_count} > {threshold_messages}")
        return TokenBudget(
            should_summarize=len(reasons) > 0,
            estimated_tokens=tokens,
            threshold_tokens=threshold_tokens,
            message_count=msg_count,
            reason="; ".join(reasons) if reasons else "within limits",
        )