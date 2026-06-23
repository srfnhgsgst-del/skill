import time
import json
from dataclasses import dataclass, field, asdict
from typing import Optional

from .pricing import get_pricing, resolve_model, DEFAULT_MODEL, estimate_api_cost


@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cache_hit_tokens: int = 0
    cache_miss_tokens: int = 0
    reasoning_tokens: int = 0
    model: str = DEFAULT_MODEL
    timestamp: float = field(default_factory=time.time)

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hit_tokens + self.cache_miss_tokens
        if total == 0:
            return 0.0
        return self.cache_hit_tokens / total

    @property
    def reasoning_ratio(self) -> float:
        if self.completion_tokens == 0:
            return 0.0
        return self.reasoning_tokens / self.completion_tokens


class TokenTracker:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = resolve_model(model)
        self.records: list[TokenUsage] = []

    def track(self, usage: TokenUsage):
        self.records.append(usage)

    def track_request(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        cache_hit: int = 0,
        cache_miss: int = 0,
        reasoning_tokens: int = 0,
        total_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ):
        if total_tokens is None:
            total_tokens = prompt_tokens + completion_tokens
        self.records.append(
            TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cache_hit_tokens=cache_hit,
                cache_miss_tokens=cache_miss,
                reasoning_tokens=reasoning_tokens,
                model=resolve_model(model) if model else self.model,
            )
        )

    def track_stream(
        self,
        prompt_tokens: int,
        stream_chunks: list,
        model: Optional[str] = None,
    ):
        completion_tokens = 0
        reasoning_tokens = 0
        for chunk in stream_chunks:
            delta = chunk.usage
            if delta:
                completion_tokens += delta.completion_tokens
                details = delta.completion_tokens_details
                if details:
                    reasoning_tokens += getattr(details, "reasoning_tokens", 0) or 0
        self.track_request(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            reasoning_tokens=reasoning_tokens,
            model=model,
        )

    def track_batch(self, usage_list: list[dict]):
        for usage in usage_list:
            self.parse_and_track(usage)

    def parse_and_track(self, api_response_usage: dict, model: Optional[str] = None):
        self.track_request(
            prompt_tokens=api_response_usage.get("prompt_tokens", 0),
            completion_tokens=api_response_usage.get("completion_tokens", 0),
            total_tokens=api_response_usage.get("total_tokens", 0),
            cache_hit=api_response_usage.get("prompt_cache_hit_tokens", 0),
            cache_miss=api_response_usage.get("prompt_cache_miss_tokens", 0),
            reasoning_tokens=api_response_usage.get("completion_tokens_details", {}).get(
                "reasoning_tokens", 0
            ),
            model=model,
        )

    def reset(self):
        self.records.clear()

    @staticmethod
    def estimate_cost(
        messages: list,
        model: str = DEFAULT_MODEL,
        output_tokens_guess: int = 500,
        cache_miss_ratio: float = 1.0,
    ) -> dict:
        from .optimizer import MessageOptimizer
        input_tokens = MessageOptimizer.estimate_message_tokens(messages)
        return estimate_api_cost(model, input_tokens, output_tokens_guess, cache_miss_ratio)

    def total_cost(self) -> float:
        cost = 0.0
        for r in self.records:
            p = get_pricing(r.model)
            cost += (r.cache_hit_tokens / 1_000_000) * p["cache_hit"]
            cost += (r.cache_miss_tokens / 1_000_000) * p["cache_miss"]
            cost += (r.completion_tokens / 1_000_000) * p["output"]
        return cost

    def cost_by_model(self) -> dict[str, float]:
        costs: dict[str, float] = {}
        for r in self.records:
            p = get_pricing(r.model)
            c = (r.cache_hit_tokens / 1_000_000) * p["cache_hit"]
            c += (r.cache_miss_tokens / 1_000_000) * p["cache_miss"]
            c += (r.completion_tokens / 1_000_000) * p["output"]
            costs[r.model] = costs.get(r.model, 0.0) + c
        return costs

    def total_tokens(self) -> dict:
        return {
            "prompt_tokens": sum(r.prompt_tokens for r in self.records),
            "completion_tokens": sum(r.completion_tokens for r in self.records),
            "total_tokens": sum(r.total_tokens for r in self.records),
            "cache_hit_tokens": sum(r.cache_hit_tokens for r in self.records),
            "cache_miss_tokens": sum(r.cache_miss_tokens for r in self.records),
            "reasoning_tokens": sum(r.reasoning_tokens for r in self.records),
        }

    def overall_cache_hit_rate(self) -> float:
        totals = self.total_tokens()
        cache_total = totals["cache_hit_tokens"] + totals["cache_miss_tokens"]
        if cache_total == 0:
            return 0.0
        return totals["cache_hit_tokens"] / cache_total

    def potential_savings_report(self) -> dict:
        totals = self.total_tokens()
        missed = totals["cache_miss_tokens"]
        p = get_pricing(self.model)
        cash_miss_cost = (missed / 1_000_000) * p["cache_miss"]
        cash_hit_cost = (missed / 1_000_000) * p["cache_hit"]
        reasoning_cost = (totals["reasoning_tokens"] / 1_000_000) * p["output"]
        return {
            "cache_savings_potential": cash_miss_cost - cash_hit_cost,
            "reasoning_cost_incurred": reasoning_cost,
            "total_potential_savings": (cash_miss_cost - cash_hit_cost) + reasoning_cost,
            "current_cost": self.total_cost(),
        }

    def export(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "records": [asdict(r) for r in self.records],
                    "summary": self.total_tokens(),
                    "cost": self.total_cost(),
                    "cost_by_model": self.cost_by_model(),
                    "cache_hit_rate": self.overall_cache_hit_rate(),
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

    @staticmethod
    def load_export(filepath: str) -> dict:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def print_summary(self):
        models: dict[str, list[TokenUsage]] = {}
        for r in self.records:
            models.setdefault(r.model, []).append(r)
        if len(models) > 1:
            for m, recs in models.items():
                self._print_block(m, recs)
        else:
            self._print_block(self.model, self.records)

    def _print_block(self, model_name: str, records: list[TokenUsage]):
        t = {
            "prompt_tokens": sum(r.prompt_tokens for r in records),
            "completion_tokens": sum(r.completion_tokens for r in records),
            "total_tokens": sum(r.total_tokens for r in records),
            "cache_hit_tokens": sum(r.cache_hit_tokens for r in records),
            "cache_miss_tokens": sum(r.cache_miss_tokens for r in records),
            "reasoning_tokens": sum(r.reasoning_tokens for r in records),
        }
        p = get_pricing(model_name)
        cost = 0.0
        for r in records:
            cost += (r.cache_hit_tokens / 1_000_000) * p["cache_hit"]
            cost += (r.cache_miss_tokens / 1_000_000) * p["cache_miss"]
            cost += (r.completion_tokens / 1_000_000) * p["output"]
        cache_total = t["cache_hit_tokens"] + t["cache_miss_tokens"]
        cache_rate = (t["cache_hit_tokens"] / cache_total * 100) if cache_total > 0 else 0

        print("=" * 60)
        print(f"  DeepSeek Token Usage Summary ({model_name})")
        print("=" * 60)
        print(f"  Requests:            {len(records)}")
        print(f"  Total tokens:        {t['total_tokens']:,}")
        print(f"  Prompt tokens:       {t['prompt_tokens']:,}")
        print(f"  Completion tokens:   {t['completion_tokens']:,}")
        print(f"  Reasoning tokens:    {t['reasoning_tokens']:,}")
        print(f"  Cache hit tokens:    {t['cache_hit_tokens']:,}")
        print(f"  Cache miss tokens:   {t['cache_miss_tokens']:,}")
        print(f"  Cache hit rate:      {cache_rate:.1f}%")
        print(f"  Total cost:          ${cost:.6f}")
        print("=" * 60)