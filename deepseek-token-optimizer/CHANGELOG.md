# Changelog

## [1.3.0] — 2026-06-23

### Added
- `DeepSeekMiddleware` and `AsyncDeepSeekMiddleware` — `auto_summarize=True` and `summarize_threshold` for automatic conversation summarization
- `CacheFriendlyBuilder` — `auto_warm=True` and `try_auto_warm()` for automatic cache prefix warming
- `analyze_session(filepath, tag="")` — optional tag filtering in session analysis
- `tag_summary(filepath)` and `print_tag_summary(filepath)` — breakdown of cost by tag
- `CacheFriendlyBuilder.cache_established` property and auto-invalidation on `set_system_prompt()`
- Middleware `tag` parameter and `set_tag()` method for per-request tag propagation

### Changed
- Version bumped to 1.3.0

## [1.2.0] — 2026-06-14

### Added
- `AsyncDeepSeekMiddleware` — async wrapper for `AsyncOpenAI` clients
- `estimate_api_cost()` — pre-call cost estimation from message tokens
- `TokenTracker.track_stream()` — accumulate tokens from streaming responses
- `TokenTracker.estimate_cost()` — static method for pre-call cost estimates
- `analyzer.py` — `analyze_session()`, `compare_sessions()`, `print_session_comparison()` for batch analysis
- `get_rate_limit_warning()` — concurrency/rate limit monitoring
- `DeepSeekMiddleware` now supports streaming (yield chunks, track at end)
- `CONTEXT_LIMITS`, `OUTPUT_LIMITS` in pricing module
- `TokenTracker.load_export()` — load JSON exports for analysis

### Changed
- `token_tracker.parse_and_track()` accepts optional `model` parameter
- `DeepSeekMiddleware._handle_request()` now supports `stream=True`
- All pricing uses centralized `pricing.py` module (no duplicates)

### Fixed
- All modules now consistently import from centralized `pricing`
- Nested class resolution in middleware proxy classes
- Version bumped to 1.2.0

## [1.1.0] — 2026-06-12

### Fixed (11 defects from v1.0)
- PRICING centralized into pricing.py
- Multi-model tracking in TokenTracker
- summarize_conversation raises on failure
- compress_system_prompt semantic-aware
- get_optimal_thinking_config uses task_type
- build_multi_turn respects thinking_effort
- strip_reasoning_smart per-message detection
- Improved token estimation
- Contextual recommend_optimizations

### Added
- pricing.py, tokenizer.py, middleware.py modules
- TokenBudget named tuple
- dry_summarize() offline estimation
- DeepSeekTokenizer with official tokenizer support

## [1.0.0] — Initial release