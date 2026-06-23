import pytest
import json
import tempfile
import os

from deepseek_token_optimizer import (
    TokenTracker,
    MessageOptimizer,
    CacheFriendlyBuilder,
    check_cache_hit,
    compute_cache_savings,
    compress_system_prompt,
    get_optimal_thinking_config,
    recommend_optimizations,
)
from deepseek_token_optimizer.tracker import TokenUsage


class TestTokenTracker:
    def test_track_single_request(self):
        tracker = TokenTracker()
        tracker.track_request(
            prompt_tokens=1000,
            completion_tokens=500,
            cache_hit=800,
            cache_miss=200,
            reasoning_tokens=100,
        )
        assert len(tracker.records) == 1
        assert tracker.records[0].prompt_tokens == 1000
        assert tracker.records[0].cache_hit_rate == 0.8

    def test_total_cost(self):
        tracker = TokenTracker(model="deepseek-v4-flash")
        tracker.track_request(
            prompt_tokens=1_000_000,
            completion_tokens=1000,
            cache_hit=500_000,
            cache_miss=500_000,
        )
        cost = tracker.total_cost()
        assert cost > 0

    def test_cache_hit_rate_zero_when_no_cache_data(self):
        tracker = TokenTracker()
        tracker.track_request(prompt_tokens=1000, completion_tokens=500)
        assert tracker.overall_cache_hit_rate() == 0.0

    def test_export_json(self):
        tracker = TokenTracker()
        tracker.track_request(prompt_tokens=1000, completion_tokens=500)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name
        try:
            tracker.export(filepath)
            with open(filepath, "r") as f:
                data = json.load(f)
            assert "records" in data
            assert "summary" in data
            assert "cost" in data
        finally:
            os.unlink(filepath)

    def test_potential_savings_report(self):
        tracker = TokenTracker()
        tracker.track_request(
            prompt_tokens=1_000_000,
            completion_tokens=1000,
            cache_hit=0,
            cache_miss=1_000_000,
            reasoning_tokens=500,
        )
        report = tracker.potential_savings_report()
        assert report["cache_savings_potential"] > 0
        assert report["reasoning_cost_incurred"] > 0

    def test_parse_and_track_from_usage_dict(self):
        tracker = TokenTracker()
        usage = {
            "prompt_tokens": 2000,
            "completion_tokens": 800,
            "total_tokens": 2800,
            "prompt_cache_hit_tokens": 1500,
            "prompt_cache_miss_tokens": 500,
            "completion_tokens_details": {"reasoning_tokens": 300},
        }
        tracker.parse_and_track(usage)
        assert len(tracker.records) == 1
        r = tracker.records[0]
        assert r.cache_hit_tokens == 1500
        assert r.reasoning_tokens == 300


class TestMessageOptimizer:
    def test_disable_thinking(self):
        params = {"model": "x", "messages": [], "reasoning_effort": "high"}
        result = MessageOptimizer.disable_thinking(params)
        assert result["extra_body"] == {"thinking": {"type": "disabled"}}
        assert "reasoning_effort" not in result

    def test_set_thinking_effort(self):
        params = {"model": "x", "messages": []}
        result = MessageOptimizer.set_thinking_effort(params, "max")
        assert result["reasoning_effort"] == "max"
        assert result["extra_body"] == {"thinking": {"type": "enabled"}}

    def test_strip_reasoning_no_tool_calls(self):
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi", "reasoning_content": "long reasoning..."},
            {"role": "user", "content": "how are you"},
        ]
        stripped = MessageOptimizer.strip_reasoning_smart(messages)
        assert "reasoning_content" not in stripped[1]
        assert stripped[1]["content"] == "hi"

    def test_strip_reasoning_with_tool_calls(self):
        messages = [
            {"role": "user", "content": "get weather"},
            {
                "role": "assistant",
                "content": None,
                "reasoning_content": "I need to call the tool",
                "tool_calls": [{"id": "1", "function": {"name": "get_weather"}}],
            },
            {"role": "tool", "tool_call_id": "1", "content": "sunny"},
        ]
        stripped = MessageOptimizer.strip_reasoning_smart(messages)
        assert len(stripped) == 3

    def test_estimate_tokens_english(self):
        tokens = MessageOptimizer.estimate_tokens("Hello world")
        assert tokens >= 1

    def test_estimate_tokens_chinese(self):
        tokens = MessageOptimizer.estimate_tokens("你好世界")
        assert tokens >= 2

    def test_estimate_message_tokens(self):
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!", "reasoning_content": "thinking..."},
        ]
        tokens = MessageOptimizer.estimate_message_tokens(messages)
        assert tokens > 5

    def test_should_summarize(self):
        long_msg = [{"role": "user", "content": "x" * 100000}]
        assert MessageOptimizer.should_summarize(long_msg, threshold_tokens=500).should_summarize
        short_msg = [{"role": "user", "content": "hi"}]
        assert not MessageOptimizer.should_summarize(short_msg, threshold_tokens=500).should_summarize


