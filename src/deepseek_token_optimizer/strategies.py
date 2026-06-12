import logging
from typing import Optional

from .optimizer import (
    MessageOptimizer,
    get_optimal_thinking_config,
    ThinkingMode,
    ReasoningEffort,
    TokenBudget,
)
from .pricing import DEFAULT_MODEL

logger = logging.getLogger(__name__)

__all__ = [
    "CacheFriendlyBuilder",
    "ThinkingMode",
    "ReasoningEffort",
    "get_optimal_thinking_config",
    "summarize_conversation",
    "dry_summarize",
    "compress_system_prompt",
]


class TokenizerError(Exception):
    pass


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
        self._prefix_established = False

    @property
    def system_prompt(self) -> str:
        return self._system

    @property
    def estimated_prefix_tokens(self) -> int:
        return MessageOptimizer.estimate_tokens(self._system)

    def set_system_prompt(self, prompt: str):
        self._system = prompt
        self._prefix_established = False

    def build(
        self,
        user_content: str,
        history: Optional[list] = None,
        thinking_params: Optional[dict] = None,
    ) -> tuple[list, dict]:
        """
        Build cache-optimized messages array and API params.

        Returns (messages, api_params) tuple. The messages array places
        the system prompt first (unchanged) to maximize cache hit probability.
        Appended history MUST start after the common prefix region.

        thinking_params: optional dict to merge into API params (e.g., from
        get_optimal_thinking_config).
        """
        messages = []
        if self._system:
            messages.append({"role": "system", "content": self._system})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_content})

        api_params = {}
        if thinking_params:
            api_params.update(thinking_params)

        return messages, api_params

    def build_multi_turn(
        self,
        turns: list[str],
        thinking_effort: Optional[str] = None,
        task_complexity: str = "simple",
        task_type: str = "chat",
    ) -> tuple[list, dict]:
        """
        Build message array for multi-turn conversation.

        thinking_effort: directly set effort level ("low"/"high"/"max").
            When provided, overrides task_complexity/task_type detection.
            When None, auto-detects optimal effort from task metadata.
        """
        messages = []
        api_params = {}

        if self._system:
            messages.append({"role": "system", "content": self._system})

        for user_msg in turns:
            messages.append({"role": "user", "content": user_msg})

        if thinking_effort is not None:
            api_params.update(
                MessageOptimizer.set_thinking_effort({}, thinking_effort)
            )
        else:
            config = get_optimal_thinking_config(
                task_complexity=task_complexity,
                task_type=task_type,
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

        Returns the assistant's response content (typically 1 token).
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
        self._prefix_established = True
        return response.choices[0].message.content


def summarize_conversation(
    messages: list,
    client,
    model: str = "deepseek-v4-flash",
    max_summary_tokens: int = 500,
    char_limit: int = 2000,
) -> list:
    """
    Summarize a long conversation history into a compact form.

    Keeps the system prompt, injects a summary paragraph, then appends
    the 4 most recent turns. Uses a separate lightweight API call for
    the summary to avoid polluting the main conversation.

    Raises TokenizerError on API failure — no longer silently returns
    the original messages.
    """
    if len(messages) <= 6:
        return messages

    to_summarize = messages[:-4]
    recent = messages[-4:]

    summary_prompt = (
        "Summarize the following conversation history in a concise paragraph. "
        "Keep all key facts, decisions, code snippets, and context. "
        "Do NOT include pleasantries or meta-commentary.\n\n"
    )
    summary_prompt += "\n".join(
        f"[{m['role']}]: {str(m.get('content', ''))[:char_limit]}"
        for m in to_summarize
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=max_summary_tokens,
            extra_body={"thinking": {"type": "disabled"}},
        )
        summary = response.choices[0].message.content
    except Exception as e:
        raise TokenizerError(
            f"Conversation summarization failed (model={model}, "
            f"messages={len(messages)}): {e}"
        ) from e

    result = []
    for msg in messages:
        if msg.get("role") == "system":
            result.append(msg)
            break

    result.append(
        {
            "role": "user",
            "content": f"[Previous conversation summary]\n{summary}\n[/Summary]",
        }
    )
    result.append(
        {
            "role": "assistant",
            "content": "Understood. I'll use this summarized context going forward.",
        }
    )
    result.extend(recent)

    original_tokens = MessageOptimizer.estimate_message_tokens(messages)
    compressed_tokens = MessageOptimizer.estimate_message_tokens(result)
    logger.info(
        "Summarized conversation: %d -> %d tokens (%.0f%% reduction)",
        original_tokens,
        compressed_tokens,
        (1 - compressed_tokens / max(original_tokens, 1)) * 100,
    )

    return result


def dry_summarize(messages: list, max_summary_tokens: int = 500) -> TokenBudget:
    """
    Estimate if summarization would help without making an API call.
    Returns a TokenBudget with recommendation.
    """
    return MessageOptimizer.should_summarize(
        messages,
        threshold_tokens=12000,
        threshold_messages=10,
    )


def compress_system_prompt(prompt: str, target_tokens: int = 1500) -> str:
    """
    Compress a verbose system prompt using semantic-section-aware logic.

    v1.1 improvement over v1.0: instead of randomly deleting from the middle,
    this version:
      1. Preserves tagged directives (MUST, DO, DON'T, NOTE, IMPORTANT)
      2. Collapses consecutive prose lines into condensed paragraphs
      3. Deduplicates semantically identical lines
      4. Truncates from the END of prose sections only when necessary
    """
    original_estimate = MessageOptimizer.estimate_tokens(prompt)
    if original_estimate <= target_tokens:
        return prompt

    DIRECTIVE_TAGS = {
        "must", "do ", "do not", "don't", "dont",
        "note:", "important:", "warning:", "critical:",
        "always", "never", "required", "forbidden",
        "example:", "usage:",
    }

    lines = prompt.split("\n")
    preserved: list[str] = []
    prose_buffer: list[str] = []
    result: list[str] = []

    def flush_prose():
        nonlocal result
        if not prose_buffer:
            return
        text = " ".join(prose_buffer).strip()
        if text:
            result.append(text)
        prose_buffer.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_prose()
            if result and result[-1] != "":
                result.append("")
            continue

        is_directive = any(
            stripped.lower().startswith(tag) for tag in DIRECTIVE_TAGS
        )
        if is_directive:
            flush_prose()
            if not result or result[-1] != stripped:
                result.append(stripped)
        else:
            if prose_buffer and prose_buffer[-1] == stripped:
                continue
            prose_buffer.append(stripped)

    flush_prose()

    compressed = "\n".join(line for line in result if line != "")

    current_tokens = MessageOptimizer.estimate_tokens(compressed)
    if current_tokens <= target_tokens:
        return compressed

    sections = compressed.split("\n")
    truncated: list[str] = []
    tokens_used = 0

    for section in sections:
        sec_tokens = MessageOptimizer.estimate_tokens(section)
        if tokens_used + sec_tokens <= target_tokens:
            truncated.append(section)
            tokens_used += sec_tokens
        else:
            remaining = target_tokens - tokens_used
            if remaining > 20 and len(section) > remaining:
                truncated.append(section[: remaining * 3] + "...")
            break

    return "\n".join(truncated)