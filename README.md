# DeepSeek Token Optimizer

Optimize DeepSeek API token consumption by up to **70%** through cache-aware message design, thinking-mode control, conversation summarization, and token budget management.

## Why Token Costs Spike

| Cause | Impact | Solution |
|---|---|---|
| Thinking mode (enabled by default) | Invisible chain-of-thought tokens billed as output | Disable for simple tasks; control effort level |
| Context cache misses | **50x cost difference** ($0.14 vs $0.0028 per 1M tokens) | Cache-friendly message structure |
| Unbounded conversation growth | Every turn appends to context | Summarize after ~8 turns |
| Verbose system prompts | 3000+ tokens sent on EVERY request | Compress and deduplicate |
| reasoning_content bloat (tool calls) | Must pass back all reasoning in subsequent turns | Strip when no tool call was made |

## Installation

```bash
pip install deepseek-token-optimizer
```

Or from source:

```bash
git clone https://github.com/srfnhgsgst-del/skill.git
cd skill
pip install -e .
```

## Quick Start

### 1. Transparent Middleware (v1.1)

```python
from openai import OpenAI
from deepseek_token_optimizer import DeepSeekMiddleware

client = OpenAI(api_key="...", base_url="https://api.deepseek.com")
wrapped = DeepSeekMiddleware(client, auto_summarize=True)

response = wrapped.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[{"role": "user", "content": "Hello"}],
)
# Token usage auto-tracked — no code changes needed
wrapped.print_summary()
wrapped.print_recommendations()
```

### 2. Multi-Model Token Tracking (v1.1)

```python
from deepseek_token_optimizer import TokenTracker

tracker = TokenTracker()
tracker.parse_and_track(flash_response.usage.__dict__, model="deepseek-v4-flash")
tracker.parse_and_track(pro_response.usage.__dict__, model="deepseek-v4-pro")
tracker.print_summary()               # per-model breakdown
print(tracker.cost_by_model())        # {'deepseek-v4-flash': 0.0003, 'deepseek-v4-pro': 0.0008}
tracker.reset()                       # clear all records
```

### 3. Smart Reasoning Stripping (v1.1)

```python
from deepseek_token_optimizer import MessageOptimizer

# Per-message tool-call detection — safe for mixed conversations
cleaned = MessageOptimizer.strip_reasoning_smart(messages)
```

### 4. Cache-Friendly Message Builder (v1.1)

```python
from deepseek_token_optimizer import CacheFriendlyBuilder

builder = CacheFriendlyBuilder(
    system_prompt="You are a Python coding assistant.",
)
# Returns (messages, api_params) tuple
messages, params = builder.build(
    "sort a list",
    thinking_params={"extra_body": {"thinking": {"type": "disabled"}}}
)
print(builder.estimated_prefix_tokens)  # token count of stable prefix
```

### 5. Token Budget Check (v1.1)

```python
from deepseek_token_optimizer import MessageOptimizer, dry_summarize

budget = MessageOptimizer.should_summarize(messages, threshold_tokens=16000)
if budget.should_summarize:
    print(f"Need summary: {budget.reason}")

# Offline estimate without API call
budget = dry_summarize(messages)
print(f"Tokens: {budget.estimated_tokens}, Messages: {budget.message_count}")
```

### 6. Accurate Token Counting (v1.1)

```python
from deepseek_token_optimizer import DeepSeekTokenizer

# CJK-aware heuristic by default
tokenizer = DeepSeekTokenizer()
count = tokenizer.count_tokens("Hello 你好")
count = tokenizer.count_message_tokens(messages)

# Optional: load official DeepSeek tokenizer for exact counts
tokenizer = DeepSeekTokenizer(tokenizer_dir="./deepseek_tokenizer")
print(tokenizer.has_official)  # True if tokenizer.json found
```

## Modules

| Module | Description |
|---|---|
| `pricing.py` | Centralized pricing table, model aliases, concurrency limits |
| `tracker.py` | `TokenTracker` — multi-model usage tracking and cost analysis |
| `optimizer.py` | `MessageOptimizer` — thinking control, token estimation, budget checking |
| `strategies.py` | `CacheFriendlyBuilder` — cache-optimized message construction, summarization, compression |
| `cache_utils.py` | Cache hit detection, savings calculation, optimization recommendations |
| `tokenizer.py` | `DeepSeekTokenizer` — accurate token counting with optional official tokenizer |
| `middleware.py` | `DeepSeekMiddleware` — transparent proxy wrapping OpenAI-compatible clients |

## API Reference

### `DeepSeekMiddleware(client, model, auto_summarize, summarize_threshold)`

Transparent proxy wrapping any OpenAI-compatible client with zero-API-change tracking.

| Method | Returns | Description |
|---|---|---|
| `.chat.completions.create(**kwargs)` | response | Auto-tracked API call |
| `print_summary()` | — | Per-model cost breakdown to console |
| `print_recommendations()` | — | Contextual optimization advice |
| `export(filepath)` | — | Export all records as JSON |
| `reset()` | — | Clear all tracking records |

### `TokenTracker(model)`

Track and analyze token usage across multiple models.

