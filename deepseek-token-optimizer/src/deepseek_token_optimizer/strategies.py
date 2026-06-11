from typing import Optional

from .optimizer import MessageOptimizer, get_optimal_thinking_config, ThinkingMode, ReasoningEffort


__all__ = [
    "CacheFriendlyBuilder",
    "ThinkingMode",
    "ReasoningEffort",
    "get_optimal_thinking_config",
    "summarize_conversation",
    "compress_system_prompt",
]


class CacheFriendlyBuilder:
    """
    Build messages arrays that maximize DeepSeek's disk-based KV cache hits.

    Cache rules from DeepSeek docs:
    1. Cache units form at request boundaries (end of user input + end of model output)
    2. System detects common prefixes and persists them as cache units
    3. Fixed-interval cache points for long inputs/outputs
    4. MUST match a cache prefix unit EXACTLY to get a hit
    """

    def __init__(self, system_prompt: str = "", model_variant: str = "flash"):
        self._system = system_prompt
        self._model_variant = model_variant
        self._cache_seed: Optional[str] = None

    @property
    def system_prompt(self) -> str:
        return self._system

    def set_system_prompt(self, prompt: str):
        self._system = prompt
        self._cache_seed = None

    def build(self, user_content: str, history: Optional[list] = None) -> list:
        """
        Build cache-optimized messages array. System prompt always comes first
        (unchanged) to enable prefix cache hits. History is appended after the
        stable prefix region.
        """
        messages = []
        if self._system:
            messages.append({"role": "system", "content": self._system})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_content})
        return messages

    def build_multi_turn(
        self,
        turns: list[str],
        thinking_effort: Optional[str] = None,
    ) -> tuple:
        """
        Build a message array for multi-turn conversation where each turn
        reuses the same system+first-message prefix for cache hits.

        Returns (messages, api_params) tuple.
        """
        messages = []
        api_params = {}

        if self._system:
            messages.append({"role": "system", "content": self._system})

        for i, user_msg in enumerate(turns):
            messages.append({"role": "user", "content": user_msg})

        if thinking_effort:
            config = get_optimal_thinking_config(
                task_complexity="simple" if len(turns) == 1 else "medium",
                model_variant=self._model_variant,
            )
            api_params.update(config)

        return messages, api_params

    def warm_cache(
        self,
        warmup_content: str,
        client,
        model: str = "deepseek-v4-flash",
    ) -> str:
        """
        Send a lightweight warmup request to establish the cache prefix.
        Subsequent requests with the same system + warmup prefix will get cache hits.
        """
        messages = []
        if self._system:
            messages.append({"role": "system", "content": self._system})
        messages.append({"role": "user", "content": warmup_content})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1,
            extra_body={"thinking": {"type": "disabled"}},
        )
        return response.choices[0].message.content


def summarize_conversation(
    messages: list,
    client,
    model: str = "deepseek-v4-flash",
    max_summary_tokens: int = 500,
) -> list:
    """
    Summarize a long conversation history into a compact form, keeping only
    the summary + the most recent N turns.

    Returns a new messages list ready for the next API call.
    """
    if len(messages) <= 6:
        return messages

    to_summarize = messages[:-4]
    recent = messages[-4:]

    summary_prompt = (
        "Summarize the following conversation history in a concise paragraph. "
        "Keep all key facts, decisions, and context. "
        "Do NOT include pleasantries or meta-commentary.\n\n"
    )
    summary_prompt += "\n".join(
        f"[{m['role']}]: {str(m.get('content', ''))[:500]}" for m in to_summarize
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=max_summary_tokens,
            extra_body={"thinking": {"type": "disabled"}},
        )
        summary = response.choices[0].message.content
    except Exception:
        return messages

    result = []
    for msg in messages:
        if msg.get("role") == "system":
            result.append(msg)
            break

    result.append({"role": "user", "content": summary})
    result.append({"role": "assistant", "content": "Understood. I'll use this context going forward."})
    result.extend(recent)

    return result


def compress_system_prompt(prompt: str, target_tokens: int = 1500) -> str:
    """
    Compress a verbose system prompt by removing redundancies and condensing
    instructions. Estimates original/compressed token counts.
    """
    original_estimate = MessageOptimizer.estimate_tokens(prompt)

    if original_estimate <= target_tokens:
        return prompt

    lines = prompt.split("\n")
    compressed_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if compressed_lines and compressed_lines[-1] != "":
                compressed_lines.append("")
            continue
        if any(
            stripped.lower().startswith(prefix)
            for prefix in [
                "note:",
                "important:",
                "remember:",
                "please note",
                "keep in mind",
                "always remember",
            ]
        ):
            compressed_lines.append(stripped)
        else:
            if compressed_lines and compressed_lines[-1] == stripped:
                continue
            compressed_lines.append(stripped)

    compressed_prompt = "\n".join(compressed_lines)
    compressed_tokens = MessageOptimizer.estimate_tokens(compressed_prompt)

    while compressed_tokens > target_tokens and len(compressed_lines) > 5:
        pop_idx = max(len(compressed_lines) // 2, 1)
        compressed_lines.pop(pop_idx)
        compressed_prompt = "\n".join(compressed_lines)
        compressed_tokens = MessageOptimizer.estimate_tokens(compressed_prompt)

    return compressed_prompt