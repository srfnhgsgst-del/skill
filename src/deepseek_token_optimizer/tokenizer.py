"""
Optional DeepSeek tokenizer integration for accurate offline token counting.

To use the official tokenizer:
1. Download deepseek_v3_tokenizer.zip from https://cdn.deepseek.com/api-docs/
2. Extract to a directory
3. Pass tokenizer_dir to DeepSeekTokenizer

Without the official tokenizer, falls back to improved heuristic estimation.
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class DeepSeekTokenizer:
    """
    Accurate token counting using DeepSeek's official tokenizer when available,
    falling back to CJK-aware heuristic estimation.

    Usage:
        t = DeepSeekTokenizer()
        t = DeepSeekTokenizer(tokenizer_dir="./deepseek_tokenizer")

        count = t.count_tokens("Hello world")
        count = t.count_message_tokens(messages)
    """

    def __init__(self, tokenizer_dir: Optional[str] = None):
        self._tokenizer = None
        self._has_official = False

        if tokenizer_dir and os.path.isdir(tokenizer_dir):
            self._load_official(tokenizer_dir)

    def _load_official(self, tokenizer_dir: str):
        try:
            tokenizer_json = os.path.join(tokenizer_dir, "tokenizer.json")
            config_json = os.path.join(tokenizer_dir, "tokenizer_config.json")

            if os.path.isfile(tokenizer_json):
                with open(tokenizer_json, "r", encoding="utf-8") as f:
                    self._tokenizer_data = json.load(f)
                self._has_official = True
                logger.info("Loaded official DeepSeek tokenizer from %s", tokenizer_dir)
            else:
                logger.warning(
                    "tokenizer.json not found in %s, using heuristic estimation",
                    tokenizer_dir,
                )
        except Exception as e:
            logger.warning("Failed to load official tokenizer: %s", e)

    @property
    def has_official(self) -> bool:
        return self._has_official

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text. Uses official tokenizer if available,
        otherwise falls back to heuristic estimation.
        """
        if not text:
            return 0

        if self._has_official and self._tokenizer_data:
            return self._official_count(text)
        return self._heuristic_count(text)

    def count_message_tokens(self, messages: list) -> int:
        total = 0
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, str):
                total += self.count_tokens(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        total += self.count_tokens(part.get("text", ""))
            reasoning = msg.get("reasoning_content", "")
            if reasoning:
                total += self.count_tokens(reasoning)
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    func = tc.get("function", {})
                    total += self.count_tokens(
                        json.dumps(func, ensure_ascii=False)
                    )
        return max(1, total)

    def _official_count(self, text: str) -> int:
        """
        Estimate token count using the official DeepSeek tokenizer's BPE
        vocabulary when the full tokenizer library is not available.

        Falls back to heuristic if merge rules can't be applied.
        """
        try:
            vocab = self._tokenizer_data.get("model", {}).get("vocab", {})
            if not vocab:
                raise ValueError("No vocab in tokenizer data")

            merges = self._tokenizer_data.get("model", {}).get("merges", [])

            merged = text
            for merge_pair in merges:
                if isinstance(merge_pair, list) and len(merge_pair) == 2:
                    pair = " ".join(merge_pair)
                    merged = merged.replace(pair, "".join(merge_pair))

            tokens = 0
            i = 0
            while i < len(merged):
                matched = False
                for end in range(min(i + 50, len(merged)), i, -1):
                    candidate = merged[i:end]
                    if candidate in vocab:
                        tokens += 1
                        i = end
                        matched = True
                        break
                if not matched:
                    tokens += 1
                    i += 1
            return max(1, tokens)
        except Exception:
            return self._heuristic_count(text)

    def _heuristic_count(self, text: str) -> int:
        """CJK-aware heuristic token estimation."""
        if not text:
            return 0

        cjk_ranges = [
            (0x4E00, 0x9FFF),
            (0x3400, 0x4DBF),
            (0xAC00, 0xD7AF),
            (0x3040, 0x30FF),
            (0x31F0, 0x31FF),
        ]

        tokens = 0
        consecutive_other = 0

        for c in text:
            cp = ord(c)
            is_cjk = any(lo <= cp <= hi for lo, hi in cjk_ranges)

            if is_cjk:
                if consecutive_other > 0:
                    tokens += consecutive_other * 0.3
                    consecutive_other = 0
                tokens += 0.6
            else:
                consecutive_other += 1

        if consecutive_other > 0:
            tokens += consecutive_other * 0.3

        return max(1, int(tokens))