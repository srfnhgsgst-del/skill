from .pricing import get_pricing


def check_cache_hit(response_usage: dict) -> tuple[int, int, float]:
    hit = response_usage.get("prompt_cache_hit_tokens", 0)
    miss = response_usage.get("prompt_cache_miss_tokens", 0)
    total = hit + miss
    rate = hit / total if total > 0 else 0.0
    return hit, miss, rate


def compute_cache_savings(cache_hit_tokens: int, cache_miss_tokens: int, model: str = "deepseek-v4-flash") -> dict:
    p = get_pricing(model)
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


def recommend_optimizations(hit_rate: float, message_count: int, estimated_context_tokens: int, thinking_enabled: bool = True, model: str = "deepseek-v4-flash") -> list[str]:
    recs = []
    if hit_rate < 0.3:
        recs.append("Low cache hit rate (<30%): Ensure system prompt is IDENTICAL across turns. Use CacheFriendlyBuilder.")
    if hit_rate < 0.1 and estimated_context_tokens > 5000:
        recs.append("Cache almost never hitting (<10%): Check if dynamic content is in the stable prefix region.")
    if message_count > 12:
        recs.append(f"Long conversation ({message_count} msgs): Use summarize_conversation() to compress history.")
    if estimated_context_tokens > 16000:
        recs.append(f"High context ({estimated_context_tokens:,} tokens): Summarize or split requests.")
    if thinking_enabled:
        recs.append("Thinking mode enabled. For simple tasks, disable with extra_body={'thinking': {'type': 'disabled'}}.")
    return recs