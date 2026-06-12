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
    DeepSeekTokenizer,
    TokenBudget,
    summarize_conversation,
    dry_summarize,
    TokenizerError,
)
from deepseek_token_optimizer.pricing import get_pricing, resolve_model, PRICING


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
            assert "cost_by_model" in data
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

    def test_multi_model_tracking(self):
        tracker = TokenTracker()
        tracker.track_request(
            prompt_tokens=1000, completion_tokens=500, model="deepseek-v4-flash"
        )
        tracker.track_request(
            prompt_tokens=1000, completion_tokens=500, model="deepseek-v4-pro"
        )
        costs = tracker.cost_by_model()
        assert "deepseek-v4-flash" in costs
        assert "deepseek-v4-pro" in costs
        assert costs["deepseek-v4-pro"] > costs["deepseek-v4-flash"]

    def test_reset(self):
        tracker = TokenTracker()
        tracker.track_request(prompt_tokens=1000, completion_tokens=500)
        assert len(tracker.records) == 1
        tracker.reset()
        assert len(tracker.records) == 0

    def test_track_batch(self):
        tracker = TokenTracker()
        tracker.track_batch(
            [
                {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                {"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300},
            ]
        )
        assert len(tracker.records) == 2


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

    def test_is_thinking_enabled(self):
        assert MessageOptimizer.is_thinking_enabled(
            {"extra_body": {"thinking": {"type": "enabled"}}}
        )
        assert not MessageOptimizer.is_thinking_enabled(
            {"extra_body": {"thinking": {"type": "disabled"}}}
        )
        assert MessageOptimizer.is_thinking_enabled({})

    def test_strip_reasoning_smart_no_tool_calls(self):
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi", "reasoning_content": "..."},
            {"role": "user", "content": "how are you"},
        ]
        stripped = MessageOptimizer.strip_reasoning_smart(messages)
        assert "reasoning_content" not in stripped[1]
        assert stripped[1]["content"] == "hi"

    def test_strip_reasoning_smart_with_tool_calls(self):
        messages = [
            {"role": "user", "content": "get weather"},
            {
                "role": "assistant",
                "content": None,
                "reasoning_content": "need to call tool",
                "tool_calls": [{"id": "1", "function": {"name": "get_weather"}}],
            },
            {"role": "tool", "tool_call_id": "1", "content": "sunny"},
        ]
        stripped = MessageOptimizer.strip_reasoning_smart(messages)
        assert "reasoning_content" in stripped[1]
        assert stripped[1]["tool_calls"] is not None

    def test_strip_reasoning_smart_mixed(self):
        conversations = [
            {"role": "user", "content": "q1"},
            {
                "role": "assistant",
                "content": "Let me check",
                "reasoning_content": "thinking...",
                "tool_calls": [{"id": "1", "function": {"name": "search"}}],
            },
            {"role": "tool", "tool_call_id": "1", "content": "result"},
            {
                "role": "assistant",
                "content": "Here is the answer",
                "reasoning_content": "synthesizing...",
            },
            {"role": "user", "content": "q2"},
        ]
        stripped = MessageOptimizer.strip_reasoning_smart(conversations)
        assert "reasoning_content" in stripped[1]
        assert "reasoning_content" not in stripped[3]

    def test_estimate_tokens_english(self):
        tokens = MessageOptimizer.estimate_tokens("Hello world")
        assert tokens >= 1

    def test_estimate_tokens_chinese(self):
        tokens = MessageOptimizer.estimate_tokens("你好世界")
        assert tokens >= 2

    def test_estimate_tokens_japanese(self):
        tokens = MessageOptimizer.estimate_tokens("こんにちは")
        assert tokens >= 2

    def test_estimate_message_tokens(self):
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!", "reasoning_content": "thinking..."},
        ]
        tokens = MessageOptimizer.estimate_message_tokens(messages)
        assert tokens > 5

    def test_should_summarize_returns_tokenbudget(self):
        result = MessageOptimizer.should_summarize(
            [{"role": "user", "content": "hi"}], threshold_tokens=500
        )
        assert isinstance(result, TokenBudget)
        assert not result.should_summarize

    def test_should_summarize_long_context(self):
        long_msg = [{"role": "user", "content": "x" * 100000}]
        result = MessageOptimizer.should_summarize(long_msg, threshold_tokens=500)
        assert result.should_summarize
        assert "token count" in result.reason.lower() or "token" in result.reason.lower()

    def test_should_summarize_by_message_count(self):
        long_turns = [{"role": "user", "content": "hi"} for _ in range(20)]
        result = MessageOptimizer.should_summarize(long_turns, threshold_tokens=100000)
        assert result.should_summarize