class TestCacheFriendlyBuilder:
    def test_build_with_system_and_user(self):
        builder = CacheFriendlyBuilder(system_prompt="You are helpful.")
        messages, _ = builder.build("Hello")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_build_with_history(self):
        builder = CacheFriendlyBuilder(system_prompt="System")
        history = [
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
        ]
        messages, _ = builder.build("q2", history=history)
        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "q2"

    def test_build_without_system_prompt(self):
        builder = CacheFriendlyBuilder()
        messages, _ = builder.build("Hello")
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_build_multi_turn(self):
        builder = CacheFriendlyBuilder(system_prompt="System")
        messages, params = builder.build_multi_turn(["q1", "q2"])
        assert len(messages) == 3
        assert messages[0]["role"] == "system"


class TestCacheUtils:
    def test_check_cache_hit(self):
        usage = {
            "prompt_cache_hit_tokens": 800,
            "prompt_cache_miss_tokens": 200,
        }
        hit, miss, rate = check_cache_hit(usage)
        assert hit == 800
        assert miss == 200
        assert rate == 0.8

    def test_check_cache_hit_zero(self):
        usage = {}
        hit, miss, rate = check_cache_hit(usage)
        assert hit == 0
        assert miss == 0
        assert rate == 0.0

    def test_compute_cache_savings(self):
        savings = compute_cache_savings(800, 200)
        assert savings["savings_from_cache"] > 0
        assert savings["savings_percentage"] > 0

    def test_compute_cache_savings_no_hit(self):
        savings = compute_cache_savings(0, 1000)
        assert savings["savings_from_cache"] == 0.0
        assert savings["savings_percentage"] == 0.0


class TestRecommendations:
    def test_low_hit_rate(self):
        recs = recommend_optimizations(hit_rate=0.1, message_count=5, estimated_context_tokens=4000)
        assert any("Low cache hit" in r for r in recs)

    def test_long_conversation(self):
        recs = recommend_optimizations(hit_rate=0.8, message_count=15, estimated_context_tokens=4000)
        assert any("Long conversation" in r for r in recs)

    def test_high_context(self):
        recs = recommend_optimizations(hit_rate=0.5, message_count=5, estimated_context_tokens=20000)
        assert any("High context" in r for r in recs)


class TestCompressSystemPrompt:
    def test_no_compression_needed(self):
        short = "You are a helpful assistant."
        result = compress_system_prompt(short, target_tokens=100)
        assert result == short

    def test_compresses_long_prompt(self):
        long_prompt = "Line1\nLine2\nNote: Important thing\nLine3\nLine4\nLine5\nLine6\nLine7\n" * 20
        result = compress_system_prompt(long_prompt, target_tokens=50)
        assert len(result) < len(long_prompt)


class TestGetOptimalThinkingConfig:
    def test_simple_task_disables(self):
        config = get_optimal_thinking_config("simple", "chat", "flash")
        assert config["extra_body"]["thinking"]["type"] == "disabled"

    def test_complex_task_high_effort(self):
        config = get_optimal_thinking_config("complex", "analysis", "pro")
        assert config["reasoning_effort"] == "high"
        assert config["extra_body"]["thinking"]["type"] == "enabled"

    def test_agent_task_high_effort(self):
        config = get_optimal_thinking_config("agent", "agent", "flash")
        assert config["reasoning_effort"] in ("high", "max")