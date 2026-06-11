# DeepSeek Token Optimizer

Optimize DeepSeek API token consumption by up to **70%** through cache-aware message design, thinking-mode control, conversation summarization, and token budget management.

## Activation

This skill activates when:
- The user is building or debugging integrations with the DeepSeek API
- The user complains about high token consumption or API costs with DeepSeek
- The user asks how to reduce DeepSeek API spending
- The conversation involves multi-turn chat, tool calls, or agent architectures with DeepSeek
- The user asks about context caching, KV cache, or cache hit optimization

## Core Principles

### 1. Thinking Mode — The Hidden Token Eater

DeepSeek's thinking mode defaults to `enabled` with `reasoning_effort="high"` (or `"max"` for agent orchestration). Every chain-of-thought token is a billable output token the user never sees.

| Scenario | Thinking Recommendation |
|---|---|
| Simple Q&A, classification, translation | **Disable** |
| Routine code generation, refactoring | **Disable** or `low` |
| Complex debugging, architecture design | `high` |
| Multi-step agent orchestration | `high` (avoid `max`) |

```python
# Disable thinking for simple tasks
response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=messages,
    extra_body={"thinking": {"type": "disabled"}}
)
```

### 2. Context Caching — The 50x Price Gap

Cache-hit input: $0.0028/M tokens vs cache-miss: $0.14/M tokens.

**Cache rules:**
- Requires EXACT prefix match against a persisted cache unit
- Cache units form at: request boundaries, common-prefix detection, fixed intervals
- If your system prompt or first message changes AT ALL — full cache miss

**Cache-friendly patterns:**
```
Always send the system prompt FIRST, never modify it across turns.
Follow with a stable, consistent initial user message when possible.
Append new content AFTER the stable prefix, never in the middle.
```

### 3. Turn Management

- Non-tool-call turns: drop `reasoning_content` from context (DeepSeek ignores it anyway)
- Tool-call turns: `reasoning_content` MUST be passed back in all subsequent requests
- After ~8 turns, summarize the conversation and start a fresh context window

### 4. System Prompt Minimization

OpenCode-like agents can send 3000+ token system prompts on EVERY request. Audit and trim:
- Remove redundant instructions
- Merge overlapping constraints
- Use structured, terse formatting

## Optimization Strategies (Priority Order)

1. **Disable thinking** for all non-reasoning tasks
2. **Design cache-friendly message structures** — identical prefix every time
3. **Compress system prompts** — strip verbose explanations
4. **Summarize when approaching context limits** — reset after ~8 turns
5. **Consolidate sequential queries** into single multi-part requests
6. **Switch to non-thinking mode for tool-call loops** that don't need reasoning

## Monitoring

Use the `deepseek_token_optimizer.tracker` module to monitor token usage:

```python
from deepseek_token_optimizer import TokenTracker

tracker = TokenTracker()
tracker.track_request(prompt_tokens=5000, completion_tokens=2000, cache_hit=3000, cache_miss=2000)
tracker.print_summary()
```

## References

- [DeepSeek Context Caching Docs](https://api-docs.deepseek.com/guides/kv_cache)
- [DeepSeek Thinking Mode Docs](https://api-docs.deepseek.com/guides/thinking_mode)
- [DeepSeek Pricing](https://api-docs.deepseek.com/quick_start/pricing)