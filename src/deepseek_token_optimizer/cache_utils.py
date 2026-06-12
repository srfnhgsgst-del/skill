from .pricing import get_pricing


def check_cache_hit(response_usage: dict) -> tuple[int, int, float]:
    """
    Parse a DeepSeek API response usage block and return
    (cache_hit_tokens, cache_miss_tokens, hit_rate).
    """
    hit = response_usage.get("prompt_cache_hit_tokens", 0)
    miss = response_usage.get("prompt_cache_miss_tokens", 0)
    total = hit + miss
    rate = hit / total if total > 0 else 0.0
    return hit, miss, rate


def compute_cache_savings(
    cache_hit_tokens: int,
    cache_miss_tokens: int,
    model: str = "deepseek-v4-flash",
) -> dict:
    """
    Calculate the cost savings from cache hits vs hypothetical all-miss scenario.
    """
    p = get_pricing(model)
    hit_cost = (cache_hit_tokens / 1_000_000) * p["cache_hit"]
    miss_cost = (cache_miss_tokens / 1_000_000) * p["cache_miss"]
    actual = hit_cost + miss_cost
    hypothetical = ((cache_hit_tokens + cache_miss_tokens) / 1_000_000) * p["cache_miss"]
    return {
        "actual_input_cost": actual,
        "hypothetical_all_miss_cost": hypothetical,
        "savings_from_cache": hypothetical - actual,
        "savings_percentage": (
            (hypothetical - actual) / hypothetical * 100
        ) if hypothetical > 0 else 0.0,
    }


def recommend_optimizations(
    hit_rate: float,
    message_count: int,
    estimated_context_tokens: int,
    thinking_enabled: bool = True,
    model: str = "deepseek-v4-flash",
) -> list[str]:
    """
    Return optimization recommendations based on current metrics.

    thinking_enabled: set to False if thinking mode is already disabled
    to avoid redundant suggestions.
    """
    recs = []

    if hit_rate < 0.3:
        recs.append(
            "Low cache hit rate (<30%): Ensure system prompt and initial "
            "messages are IDENTICAL across turns. Any prefix change "
            "invalidates the entire cache."
        )
        recs.append(
            "Use CacheFriendlyBuilder to maintain a stable message prefix "
            "and call warm_cache() to establish cache persistence."
        )

    if hit_rate < 0.1 and estimated_context_tokens > 5000:
        recs.append(
            "Cache is almost never hitting (<10%). Check if system prompts "
            "differ between requests, or if dynamic content (timestamps, "
            "file paths) is embedded in the stable prefix region."
        )

    if message_count > 12:
        recs.append(
            f"Long conversation ({message_count} messages): Use "
            "summarize_conversation() to compress history into a compact "
            "summary and start a fresh context window."
        )

    if estimated_context_tokens > 16000:
        recs.append(
            f"High context ({estimated_context_tokens:,} tokens): Split "
            "into separate requests or summarize earlier turns to stay "
            "within efficient cache ranges."
        )

    if thinking_enabled:
        recs.append(
            "Thinking mode is enabled. For simple tasks (translation, "
            "classification, boilerplate code), disable it with "
            "extra_body={'thinking': {'type': 'disabled'}} to save "
            "reasoning tokens."
        )

    return recs