| Method | Returns | Description |
|---|---|---|
| `track(usage: TokenUsage)` | — | Track a TokenUsage dataclass |
| `track_request(prompt, completion, cache_hit, cache_miss, reasoning, total, model)` | — | Track raw counts |
| `parse_and_track(usage_dict, model)` | — | Track from API response dict |
| `track_batch(usage_list)` | — | Bulk-import multiple records |
| `total_cost()` | float | Total cost in USD |
| `cost_by_model()` | dict[str, float] | Per-model cost breakdown |
| `total_tokens()` | dict | Aggregate token counts |
| `overall_cache_hit_rate()` | float | 0.0 – 1.0 |
| `potential_savings_report()` | dict | Savings analysis |
| `per_model_summary()` | — | Print per-model summaries |
| `print_summary()` | — | Formatted console output |
| `export(filepath)` | — | Save as JSON |
| `reset()` | — | Clear all records |

### `MessageOptimizer`

Thinking mode control and context analysis.

| Method | Returns | Description |
|---|---|---|
| `disable_thinking(params)` | dict | Remove thinking from API params |
| `set_thinking_effort(params, effort)` | dict | Set effort level (low/high/max) |
| `is_thinking_enabled(params)` | bool | Check thinking state |
| `strip_reasoning_smart(messages)` | list | Per-message reasoning cleanup |
| `estimate_tokens(text)` | int | CJK-aware token estimation |
| `estimate_message_tokens(messages)` | int | Full message array estimation |
| `should_summarize(messages, threshold, threshold_messages)` | `TokenBudget` | Check if summarization needed |

### `CacheFriendlyBuilder(system_prompt, model_variant)`

Cache-optimized message construction for maximum KV cache hit rate.

| Method | Returns | Description |
|---|---|---|
| `build(user_content, history, thinking_params)` | `(messages, api_params)` | Single-turn message + params |
| `build_multi_turn(turns, thinking_effort, task_complexity, task_type)` | `(messages, api_params)` | Multi-turn with thinking control |
| `warm_cache(warmup_content, client, model)` | str | Establish cache prefix via API |
| `set_system_prompt(prompt)` | — | Update stable prefix |
| `system_prompt` | str | Current system prompt (property) |
| `estimated_prefix_tokens` | int | Token count of stable prefix (property) |

### `DeepSeekTokenizer(tokenizer_dir)`

Accurate offline token counting with optional official tokenizer integration.

| Method | Returns | Description |
|---|---|---|
| `count_tokens(text)` | int | Token count for text |
| `count_message_tokens(messages)` | int | Token count for message array |
| `has_official` | bool | Whether official tokenizer is loaded (property) |

### Utility Functions

| Function | Returns | Description |
|---|---|---|
| `summarize_conversation(messages, client, model, max_summary_tokens, char_limit)` | list | Compress history via API; raises `TokenizerError` on failure |
| `dry_summarize(messages, max_summary_tokens)` | `TokenBudget` | Offline summarization estimate |
| `compress_system_prompt(prompt, target_tokens)` | str | Semantic-aware system prompt compression |
| `get_optimal_thinking_config(complexity, type, variant)` | dict | Best thinking/effort config per task |
| `check_cache_hit(response_usage)` | `(hit, miss, rate)` | Parse cache status from API response |
| `compute_cache_savings(hit, miss, model)` | dict | Cost savings from cache hits |
| `recommend_optimizations(hit_rate, msg_count, ctx_tokens, thinking_enabled, model)` | list[str] | Contextual optimization advice |

### Enums & Data Classes

| Type | Fields |
|---|---|
| `TokenBudget` (NamedTuple) | `should_summarize`, `estimated_tokens`, `threshold_tokens`, `message_count`, `reason` |
| `TokenUsage` (dataclass) | `prompt_tokens`, `completion_tokens`, `total_tokens`, `cache_hit_tokens`, `cache_miss_tokens`, `reasoning_tokens`, `model`, `timestamp` |
| `ThinkingMode` (Enum) | `DISABLED`, `ENABLED` |
| `ReasoningEffort` (Enum) | `LOW`, `MEDIUM`, `HIGH`, `MAX` |
| `TokenizerError` (Exception) | Raised by `summarize_conversation` on API failure |

## Optimization Strategy by Task Type

| Task | Thinking | Effort | Context Strategy |
|---|---|---|---|
| Simple Q&A | OFF | — | Fresh each turn |
| Code generation | OFF | — | Cache-warm system prompt |
| Translation | OFF | — | Single request |
| Debugging | ON | `low` | Keep recent 3 turns |
| Architecture design | ON | `high` | Summary at 8 turns |
| Agent orchestration | ON | `high` | Summary at 8 turns, `strip_reasoning_smart` |

## v1.1 Changes

See [CHANGELOG.md](CHANGELOG.md) for full details. Key fixes:

| # | v1.0 Defect | v1.1 Fix |
|---|---|---|
| 1 | PRICING duplicated across files | Centralized in `pricing.py` |
| 2 | TokenTracker fixed to one model | Per-record model, `cost_by_model()`, `reset()` |
| 3 | `summarize_conversation` silently swallows errors | Raises `TokenizerError` with cause chain |
| 4 | `compress_system_prompt` deletes lines from middle | Semantic-section-aware, preserves directives |
| 5 | `_cache_seed` dead code | Removed |
| 6 | `get_optimal_thinking_config` ignores `task_type` | Full `TASK_EFFORT_MAP` matrix |
| 7 | `build_multi_turn` ignores `thinking_effort` | Directly applies when provided |
| 8 | `strip_reasoning` uses single boolean flag | Per-message tool-call detection |
| 9 | Token estimation accuracy low | CJK boundary detection + optional official tokenizer |
| 10 | `recommend_optimizations` always suggests disabling thinking | Checks `thinking_enabled` contextually |
| 11 | Summarization truncates at 500 chars | Configurable `char_limit`, default 2000 |

## License

MIT