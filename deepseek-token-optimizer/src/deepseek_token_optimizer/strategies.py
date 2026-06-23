import logging
from typing import Optional

from .optimizer import MessageOptimizer, get_optimal_thinking_config, ThinkingMode, ReasoningEffort, TokenBudget

logger = logging.getLogger(__name__)

__all__ = [
    "CacheFriendlyBuilder", "ThinkingMode", "ReasoningEffort",
    "get_optimal_thinking_config", "summarize_conversation",
    "dry_summarize", "compress_system_prompt",
]


class TokenizerError(Exception):
    pass


class CacheFriendlyBuilder:
    def __init__(self, system_prompt: str = "", model_variant: str = "flash"):
        self._system = system_prompt
        self._model_variant = model_variant

    @property
    def system_prompt(self) -> str:
        return self._system

    @property
    def estimated_prefix_tokens(self) -> int:
        return MessageOptimizer.estimate_tokens(self._system)

    def set_system_prompt(self, prompt: str):
        self._system = prompt

    def build(self, user_content: str, history: Optional[list] = None, thinking_params: Optional[dict] = None) -> tuple[list, dict]:
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

    def build_multi_turn(self, turns: list[str], thinking_effort: Optional[str] = None, task_complexity: str = "simple", task_type: str = "chat") -> tuple[list, dict]:
        messages = []
        api_params = {}
        if self._system:
            messages.append({"role": "system", "content": self._system})
        for user_msg in turns:
            messages.append({"role": "user", "content": user_msg})
        if thinking_effort is not None:
            api_params.update(MessageOptimizer.set_thinking_effort({}, thinking_effort))
        else:
            api_params.update(get_optimal_thinking_config(task_complexity, task_type, self._model_variant))
        return messages, api_params

    def warm_cache(self, warmup_content: str, client, model: str = "deepseek-v4-flash") -> str:
        messages = []
        if self._system:
            messages.append({"role": "system", "content": self._system})
        messages.append({"role": "user", "content": warmup_content})
        response = client.chat.completions.create(
            model=model, messages=messages, max_tokens=1,
            extra_body={"thinking": {"type": "disabled"}},
        )
        return response.choices[0].message.content


def summarize_conversation(messages: list, client, model: str = "deepseek-v4-flash", max_summary_tokens: int = 500, char_limit: int = 2000) -> list:
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
        f"[{m['role']}]: {str(m.get('content', ''))[:char_limit]}" for m in to_summarize
    )
    try:
        response = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=max_summary_tokens, extra_body={"thinking": {"type": "disabled"}},
        )
        summary = response.choices[0].message.content
    except Exception as e:
        raise TokenizerError(f"Summarization failed (model={model}, msgs={len(messages)}): {e}") from e
    result = []
    for msg in messages:
        if msg.get("role") == "system":
            result.append(msg)
            break
    result.append({"role": "user", "content": f"[Previous conversation summary]\n{summary}\n[/Summary]"})
    result.append({"role": "assistant", "content": "Understood. I'll use this summarized context going forward."})
    result.extend(recent)
    logger.info(
        "Summarized: %d -> %d tokens (%.0f%% reduction)",
        MessageOptimizer.estimate_message_tokens(messages),
        MessageOptimizer.estimate_message_tokens(result),
        (1 - MessageOptimizer.estimate_message_tokens(result) / max(MessageOptimizer.estimate_message_tokens(messages), 1)) * 100,
    )
    return result


def dry_summarize(messages: list, max_summary_tokens: int = 500) -> TokenBudget:
    return MessageOptimizer.should_summarize(messages, threshold_tokens=12000, threshold_messages=10)


def compress_system_prompt(prompt: str, target_tokens: int = 1500) -> str:
    if MessageOptimizer.estimate_tokens(prompt) <= target_tokens:
        return prompt
    DIRECTIVE_TAGS = {"must", "do ", "do not", "don't", "note:", "important:", "warning:", "critical:", "always", "never", "required", "forbidden", "example:", "usage:"}
    lines = prompt.split("\n")
    preserved, prose_buffer, result = [], [], []

    def flush_prose():
        if prose_buffer:
            t = " ".join(prose_buffer).strip()
            if t: result.append(t)
            prose_buffer.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_prose()
            if result and result[-1] != "": result.append("")
            continue
        if any(stripped.lower().startswith(tag) for tag in DIRECTIVE_TAGS):
            flush_prose()
            if not result or result[-1] != stripped: result.append(stripped)
        else:
            if not (prose_buffer and prose_buffer[-1] == stripped):
                prose_buffer.append(stripped)
    flush_prose()
    compressed = "\n".join(l for l in result if l != "")
    if MessageOptimizer.estimate_tokens(compressed) <= target_tokens:
        return compressed
    sections = compressed.split("\n")
    truncated, tokens_used = [], 0
    for section in sections:
        sec_tokens = MessageOptimizer.estimate_tokens(section)
        if tokens_used + sec_tokens <= target_tokens:
            truncated.append(section)
            tokens_used += sec_tokens
        else:
            remaining = target_tokens - tokens_used
            if remaining > 20:
                truncated.append(section[:remaining * 3] + "...")
            break
    return "\n".join(truncated)