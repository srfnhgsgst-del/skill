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


CONCURRENCY_LIMITS = {
    "deepseek-v4-flash": 2500,
    "deepseek-v4-pro": 500,
}