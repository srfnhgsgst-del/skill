"""
Transparent sync/async middleware wrapping OpenAI-compatible clients
with auto-summarize, streaming, and tagged cost tracking.
"""

import logging
from typing import Optional

from .tracker import TokenTracker
from .cache_utils import recommend_optimizations
from .optimizer import MessageOptimizer
from .pricing import get_rate_limit_warning
from .strategies import summarize_conversation, dry_summarize

logger = logging.getLogger(__name__)


class DeepSeekMiddleware:
    def __init__(self, client, model: str = "deepseek-v4-flash",
                 auto_summarize: bool = False, summarize_threshold: int = 16000,
                 tag: str = ""):
        self._client = client
        self.tracker = TokenTracker(model=model)
        self._auto_summarize = auto_summarize
        self._summarize_threshold = summarize_threshold
        self._tag = tag
        self._thinking_enabled = True
        self.chat = self._ChatProxy(self)

    class _CompletionsProxy:
        def __init__(self, middleware: "DeepSeekMiddleware"):
            self._mw = middleware
        def create(self, **kwargs): return self._mw._handle_request(**kwargs)

    class _ChatProxy:
        def __init__(self, middleware: "DeepSeekMiddleware"):
            self._mw = middleware
            self.completions = middleware._CompletionsProxy(middleware)

    def set_tag(self, tag: str): self._tag = tag

    def _handle_request(self, **kwargs):
        self._thinking_enabled = MessageOptimizer.is_thinking_enabled(kwargs)
        tag = kwargs.pop("tag", self._tag)
        stream = kwargs.get("stream", False)
        if stream:
            return self._handle_stream(kwargs, tag)
        return self._track_and_return(kwargs, tag)

    def _handle_stream(self, kwargs, tag):
        chunks = []
        for chunk in self._client.chat.completions.create(**kwargs):
            chunks.append(chunk)
            yield chunk
        last = chunks[-1] if chunks else None
        if last and last.usage:
            self.tracker.track_stream(prompt_tokens=last.usage.prompt_tokens, stream_chunks=chunks, model=kwargs.get("model", self.tracker.model), tag=tag)

    def _track_and_return(self, kwargs, tag):
        response = self._client.chat.completions.create(**kwargs)
        messages = kwargs.get("messages", [])
        try:
            usage = response.usage
            if usage:
                self.tracker.parse_and_track({
                    "prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "prompt_cache_hit_tokens": getattr(usage, "prompt_cache_hit_tokens", 0),
                    "prompt_cache_miss_tokens": getattr(usage, "prompt_cache_miss_tokens", 0),
                    "completion_tokens_details": getattr(usage, "completion_tokens_details", {}) or {},
                }, model=kwargs.get("model", self.tracker.model), tag=tag)
        except Exception as e: logger.debug("Failed to track usage: %s", e)
        self._check_auto_summarize(messages, kwargs.get("model", self.tracker.model))
        self._check_rate_limit()
        return response

    def _check_auto_summarize(self, messages, model):
        if not self._auto_summarize: return
        budget = MessageOptimizer.should_summarize(messages, threshold_tokens=self._summarize_threshold)
        if budget.should_summarize:
            logger.info("Auto-summarizing: %d tokens", budget.estimated_tokens)
            try:
                summarize_conversation(messages, self._client, model=model)
            except Exception as e: logger.warning("Auto-summarize failed: %s", e)

    def _check_rate_limit(self):
        warn = get_rate_limit_warning(self.tracker.model, requests_5min=len(self.tracker.records), concurrency=0)
        if warn: logger.warning(warn)

    def print_summary(self): self.tracker.print_summary()

    def print_recommendations(self):
        totals = self.tracker.total_tokens()
        recs = recommend_optimizations(hit_rate=self.tracker.overall_cache_hit_rate(), message_count=len(self.tracker.records), estimated_context_tokens=totals["total_tokens"], thinking_enabled=self._thinking_enabled)
        print("="*60); print("  Optimization Recommendations"); print("="*60)
        for i, rec in enumerate(recs, 1): print(f"  {i}. {rec}")
        print("="*60)

    def export(self, filepath: str): self.tracker.export(filepath)
    def export_html(self, filepath: str): self.tracker.export_html(filepath)
    def reset(self): self.tracker.reset()


class AsyncDeepSeekMiddleware:
    def __init__(self, client, model: str = "deepseek-v4-flash",
                 auto_summarize: bool = False, summarize_threshold: int = 16000,
                 tag: str = ""):
        self._client = client
        self.tracker = TokenTracker(model=model)
        self._auto_summarize = auto_summarize
        self._summarize_threshold = summarize_threshold
        self._tag = tag
        self._thinking_enabled = True
        self.chat = self._AsyncChatProxy(self)

    class _AsyncCompletionsProxy:
        def __init__(self, middleware: "AsyncDeepSeekMiddleware"):
            self._mw = middleware
        async def create(self, **kwargs): return await self._mw._async_handle_request(**kwargs)

    class _AsyncChatProxy:
        def __init__(self, middleware: "AsyncDeepSeekMiddleware"):
            self._mw = middleware
            self.completions = middleware._AsyncCompletionsProxy(middleware)

    def set_tag(self, tag: str): self._tag = tag

    async def _async_handle_request(self, **kwargs):
        self._thinking_enabled = MessageOptimizer.is_thinking_enabled(kwargs)
        tag = kwargs.pop("tag", self._tag)
        stream = kwargs.get("stream", False)
        if stream:
            return self._async_stream(kwargs, tag)
        response = await self._client.chat.completions.create(**kwargs)
        try:
            usage = response.usage
            if usage:
                self.tracker.parse_and_track({
                    "prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "prompt_cache_hit_tokens": getattr(usage, "prompt_cache_hit_tokens", 0),
                    "prompt_cache_miss_tokens": getattr(usage, "prompt_cache_miss_tokens", 0),
                    "completion_tokens_details": getattr(usage, "completion_tokens_details", {}) or {},
                }, model=kwargs.get("model", self.tracker.model), tag=tag)
        except Exception as e: logger.debug("Failed to track usage: %s", e)
        messages = kwargs.get("messages", [])
        if self._auto_summarize:
            budget = MessageOptimizer.should_summarize(messages, threshold_tokens=self._summarize_threshold)
            if budget.should_summarize:
                logger.info("Auto-summarize triggered: %d tokens", budget.estimated_tokens)
        return response

    async def _async_stream(self, kwargs, tag):
        chunks = []
        async for chunk in await self._client.chat.completions.create(**kwargs):
            chunks.append(chunk); yield chunk
        last = chunks[-1] if chunks else None
        if last and last.usage:
            self.tracker.track_stream(prompt_tokens=last.usage.prompt_tokens, stream_chunks=chunks, model=kwargs.get("model", self.tracker.model), tag=tag)

    def print_summary(self): self.tracker.print_summary()
    def print_recommendations(self):
        totals = self.tracker.total_tokens()
        recs = recommend_optimizations(hit_rate=self.tracker.overall_cache_hit_rate(), message_count=len(self.tracker.records), estimated_context_tokens=totals["total_tokens"], thinking_enabled=self._thinking_enabled)
        print("="*60); print("  Optimization Recommendations"); print("="*60)
        for i, rec in enumerate(recs, 1): print(f"  {i}. {rec}")
        print("="*60)

    def export(self, filepath: str): self.tracker.export(filepath)
    def export_html(self, filepath: str): self.tracker.export_html(filepath)
    def reset(self): self.tracker.reset()