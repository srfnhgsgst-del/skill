"""
Transparent sync/async middleware wrapping OpenAI-compatible clients
to auto-track token usage and provide optimization recommendations.
"""

import logging
from typing import Optional

from .tracker import TokenTracker
from .cache_utils import recommend_optimizations
from .optimizer import MessageOptimizer
from .pricing import get_rate_limit_warning

logger = logging.getLogger(__name__)


class DeepSeekMiddleware:
    """Transparent sync wrapper around an OpenAI-compatible client."""

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
        self._thinking_enabled = MessageOptimizer.is_thinking_enabled(kwargs)
        response = self._client.chat.completions.create(**kwargs)

        stream = kwargs.get("stream", False)
        if stream:
            return self._handle_stream(response, kwargs)
        return self._track_and_return(response, kwargs)

    def _handle_stream(self, stream_response, kwargs):
        chunks = []
        for chunk in stream_response:
            chunks.append(chunk)
            yield chunk
        last = chunks[-1] if chunks else None
        if last and last.usage:
            self.tracker.track_stream(
                prompt_tokens=last.usage.prompt_tokens,
                stream_chunks=chunks,
                model=kwargs.get("model", self.tracker.model),
            )

    def _track_and_return(self, response, kwargs):
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
                        "completion_tokens_details": getattr(usage, "completion_tokens_details", {}) or {},
                    },
                    model=model,
                )
        except Exception as e:
            logger.debug("Failed to track usage: %s", e)

        self._check_auto_summarize(kwargs)
        self._check_rate_limit()
        return response

    def _check_auto_summarize(self, kwargs):
        messages = kwargs.get("messages", [])
        budget = MessageOptimizer.should_summarize(messages, threshold_tokens=self._summarize_threshold)
        if budget.should_summarize and self._auto_summarize:
            logger.info(
                "Context approaching limit (%d tokens, %d messages)",
                budget.estimated_tokens, budget.message_count,
            )

    def _check_rate_limit(self):
        warn = get_rate_limit_warning(
            self.tracker.model,
            requests_5min=len(self.tracker.records),
            concurrency=0,
        )
        if warn:
            logger.warning(warn)

    def print_summary(self):
        self.tracker.print_summary()

    def print_recommendations(self):
        totals = self.tracker.total_tokens()
        recs = recommend_optimizations(
            hit_rate=self.tracker.overall_cache_hit_rate(),
            message_count=len(self.tracker.records),
            estimated_context_tokens=totals["total_tokens"],
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


class AsyncDeepSeekMiddleware:
    """Transparent async wrapper around an AsyncOpenAI-compatible client."""

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
        self.chat = self._AsyncChatProxy(self)

    class _AsyncCompletionsProxy:
        def __init__(self, middleware: "AsyncDeepSeekMiddleware"):
            self._mw = middleware

        async def create(self, **kwargs):
            return await self._mw._async_handle_request(**kwargs)

    class _AsyncChatProxy:
        def __init__(self, middleware: "AsyncDeepSeekMiddleware"):
            self._mw = middleware
            self.completions = middleware._AsyncCompletionsProxy(middleware)

    async def _async_handle_request(self, **kwargs):
        self._thinking_enabled = MessageOptimizer.is_thinking_enabled(kwargs)
        stream = kwargs.get("stream", False)

        if stream:
            return self._async_stream(self._client.chat.completions.create(**kwargs), kwargs)

        response = await self._client.chat.completions.create(**kwargs)
        return self._track_and_return(response, kwargs)

    async def _async_stream(self, stream_response, kwargs):
        chunks = []
        async for chunk in await stream_response:
            chunks.append(chunk)
            yield chunk
        last = chunks[-1] if chunks else None
        if last and last.usage:
            self.tracker.track_stream(
                prompt_tokens=last.usage.prompt_tokens,
                stream_chunks=chunks,
                model=kwargs.get("model", self.tracker.model),
            )

    def _track_and_return(self, response, kwargs):
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
                        "completion_tokens_details": getattr(usage, "completion_tokens_details", {}) or {},
                    },
                    model=model,
                )
        except Exception as e:
            logger.debug("Failed to track usage: %s", e)

        messages = kwargs.get("messages", [])
        budget = MessageOptimizer.should_summarize(messages, threshold_tokens=self._summarize_threshold)
        if budget.should_summarize and self._auto_summarize:
            logger.info(
                "Context approaching limit (%d tokens, %d messages)",
                budget.estimated_tokens, budget.message_count,
            )
        return response

    def print_summary(self):
        self.tracker.print_summary()

    def print_recommendations(self):
        totals = self.tracker.total_tokens()
        recs = recommend_optimizations(
            hit_rate=self.tracker.overall_cache_hit_rate(),
            message_count=len(self.tracker.records),
            estimated_context_tokens=totals["total_tokens"],
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