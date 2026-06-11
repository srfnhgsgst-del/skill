import time
import json
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cache_hit_tokens: int = 0
    cache_miss_tokens: int = 0
    reasoning_tokens: int = 0
    model: str = "deepseek-v4-flash"
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


class TokenTracker:
    def __init__(self, model: str = "deepseek-v4-flash"):
        self.model = model
        self.records: list[TokenUsage] = []
        self._pricing = PRICING.get(model, PRICING["deepseek-v4-flash"])

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
                model=self.model,
            )
        )

    def parse_and_track(self, api_response_usage: dict):
        self.track_request(
            prompt_tokens=api_response_usage.get("prompt_tokens", 0),
            completion_tokens=api_response_usage.get("completion_tokens", 0),
            total_tokens=api_response_usage.get("total_tokens", 0),
            cache_hit=api_response_usage.get("prompt_cache_hit_tokens", 0),
            cache_miss=api_response_usage.get("prompt_cache_miss_tokens", 0),
            reasoning_tokens=api_response_usage.get("completion_tokens_details", {}).get(
                "reasoning_tokens", 0
            ),
        )

    def total_cost(self) -> float:
        cost = 0.0
        for r in self.records:
            cost += (r.cache_hit_tokens / 1_000_000) * self._pricing["cache_hit"]
            cost += (r.cache_miss_tokens / 1_000_000) * self._pricing["cache_miss"]
            cost += (r.completion_tokens / 1_000_000) * self._pricing["output"]
        return cost

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
        cash_miss_cost = (missed / 1_000_000) * self._pricing["cache_miss"]
        cash_hit_cost = (missed / 1_000_000) * self._pricing["cache_hit"]
        reasoning_cost = (totals["reasoning_tokens"] / 1_000_000) * self._pricing["output"]
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
                    "cache_hit_rate": self.overall_cache_hit_rate(),
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

    def print_summary(self):
        totals = self.total_tokens()
        cost = self.total_cost()
        cache_rate = self.overall_cache_hit_rate() * 100
        savings = self.potential_savings_report()

        print("=" * 60)
        print(f"  DeepSeek Token Usage Summary ({self.model})")
        print("=" * 60)
        print(f"  Requests:            {len(self.records)}")
        print(f"  Total tokens:        {totals['total_tokens']:,}")
        print(f"  Prompt tokens:       {totals['prompt_tokens']:,}")
        print(f"  Completion tokens:   {totals['completion_tokens']:,}")
        print(f"  Reasoning tokens:    {totals['reasoning_tokens']:,}")
        print(f"  Cache hit tokens:    {totals['cache_hit_tokens']:,}")
        print(f"  Cache miss tokens:   {totals['cache_miss_tokens']:,}")
        print(f"  Cache hit rate:      {cache_rate:.1f}%")
        print(f"  Total cost:          ${cost:.6f}")
        print(f"  Potential savings:   ${savings['total_potential_savings']:.6f}")
        print("=" * 60)