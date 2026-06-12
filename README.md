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
git clone https://github.com/your-org/deepseek-token-optimizer.git
cd deepseek-token-optimizer
pip install -e .
```

## Quick Start

### 1. Transparent Middleware (v1.1 new)

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

### 2. Token Tracker with Multi-Model Support (v1.1 improved)

```python
from deepseek_token_optimizer import TokenTracker

tracker = TokenTracker()
tracker.parse_and_track(flash_response.usage.__dict__, model="deepseek-v4-flash")
tracker.parse_and_track(pro_response.usage.__dict__, model="deepseek-v4-pro")
tracker.print_summary()  # prints per-model breakdown
print(tracker.cost_by_model())  # {'deepseek-v4-flash': 0.0003, 'deepseek-v4-pro': 0.0008}
```

### 3. Smart Reasoning Stripping (v1.1 fixed)

```python
from deepseek_token_optimizer import MessageOptimizer

# Automatically detects tool-call boundaries per assistant message
cleaned = MessageOptimizer.strip_reasoning_smart(messages)
```

### 4. Cache-Friendly Messages (v1.1 improved)

```python
from deepseek_token_optimizer import CacheFriendlyBuilder

builder = CacheFriendlyBuilder(
    system_prompt="You are a Python coding assistant.",
)
builder.set_system_prompt("...")

# Now returns (messages, api_params) tuple
messages, params = builder.build("sort a list", thinking_params={"extra_body": {"thinking": {"type": "disabled"}}})
```

### 5. Accurate Token Counting (v1.1 new)

```python
from deepseek_token_optimizer import DeepSeekTokenizer

# Falls back to improved heuristic if official tokenizer not found
tokenizer = DeepSeekTokenizer()  # or DeepSeekTokenizer(tokenizer_dir="./tokenizer/")
count = tokenizer.count_tokens("Hello world")
count = tokenizer.count_message_tokens(messages)
```

## API Reference

### `DeepSeekMiddleware` (NEW v1.1)
- Transparent proxy wrapping any OpenAI-compatible client
- Auto-tracks all token usage on `.chat.completions.create()`
- `print_summary()` — per-model cost breakdown
- `print_recommendations()` — contextual optimization advice
- `export(filepath)` / `reset()`

### `TokenTracker`
- `track(usage)` / `track_request(...)` / `parse_and_track(dict, model=...)`
- `track_batch(list)` (NEW) — import from streaming responses
- `total_cost()` / `cost_by_model()` (NEW) / `total_tokens()`
- `overall_cache_hit_rate()` / `potential_savings_report()`
- `per_model_summary()` (NEW) / `print_summary()` / `export(filepath)`
- `reset()` (NEW)

### `MessageOptimizer`
- `disable_thinking(params)` / `set_thinking_effort(params, effort)`
- `is_thinking_enabled(params)` (NEW)
- `strip_reasoning_smart(messages)` (NEW — replaces `strip_reasoning_from_context`)
- `estimate_tokens(text)` / `estimate_message_tokens(messages)`
- `should_summarize(messages, threshold, threshold_messages)` → `TokenBudget` (NEW)

### `CacheFriendlyBuilder`
- `build(user_content, history, thinking_params)` → `(messages, api_params)` (CHANGED)
- `build_multi_turn(turns, thinking_effort, task_complexity, task_type)` → `(messages, api_params)` (FIXED)
- `warm_cache(warmup_content, client, model)` → str
- `estimated_prefix_tokens` (NEW) / `system_prompt` properties

### `DeepSeekTokenizer` (NEW v1.1)
- `count_tokens(text)` → int
- `count_message_tokens(messages)` → int
- `has_official` — whether official tokenizer is loaded

### Utility Functions
- `summarize_conversation(messages, client, model, max_tokens, char_limit)` → list (FIXED — raises on error)
- `dry_summarize(messages, max_tokens)` (NEW) → TokenBudget estimate
- `compress_system_prompt(prompt, target_tokens)` → str (FIXED — semantic-aware)
- `get_optimal_thinking_config(complexity, type, variant)` → dict (FIXED — uses task_type)
- `check_cache_hit(response_usage)` → tuple
- `compute_cache_savings(hit, miss, model)` → dict
- `recommend_optimizations(..., thinking_enabled, model)` → list (FIXED — contextual)

## v1.1 Changes

See [CHANGELOG.md](CHANGELOG.md) for full details. Key fixes:

| # | v1.0 Defect | v1.1 Fix |
|---|---|---|
| 1 | PRICING duplicated in 2 files | Centralized in `pricing.py` |
| 2 | TokenTracker fixed to one model | Per-record model, `cost_by_model()` |
| 3 | summarize_conversation silently fails | Raises `TokenizerError` with cause |
| 4 | compress deletes lines from middle | Semantic-section-aware compression |
| 5 | `_cache_seed` dead code | Removed |
| 6 | `get_optimal_thinking_config` ignores task_type | Full `TASK_EFFORT_MAP` matrix |
| 7 | `build_multi_turn` ignores thinking_effort | Directly applies when provided |
| 8 | `strip_reasoning` uses binary flag | Per-message tool-call detection |
| 9 | Token estimation accuracy low | CJK + optional official tokenizer |
| 10 | recommend always suggests disabling thinking | Checks `thinking_enabled` flag |
| 11 | summarize truncates at 500 chars | Configurable `char_limit`, default 2000 |

## License

MIT