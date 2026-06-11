PRICING = {
    "deepseek-v4-flash": {"cache_hit": 0.0028, "cache_miss": 0.14, "output": 0.28},
    "deepseek-v4-pro": {"cache_hit": 0.003625, "cache_miss": 0.435, "output": 0.87},
}


def check_cache_hit(response_usage: dict) -> tuple[int, int, float]:
    """
    Parse a DeepSeek API response usage block and return
    (cache_hit_tokens, cache_miss_tokens, hit_rate).

    response_usage: the `usage` dict from a DeepSeek chat completion response
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

    Returns a dict with actual_cost, potential_cost_if_all_miss, and savings.
    """
    p = PRICING.get(model, PRICING["deepseek-v4-flash"])
    hit_cost = (cache_hit_tokens / 1_000_000) * p["cache_hit"]
    miss_cost = (cache_miss_tokens / 1_000_000) * p["cache_miss"]
    actual = hit_cost + miss_cost
    hypothetical = ((cache_hit_tokens + cache_miss_tokens) / 1_000_000) * p["cache_miss"]
    return {
        "actual_input_cost": actual,
        "hypothetical_all_miss_cost": hypothetical,
        "savings_from_cache": hypothetical - actual,
        "savings_percentage": ((hypothetical - actual) / hypothetical * 100) if hypothetical > 0 else 0.0,
    }


def recommend_optimizations(
    hit_rate: float,
    message_count: int,
    estimated_context_tokens: int,
) -> list[str]:
    """
    Return a list of optimization recommendations based on current metrics.
    """
    recs = []

    if hit_rate < 0.3:
        recs.append(
            "Low cache hit rate (<30%): Ensure system prompt and initial messages are "
            "IDENTICAL across turns. Any change to the prefix invalidates the entire cache."
        )
        recs.append(
            "Consider using CacheFriendlyBuilder to maintain a stable message prefix."
        )

    if message_count > 10:
        recs.append(
            f"Long conversation ({message_count} messages): Use summarize_conversation() "
            "to compress history and start a fresh context window."
        )

    if estimated_context_tokens > 16000:
        recs.append(
            f"High context token count ({estimated_context_tokens:,}): Summarize earlier "
            "turns or split into separate requests to stay within efficient cache ranges."
        )

    if hit_rate < 0.1 and estimated_context_tokens > 5000:
        recs.append(
            "Cache is almost never hitting. Review whether system prompts differ between "
            "requests, or consider disabling caching-dependent optimizations."
        )

    recs.append(
        "Disable thinking mode for simple tasks: use extra_body={'thinking': {'type': 'disabled'}}"
    )

    return recs