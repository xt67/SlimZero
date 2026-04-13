"""
SlimZero Savings Logger (post-processing)

Tracks per-call and cumulative statistics for token savings.
Provides JSON and Markdown export capabilities.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path

from slimzero.schemas import HallucinationRiskTier

logger = logging.getLogger(__name__)

DEFAULT_COST_PER_1K_TOKENS = 0.002


class SavingsLogger:
    """
    Tracks and logs token savings statistics.

    Tracks per-call and cumulative statistics including:
    - original_input_tokens, sent_input_tokens, delta_input
    - estimated_output_tokens, stages_applied
    - semantic_similarity, hallucination_risk_tier
    - response_validated, flags_raised
    - cumulative_tokens_saved, cumulative_estimated_cost_usd
    """

    MODEL_PRICING = {
        "claude-sonnet-4-6": {"input": 0.000003, "output": 0.000015},
        "claude-opus-4-6": {"input": 0.000015, "output": 0.000075},
        "gpt-4o": {"input": 0.000005, "output": 0.000015},
        "default": {"input": 0.000005, "output": 0.000015},
    }

    def __init__(
        self,
        cost_per_1k_tokens: float = DEFAULT_COST_PER_1K_TOKENS,
        log_dir: Optional[str] = None,
        model: str = "default",
    ):
        """
        Initialize SavingsLogger.

        Args:
            cost_per_1k_tokens: Cost per 1K tokens in USD.
            log_dir: Directory for log files.
            model: Model name for pricing lookup.
        """
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.log_dir = Path(log_dir) if log_dir else None
        self.model = model
        self._session_logs: List[Dict[str, Any]] = []
        self._cumulative_tokens_saved = 0
        self._cumulative_cost_saved = 0.0

    def _current_timestamp(self) -> str:
        """Get current ISO timestamp."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def log_call(
        self,
        original_input_tokens: int,
        sent_input_tokens: int,
        estimated_output_tokens: Optional[int] = None,
        stages_applied: Optional[List[str]] = None,
        semantic_similarity: Optional[float] = None,
        hallucination_risk_tier: Optional[HallucinationRiskTier] = None,
        response_validated: bool = False,
        flags_raised: int = 0,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Log a single call.

        Args:
            original_input_tokens: Original input token count.
            sent_input_tokens: Actual tokens sent to LLM.
            estimated_output_tokens: Estimated output tokens.
            stages_applied: List of stages applied.
            semantic_similarity: Semantic similarity score.
            hallucination_risk_tier: Risk tier.
            response_validated: Whether response was validated.
            flags_raised: Number of flags raised.
            context: Additional context.

        Returns:
            Dict with call statistics.
        """
        delta_input = original_input_tokens - sent_input_tokens
        cost_saved = (delta_input / 1000) * self.cost_per_1k_tokens

        self._cumulative_tokens_saved += delta_input
        self._cumulative_cost_saved += cost_saved

        call_log: Dict[str, Any] = {
            "timestamp": self._current_timestamp(),
            "stage": "savings_logger",
            "original_input_tokens": original_input_tokens,
            "sent_input_tokens": sent_input_tokens,
            "delta_input": delta_input,
            "estimated_output_tokens": estimated_output_tokens,
            "stages_applied": stages_applied or [],
            "semantic_similarity": semantic_similarity,
            "hallucination_risk_tier": (
                hallucination_risk_tier.value if hallucination_risk_tier else None
            ),
            "response_validated": response_validated,
            "flags_raised": flags_raised,
            "cumulative_tokens_saved": self._cumulative_tokens_saved,
            "cumulative_estimated_cost_usd": round(self._cumulative_cost_saved, 6),
            "context": context or {},
        }

        self._session_logs.append(call_log)
        logger.info(
            f"SavingsLogger: saved {delta_input} tokens, "
            f"cumulative: {self._cumulative_tokens_saved} tokens, "
            f"${self._cumulative_cost_saved:.6f}"
        )

        return call_log

    def get_cumulative_stats(self) -> Dict[str, Any]:
        """
        Get cumulative statistics.

        Returns:
            Dict with cumulative statistics.
        """
        model_pricing = self.MODEL_PRICING.get(self.model, self.MODEL_PRICING["default"])
        cost_per_token = model_pricing["input"]
        cost_saved = self._cumulative_tokens_saved * cost_per_token

        return {
            "cumulative_tokens_saved": self._cumulative_tokens_saved,
            "cumulative_estimated_cost_usd": round(cost_saved, 6),
            "model": self.model,
            "model_pricing_per_token": cost_per_token,
            "total_calls": len(self._session_logs),
            "avg_tokens_saved_per_call": (
                self._cumulative_tokens_saved / len(self._session_logs)
                if self._session_logs else 0
            ),
        }

    def export_json(self, filepath: Optional[str] = None) -> str:
        """
        Export session logs to JSON.

        Args:
            filepath: Optional file path to save JSON.

        Returns:
            JSON string.
        """
        export_data = {
            "export_timestamp": self._current_timestamp(),
            "stats": self.get_cumulative_stats(),
            "calls": self._session_logs,
        }

        json_str = json.dumps(export_data, indent=2)

        if filepath:
            save_path: Path = Path(filepath)
            if self.log_dir:
                save_path = self.log_dir / save_path
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(json_str, encoding="utf-8")
            logger.info(f"Exported JSON to {save_path}")

        return json_str

    def export_markdown(self, filepath: Optional[str] = None) -> str:
        """
        Export session logs to Markdown summary.

        Args:
            filepath: Optional file path to save Markdown.

        Returns:
            Markdown string.
        """
        stats = self.get_cumulative_stats()

        md_lines = [
            "# SlimZero Session Summary",
            "",
            f"**Export Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "",
            "## Cumulative Statistics",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Calls | {stats['total_calls']} |",
            f"| Tokens Saved (Total) | {stats['cumulative_tokens_saved']} |",
            f"| Cost Saved (USD) | ${stats['cumulative_estimated_cost_usd']:.6f} |",
            f"| Avg Tokens Saved/Call | {stats['avg_tokens_saved_per_call']:.1f} |",
            "",
        ]

        if self._session_logs:
            md_lines.extend([
                "## Recent Calls",
                "",
                "| Timestamp | Original | Sent | Saved | Similarity | Risk | Flags |",
                "|-----------|----------|------|-------|------------|------|-------|",
            ])

            for call in self._session_logs[-10:]:
                md_lines.append(
                    f"| {call['timestamp']} | "
                    f"{call['original_input_tokens']} | "
                    f"{call['sent_input_tokens']} | "
                    f"{call['delta_input']} | "
                    f"{call.get('semantic_similarity', 'N/A')} | "
                    f"{call.get('hallucination_risk_tier', 'N/A')} | "
                    f"{call['flags_raised']} |"
                )

        md_str = "\n".join(md_lines)

        if filepath:
            save_path: Path = Path(filepath)
            if self.log_dir:
                save_path = self.log_dir / save_path
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(md_str, encoding="utf-8")
            logger.info(f"Exported Markdown to {save_path}")

        return md_str

    def reset(self) -> None:
        """Reset cumulative statistics."""
        self._session_logs.clear()
        self._cumulative_tokens_saved = 0
        self._cumulative_cost_saved = 0.0
        logger.info("SavingsLogger: session reset")
