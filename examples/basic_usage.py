"""
Usage examples for deepseek-token-optimizer.

Run: python examples/basic_usage.py
"""

import os
from deepseek_token_optimizer import (
    TokenTracker,
    MessageOptimizer,
    CacheFriendlyBuilder,
    check_cache_hit,
    compute_cache_savings,
    summarize_conversation,
    compress_system_prompt,
    get_optimal_thinking_config,
    recommend_optimizations,
)


def example_tracker():
    print("=== Example: TokenTracker ===\n")
    tracker = TokenTracker(model="deepseek-v4-flash")

    tracker.track_request(
        prompt_tokens=5200,
        completion_tokens=800,
        cache_hit=5000,
        cache_miss=200,
        reasoning_tokens=300,
    )

    tracker.track_request(
        prompt_tokens=5200,
        completion_tokens=900,
        cache_hit=5000,
        cache_miss=200,
        reasoning_tokens=350,
    )

    tracker.track_request(
        prompt_tokens=3000,
        completion_tokens=400,
        cache_hit=0,
        cache_miss=3000,
        reasoning_tokens=0,
    )

    tracker.print_summary()
    print()


def example_thinking_control():
    print("=== Example: Thinking Mode Control ===\n")
    params = {"model": "deepseek-v4-flash", "messages": []}

    optimizer = MessageOptimizer()
    disabled = optimizer.disable_thinking(params.copy())
    print("Disabled thinking:", disabled)

    high_effort = optimizer.set_thinking_effort(params.copy(), "high")
    print("High effort:", high_effort)

    config = get_optimal_thinking_config(
        task_complexity="simple",
        task_type="chat",
        model_variant="flash",
    )
    print("Optimal config for simple chat:", config)
    print()


def example_cache_friendly():
    print("=== Example: CacheFriendlyBuilder ===\n")

    builder = CacheFriendlyBuilder(
        system_prompt="You are a helpful coding assistant. Always respond in Python.",
    )

    messages = builder.build("Write a function to calculate factorial")
    print("Turn 1 messages:", len(messages), "messages")

    messages = builder.build(
        "Write a function to calculate fibonacci",
        history=messages,
    )
    print("Turn 2 messages:", len(messages), "messages")
    print()


def example_cache_check():
    print("=== Example: Cache Hit Check ===\n")

    mock_usage = {
        "prompt_tokens": 5200,
        "completion_tokens": 800,
        "total_tokens": 6000,
        "prompt_cache_hit_tokens": 4800,
        "prompt_cache_miss_tokens": 400,
    }

    hit, miss, rate = check_cache_hit(mock_usage)
    savings = compute_cache_savings(hit, miss)

    print(f"Cache hit tokens: {hit:,}")
    print(f"Cache miss tokens: {miss:,}")
    print(f"Hit rate: {rate:.1%}")
    print(f"Actual input cost: ${savings['actual_input_cost']:.6f}")
    print(f"Savings from cache: ${savings['savings_from_cache']:.6f} ({savings['savings_percentage']:.1f}%)")
    print()


def example_recommendations():
    print("=== Example: Optimization Recommendations ===\n")

    recs = recommend_optimizations(
        hit_rate=0.15,
        message_count=15,
        estimated_context_tokens=20000,
    )
    for i, rec in enumerate(recs, 1):
        print(f"  {i}. {rec}")
    print()


def example_system_prompt_compression():
    print("=== Example: System Prompt Compression ===\n")

    verbose_prompt = """You are an expert Python software engineer with deep knowledge of design patterns,
best practices, and system architecture. Always write clean, well-structured code that follows PEP 8.
Always include type hints. Always write docstrings. Always handle edge cases. Always write tests.
Note: Use f-strings for string formatting.
Note: Use pathlib for file paths.
Important: Never use global variables.
Important: Always use context managers for file I/O.
Remember: Prefer composition over inheritance.
Remember: Keep functions small and focused.
Keep in mind: Use dataclasses for data containers.
Keep in mind: Use enums for constant values."""

    compressed = compress_system_prompt(verbose_prompt, target_tokens=100)

    original_tokens = MessageOptimizer.estimate_tokens(verbose_prompt)
    compressed_tokens = MessageOptimizer.estimate_tokens(compressed)

    print(f"Original: ~{original_tokens} tokens ({len(verbose_prompt)} chars)")
    print(f"Compressed: ~{compressed_tokens} tokens ({len(compressed)} chars)")
    print(f"Reduction: {((original_tokens - compressed_tokens) / original_tokens * 100):.0f}%")
    print()
    print("Compressed prompt:")
    print(compressed)
    print()


def example_estimate_tokens():
    print("=== Example: Token Estimation ===\n")

    text_en = "The quick brown fox jumps over the lazy dog"
    text_cn = "敏捷的棕色狐狸跳过了懒狗"
    text_mixed = "Python是一种programming language"

    print(f'"{text_en}" => ~{MessageOptimizer.estimate_tokens(text_en)} tokens')
    print(f'"{text_cn}" => ~{MessageOptimizer.estimate_tokens(text_cn)} tokens')
    print(f'"{text_mixed}" => ~{MessageOptimizer.estimate_tokens(text_mixed)} tokens')
    print()


if __name__ == "__main__":
    example_tracker()
    example_thinking_control()
    example_cache_friendly()
    example_cache_check()
    example_recommendations()
    example_system_prompt_compression()
    example_estimate_tokens()