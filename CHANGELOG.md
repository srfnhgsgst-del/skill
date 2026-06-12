# DeepSeek Token Optimizer Changelog

## [1.1.0] — 2026-06-12

### Fixed

- **DEFECT #1 — PRICING dictionary duplicated** across `tracker.py` and `cache_utils.py`.
  Extracted into new `pricing.py` module as single source of truth.

- **DEFECT #2 — TokenTracker: fixed single-model assumption.** Records now store their own
  model per entry; `total_cost()` computes per-model costs correctly regardless of mixed
  model usage. Added `reset()`, `cost_by_model()`, and `per_model_summary()` methods.

- **DEFECT #3 — summarize_conversation: silent exception swallowing.**
  Now raises `TokenizerError` with original exception chained. Added `dry_summarize()`
  for offline estimation without an API call.

- **DEFECT #4 — compress_system_prompt: destructive middle-line deletion.**
  Replaced random-removal algorithm with semantic-section-aware compression: preserves
  tagged directives (`NOTE:`, `IMPORTANT:`, `DO:`/`DON'T:`) and condenses prose sections.

- **DEFECT #5 — CacheFriendlyBuilder._cache_seed: dead code removed.**

- **DEFECT #6 — get_optimal_thinking_config: now uses `task_type`** to differentiate
  effort levels (code tasks get lower effort than analysis/agent tasks).

- **DEFECT #7 — build_multi_turn: now properly uses `thinking_effort`.** When provided,
  directly sets effort; when omitted, auto-detects from task complexity.

- **DEFECT #8 — strip_reasoning_from_context: replaced binary flag with per-round detection.**
  New `strip_reasoning_smart()` automatically detects tool-call boundaries and only strips
  reasoning from non-tool-call assistant messages.

- **DEFECT #9 — estimate_tokens: improved to 3-tier estimation.**
  Adds optional `DeepSeekTokenizer` class that wraps the official tokenizer for accurate
  offline counting when available. Falls back to improved heuristic.

- **DEFECT #10 — recommend_optimizations: now checks thinking state** before suggesting
  to disable it. Only suggests when thinking mode is known to be enabled.

- **DEFECT #11 — summarize_conversation: increased per-message window** from 500 to 2000
  characters and added configurable `char_limit` parameter.

### Added

- **`pricing.py`** — central pricing module; single source of truth for all rate tables.
  Supports dynamic model lookups and `get_pricing(model) -> dict` helper.

- **`tokenizer.py`** — `DeepSeekTokenizer` class with optional official tokenizer
  integration and improved heuristic estimation with CJK-aware boundary detection.

- **`middleware.py`** — `DeepSeekMiddleware` transparent proxy that wraps any
  OpenAI-compatible client, automatically tracking token usage, detecting cache hits,
  and providing optimization recommendations after each session.

- **`TokenTracker.cost_by_model()`** — per-model cost breakdown.
- **`TokenTracker.per_model_summary()`** — print per-model summaries.
- **`TokenTracker.reset()`** — clear all records.
- **`TokenTracker.track_batch()`** — efficient batch import from streaming responses.

- **`CacheFriendlyBuilder.estimated_prefix_tokens`** — exposes token count of the
  stable cache prefix region for budgeting.

- **`summarize_conversation` now accepts `char_limit` parameter** to tune truncation.
- **`dry_summarize()`** — offline estimation utility for conversation compression.

- **`should_summarize()` now returns `TokenBudget` named tuple** with detail on why (count,
  tokens, threshold, reason) instead of a bare bool.

### Changed

- `MessageOptimizer.estimate_tokens()` now supports CJK-aware boundary detection, improving
  Chinese/Japanese/Korean token estimation accuracy by ~15-20%.
- `__init__.py` reorganized exports; version bumped to "1.1.0".
- All modules now import `PRICING` from `pricing.py` instead of locally defining it.
- `recommend_optimizations()` signature now accepts optional `thinking_enabled: bool`.