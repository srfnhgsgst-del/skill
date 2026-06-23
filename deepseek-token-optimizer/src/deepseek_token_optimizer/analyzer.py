"""
Batch analysis of multiple tracked sessions for long-running services.
"""

import json
from dataclasses import dataclass
from typing import Optional

from .pricing import get_pricing, resolve_model


@dataclass
class SessionSummary:
    session_id: str
    model: str
    requests: int
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    cache_hit_tokens: int
    cache_miss_tokens: int
    reasoning_tokens: int
    total_cost: float
    cache_hit_rate: float


def analyze_session(filepath: str, tag: str = "") -> SessionSummary:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = data.get("records", [])
    if tag:
        records = [r for r in records if isinstance(r, dict) and r.get("tag", "") == tag]

    if not records:
        return SessionSummary(
            session_id=filepath, model="unknown", requests=0,
            total_tokens=0, prompt_tokens=0, completion_tokens=0,
            cache_hit_tokens=0, cache_miss_tokens=0, reasoning_tokens=0,
            total_cost=0.0, cache_hit_rate=0.0,
        )

    model = resolve_model(records[0].get("model", "deepseek-v4-flash")) if isinstance(records[0], dict) else "unknown"
    p = get_pricing(model)

    total = {"prompt": 0, "completion": 0, "cache_hit": 0, "cache_miss": 0, "reasoning": 0}
    for r in records:
        if isinstance(r, dict):
            total["prompt"] += r.get("prompt_tokens", 0)
            total["completion"] += r.get("completion_tokens", 0)
            total["cache_hit"] += r.get("cache_hit_tokens", 0)
            total["cache_miss"] += r.get("cache_miss_tokens", 0)
            total["reasoning"] += r.get("reasoning_tokens", 0)

    cache_total = total["cache_hit"] + total["cache_miss"]
    cost = (total["cache_hit"] / 1_000_000) * p["cache_hit"]
    cost += (total["cache_miss"] / 1_000_000) * p["cache_miss"]
    cost += (total["completion"] / 1_000_000) * p["output"]

    return SessionSummary(
        session_id=filepath,
        model=model,
        requests=len(records),
        total_tokens=total["prompt"] + total["completion"],
        prompt_tokens=total["prompt"],
        completion_tokens=total["completion"],
        cache_hit_tokens=total["cache_hit"],
        cache_miss_tokens=total["cache_miss"],
        reasoning_tokens=total["reasoning"],
        total_cost=round(cost, 6),
        cache_hit_rate=total["cache_hit"] / cache_total if cache_total > 0 else 0.0,
    )


def compare_sessions(filepaths: list[str]) -> list[SessionSummary]:
    return [analyze_session(fp) for fp in filepaths]


def print_session_comparison(summaries: list[SessionSummary]):
    print("=" * 80)
    print(f"  {'Session':<40} {'Requests':>8} {'Tokens':>10} {'Cost':>10} {'Cache%':>7}")
    print("=" * 80)
    for s in summaries:
        name = s.session_id.split("\\")[-1].split("/")[-1][:38]
        print(
            f"  {name:<40} {s.requests:>8} {s.total_tokens:>10,} "
            f"${s.total_cost:>7.4f} {s.cache_hit_rate:>6.1%}"
        )
    print("=" * 80)


def tag_summary(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f: data = json.load(f)
    records = data.get("records", [])
    tags: dict[str, dict] = {}
    for r in records:
        if not isinstance(r, dict): continue
        t = r.get("tag", "")
        if not t: continue
        if t not in tags: tags[t] = {"requests": 0, "total_tokens": 0, "total_cost": 0.0}
        model = resolve_model(r.get("model", "deepseek-v4-flash"))
        p = get_pricing(model)
        tags[t]["requests"] += 1
        tags[t]["total_tokens"] += r.get("prompt_tokens", 0) + r.get("completion_tokens", 0)
        tags[t]["total_cost"] += (r.get("cache_hit_tokens", 0) / 1_000_000) * p["cache_hit"]
        tags[t]["total_cost"] += (r.get("cache_miss_tokens", 0) / 1_000_000) * p["cache_miss"]
        tags[t]["total_cost"] += (r.get("completion_tokens", 0) / 1_000_000) * p["output"]
    return tags


def print_tag_summary(filepath: str):
    tags = tag_summary(filepath)
    print("=" * 50); print("  Cost by Tag"); print("=" * 50)
    print(f"  {'Tag':<20} {'Requests':>8} {'Tokens':>10} {'Cost':>10}")
    print("-" * 50)
    for t, s in sorted(tags.items()):
        print(f"  {t:<20} {s['requests']:>8} {s['total_tokens']:>10,} ${s['total_cost']:>7.4f}")
    print("=" * 50)