class TestCacheFriendlyBuilder:
    def test_build_returns_tuple(self):
        builder = CacheFriendlyBuilder(system_prompt="You are helpful.")
        messages, params = builder.build("Hello")
        assert isinstance(messages, list)
        assert isinstance(params, dict)

    def test_build_with_thinking_params(self):
        builder = CacheFriendlyBuilder(system_prompt="System")
        messages, params = builder.build(
            "Hello",
            thinking_params={"extra_body": {"thinking": {"type": "disabled"}}},
        )
        assert params["extra_body"]["thinking"]["type"] == "disabled"

    def test_estimated_prefix_tokens(self):
        builder = CacheFriendlyBuilder(system_prompt="You are helpful.")
        assert builder.estimated_prefix_tokens > 0

    def test_build_multi_turn_with_effort(self):
        builder = CacheFriendlyBuilder(system_prompt="System")
        messages, params = builder.build_multi_turn(
            ["q1", "q2"], thinking_effort="low"
        )
        assert params["reasoning_effort"] == "low"

    def test_build_multi_turn_auto_detect(self):
        builder = CacheFriendlyBuilder(system_prompt="System")
        messages, params = builder.build_multi_turn(
            ["q1", "q2"], task_complexity="complex", task_type="agent"
        )
        assert "extra_body" in params


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

    def test_recommendations_with_thinking_disabled(self):
        recs = recommend_optimizations(
            hit_rate=0.5, message_count=5, estimated_context_tokens=4000, thinking_enabled=False
        )
        assert not any("Disable thinking" in r or "Thinking mode is enabled" in r for r in recs)

    def test_recommendations_with_thinking_enabled(self):
        recs = recommend_optimizations(
            hit_rate=0.5, message_count=5, estimated_context_tokens=4000, thinking_enabled=True
        )
        assert any("Thinking mode is enabled" in r for r in recs)


class TestCompressSystemPrompt:
    def test_no_compression_needed(self):
        short_prompt = "You are a helpful assistant."
        result = compress_system_prompt(short_prompt, target_tokens=100)
        assert result == short_prompt

    def test_preserves_directives(self):
        long_prompt = (
            "MUST: Always validate input.\n"
            + "Some prose content that should be compressible.\n" * 50
            + "NOTE: Important security rule.\n"
        )
        result = compress_system_prompt(long_prompt, target_tokens=50)
        assert "MUST" in result
        assert "NOTE" in result

    def test_compresses_redundant_lines(self):
        redundant = ("Line to repeat.\n") * 100
        result = compress_system_prompt(redundant, target_tokens=100)
        assert len(result) < len(redundant)

    def test_handles_empty(self):
        result = compress_system_prompt("", target_tokens=100)
        assert result == ""


class TestGetOptimalThinkingConfig:
    def test_simple_chat_disables(self):
        config = get_optimal_thinking_config("simple", "chat", "flash")
        assert config["extra_body"]["thinking"]["type"] == "disabled"

    def test_complex_analysis_high_effort(self):
        config = get_optimal_thinking_config("complex", "analysis", "pro")
        assert config["reasoning_effort"] == "high"

    def test_agent_agent_max_effort(self):
        config = get_optimal_thinking_config("agent", "agent", "pro")
        assert config["reasoning_effort"] == "max"

    def test_medium_code_low_effort(self):
        config = get_optimal_thinking_config("medium", "code", "flash")
        assert config["reasoning_effort"] == "low"

    def test_medium_analysis_high_effort(self):
        config = get_optimal_thinking_config("medium", "analysis", "flash")
        assert config["reasoning_effort"] == "high"


class TestPricing:
    def test_get_pricing_flash(self):
        p = get_pricing("deepseek-v4-flash")
        assert p["cache_hit"] == 0.0028

    def test_get_pricing_pro(self):
        p = get_pricing("deepseek-v4-pro")
        assert p["cache_miss"] == 0.435

    def test_get_pricing_alias(self):
        p = get_pricing("deepseek-chat")
        assert p["cache_hit"] == 0.0028

    def test_resolve_model(self):
        assert resolve_model("deepseek-chat") == "deepseek-v4-flash"

    def test_get_pricing_unknown_fallback(self):
        p = get_pricing("unknown-model")
        assert p["cache_hit"] == PRICING["deepseek-v4-flash"]["cache_hit"]


class TestDeepSeekTokenizer:
    def test_heuristic_count(self):
        t = DeepSeekTokenizer()
        assert t.has_official is False
        count = t.count_tokens("Hello world")
        assert count >= 1

    def test_chinese_text(self):
        t = DeepSeekTokenizer()
        count = t.count_tokens("你好世界")
        assert count >= 2

    def test_mixed_text(self):
        t = DeepSeekTokenizer()
        count = t.count_tokens("Hello 你好 world 世界")
        assert count >= 3

    def test_count_message_tokens(self):
        t = DeepSeekTokenizer()
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
        ]
        count = t.count_message_tokens(messages)
        assert count >= 3

    def test_empty_text(self):
        t = DeepSeekTokenizer()
        assert t.count_tokens("") == 0


class TestDrySummarize:
    def test_short_conversation_no_summary(self):
        messages = [{"role": "user", "content": "hi"} for _ in range(5)]
        budget = dry_summarize(messages)
        assert isinstance(budget, TokenBudget)
        assert not budget.should_summarize

    def test_long_conversation_needs_summary(self):
        messages = [{"role": "user", "content": "hello world this is a test"} for _ in range(30)]
        budget = dry_summarize(messages)
        assert isinstance(budget, TokenBudget)


class TestSummarizeConversation:
    def test_short_conversation_returns_original(self):
        messages = [
            {"role": "user", "content": "h"} for _ in range(5)
        ]
        result = summarize_conversation(messages, client="mock", model="deepseek-v4-flash")
        assert len(result) == len(messages)

    def test_requires_client_raises_on_error(self):
        messages = [
            {"role": "user", "content": "hello world. " * 50} for _ in range(20)
        ]
        with pytest.raises(TokenizerError):
            summarize_conversation(messages, client="not_a_real_client")