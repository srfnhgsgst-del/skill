"""
Transparent middleware that wraps any OpenAI-compatible client to
automatically track token usage and provide optimization recommendations.

Usage:
    from openai import OpenAI
    from deepseek_token_optimizer import DeepSeekMiddleware

    client = OpenAI(api_key="...", base_url="https://api.deepseek.com")
    wrapped = DeepSeekMiddleware(client)

    response = wrapped.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": "Hello"}],
    )
    # Token usage is automatically tracked

    wrapped.tracker.print_summary()
    wrapped.print_recommendations()
"""

import logging
from typing import Optional

from .tracker import TokenTracker
from .cache_utils import check_cache_hit, recommend_optimizations
from .optimizer import MessageOptimizer

logger = logging.getLogger(__name__)


class DeepSeekMiddleware:
    """
    Transparent wrapper around an OpenAI-compatible client that tracks
    token usage, cache statistics, and provides optimization recommendations.

    Usage:
        wrapped = DeepSeekMiddleware(client)
        wrapped.chat.completions.create(...)  # same API, auto-tracked
        wrapped.print_summary()
    """

    def __init__(
        self,
        client,
        model: str = "deepseek-v4-flash",
        auto_summarize: bool = False,
        summarize_threshold: int = 16000,
    ):
        self._client = client
        self.tracker = TokenTracker(model=model)
        self._auto_summarize = auto_summarize
        self._summarize_threshold = summarize_threshold
        self._thinking_enabled = True

        self.chat = self._ChatProxy(self)

    class _CompletionsProxy:
        def __init__(self, middleware: "DeepSeekMiddleware"):
            self._mw = middleware

        def create(self, **kwargs):
            return self._mw._handle_request(**kwargs)

    class _ChatProxy:
        def __init__(self, middleware: "DeepSeekMiddleware"):
            self._mw = middleware
            self.completions = middleware._CompletionsProxy(middleware)

    def _handle_request(self, **kwargs):
        thinking_enabled = MessageOptimizer.is_thinking_enabled(kwargs)
        self._thinking_enabled = thinking_enabled

        response = self._client.chat.completions.create(**kwargs)

        try:
            usage = response.usage
            if usage:
                model = kwargs.get("model", self.tracker.model)
                self.tracker.parse_and_track(
                    {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens,
                        "prompt_cache_hit_tokens": getattr(usage, "prompt_cache_hit_tokens", 0),
                        "prompt_cache_miss_tokens": getattr(usage, "prompt_cache_miss_tokens", 0),
                        "completion_tokens_details": getattr(usage, "completion_tokens_details", {})
                        or {},
                    },
                    model=model,
                )
        except Exception as e:
            logger.debug("Failed to track usage from response: %s", e)

        messages = kwargs.get("messages", [])
        budget = MessageOptimizer.should_summarize(
            messages, threshold_tokens=self._summarize_threshold
        )
        if budget.should_summarize and self._auto_summarize:
            logger.info(
                "Context approaching limit (%d tokens, %d messages): "
                "consider summarizing",
                budget.estimated_tokens,
                budget.message_count,
            )

        return response

    def print_summary(self):
        self.tracker.print_summary()

    def print_recommendations(self):
        totals = self.tracker.total_tokens()
        hit_rate = self.tracker.overall_cache_hit_rate()
        messages = len(self.tracker.records)
        tokens = totals["total_tokens"]

        recs = recommend_optimizations(
            hit_rate=hit_rate,
            message_count=messages,
            estimated_context_tokens=tokens,
            thinking_enabled=self._thinking_enabled,
        )

        print("=" * 60)
        print("  Optimization Recommendations")
        print("=" * 60)
        for i, rec in enumerate(recs, 1):
            print(f"  {i}. {rec}")
        print("=" * 60)

    def export(self, filepath: str):
        self.tracker.export(filepath)

    def reset(self):
        self.tracker.reset()