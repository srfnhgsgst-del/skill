PRICING = {
    "deepseek-v4-flash": {
        "cache_hit": 0.0028,
        "cache_miss": 0.14,
        "output": 0.28,
    },
    "deepseek-v4-pro": {
        "cache_hit": 0.003625,
        "cache_miss": 0.435,
        "output": 0.87,
    },
}

MODEL_ALIASES = {
    "deepseek-chat": "deepseek-v4-flash",
    "deepseek-reasoner": "deepseek-v4-flash",
    "deepseek-v4": "deepseek-v4-pro",
    "v4-flash": "deepseek-v4-flash",
    "v4-pro": "deepseek-v4-pro",
}

DEFAULT_MODEL = "deepseek-v4-flash"

CONCURRENCY_LIMITS = {
    "deepseek-v4-flash": 2500,
    "deepseek-v4-pro": 500,
}

CONTEXT_LIMITS = {
    "deepseek-v4-flash": 1_000_000,
    "deepseek-v4-pro": 1_000_000,
}

OUTPUT_LIMITS = {
    "deepseek-v4-flash": 384_000,
    "deepseek-v4-pro": 384_000,
}


def get_pricing(model: str = DEFAULT_MODEL) -> dict:
    resolved = MODEL_ALIASES.get(model, model)
    return PRICING.get(resolved, PRICING[DEFAULT_MODEL])


def resolve_model(model: str = DEFAULT_MODEL) -> str:
    return MODEL_ALIASES.get(model, model)


def input_cost_per_token(model: str = DEFAULT_MODEL, cache_hit: bool = False) -> float:
    p = get_pricing(model)
    key = "cache_hit" if cache_hit else "cache_miss"
    return p[key] / 1_000_000


def output_cost_per_token(model: str = DEFAULT_MODEL) -> float:
    return get_pricing(model)["output"] / 1_000_000


def estimate_api_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_miss_ratio: float = 1.0,
) -> dict:
    p = get_pricing(model)
    miss = input_tokens * cache_miss_ratio
    hit = input_tokens * (1 - cache_miss_ratio)
    cost = (miss / 1_000_000) * p["cache_miss"]
    cost += (hit / 1_000_000) * p["cache_hit"]
    cost += (output_tokens / 1_000_000) * p["output"]
    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_miss_ratio": cache_miss_ratio,
        "estimated_cost_usd": round(cost, 8),
    }


def get_rate_limit_warning(
    model: str,
    requests_5min: int,
    concurrency: int,
) -> str | None:
    limit = CONCURRENCY_LIMITS.get(resolve_model(model), 500)
    if concurrency > limit * 0.8:
        return (
            f"WARNING: Concurrency ({concurrency}) exceeds 80% of "
            f"the {limit} limit for {resolve_model(model)}"
        )
    if requests_5min > limit * 5:
        return (
            f"WARNING: {requests_5min} requests in 5min approaching "
            f"rate limit"
        )
    return None