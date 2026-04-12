"""
SlimZero Core Module

Main SlimZero class and pipeline runner.
"""

import json
import logging
from typing import Optional, Any, List, Dict

from slimzero.schemas import (
    IntentSchema,
    StageInput,
    StageOutput,
    SlimZeroResult,
    AgentResult,
    OutputFormat,
    HallucinationRiskTier,
)
from slimzero.exceptions import (
    SlimZeroError,
    SlimZeroInputError,
)

logger = logging.getLogger(__name__)

from slimzero.stages.intent import IntentExtractor
from slimzero.stages.rewriter import PromptRewriter
from slimzero.stages.semantic_guard import SemanticGuard
from slimzero.stages.few_shot import FewShotRanker
from slimzero.stages.history import HistoryCompressor
from slimzero.stages.injector import ResponseFormatInjector
from slimzero.stages.hallucination import HallucinationRiskScorer
from slimzero.stages.budget import TokenBudgetEnforcer
from slimzero.post.validator import ResponseValidator
from slimzero.post.flagger import HallucinationFlagger
from slimzero.post.logger import SavingsLogger
from slimzero.agent.ralph import RalphLoop
from slimzero.dashboard import get_dashboard, SlimZeroDashboard

DEFAULT_TOKEN_BUDGET = 512


class SlimZero:
    """
    Main SlimZero class for prompt compression and LLM optimization.

    Usage:
        from slimzero import SlimZero

        sz = SlimZero(model="claude-sonnet-4-6")
        result = sz.call(prompt="Explain gradient descent in detail please.")
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        api_client: Optional[Any] = None,
        token_budget: Optional[int] = None,
        sim_threshold: float = 0.92,
        few_shot_k: int = 3,
        history_window: int = 4,
        hallucination_guard: bool = True,
        response_validation: bool = True,
        agent_mode: bool = False,
        max_agent_steps: int = 20,
        max_retries: int = 3,
        drift_threshold: float = 0.75,
        dashboard: bool = False,
        log_file: Optional[str] = None,
    ):
        self.model = model
        self.api_client = api_client
        self.token_budget = token_budget or DEFAULT_TOKEN_BUDGET
        self.sim_threshold = sim_threshold
        self.few_shot_k = few_shot_k
        self.history_window = history_window
        self.hallucination_guard = hallucination_guard
        self.response_validation = response_validation
        self.agent_mode = agent_mode
        self.max_agent_steps = max_agent_steps
        self.max_retries = max_retries
        self.drift_threshold = drift_threshold
        self.dashboard = dashboard
        self.log_file = log_file

        self._intent_extractor = IntentExtractor()
        self._rewriter = PromptRewriter()
        self._semantic_guard = SemanticGuard(threshold=sim_threshold)
        self._few_shot_ranker = FewShotRanker(k=few_shot_k)
        self._history_compressor = HistoryCompressor(window=history_window)
        self._response_injector = ResponseFormatInjector()
        self._hallucination_scorer = HallucinationRiskScorer()
        self._budget_enforcer = TokenBudgetEnforcer(token_budget=self.token_budget)
        self._response_validator = ResponseValidator()
        self._hallucination_flagger = HallucinationFlagger()
        self._savings_logger = SavingsLogger()

        self._ralph_loop: Optional[RalphLoop] = None
        if agent_mode:
            self._init_agent()

        self._dashboard: Optional[SlimZeroDashboard] = None
        if dashboard:
            self._init_dashboard()

    def _init_agent(self) -> None:
        """Initialize the Ralph agent loop."""
        self._ralph_loop = RalphLoop(
            max_steps=self.max_agent_steps,
            max_retries_per_step=self.max_retries,
            drift_threshold=self.drift_threshold,
            api_client=self.api_client,
        )

    def _init_dashboard(self) -> None:
        """Initialize the live dashboard."""
        self._dashboard = get_dashboard()
        if self._dashboard.is_enabled:
            self._dashboard.start()

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count."""
        return len(text.split())

    def _call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Call the LLM API.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt

        Returns:
            LLM response text
        """
        if self.api_client:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = self.api_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
                content: str = response.choices[0].message.content
                return content
            except Exception as e:
                logger.warning(f"API call failed: {e}")
                return f"[API Error: {e}]"

        return f"[Mock response for: {prompt[:50]}...]"

    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        few_shot_examples: Optional[List[str]] = None,
    ) -> SlimZeroResult:
        """
        Process a single prompt through the SlimZero pipeline.

        Pipeline order:
        1. Intent Extractor
        2. Prompt Rewriter
        3. Semantic Guard
        4. Few-Shot Ranker
        5. History Compressor
        6. Response Format Injector
        7. Hallucination Risk Scorer
        8. Token Budget Enforcer
        9. LLM Call
        10. Response Validator (post)
        11. Hallucination Flagger (post)
        12. Savings Logger (post)

        Args:
            prompt: The user prompt to process
            system_prompt: Optional system prompt to prepend
            history: Optional conversation history
            few_shot_examples: Optional few-shot examples

        Returns:
            SlimZeroResult with optimized response
        """
        if not prompt or not prompt.strip():
            raise SlimZeroInputError("Prompt cannot be empty", field_name="prompt")

        original_prompt = prompt
        original_tokens = self._estimate_tokens(original_prompt)
        stages_applied: List[str] = []

        try:
            intent = self._intent_extractor.extract(prompt)
            stages_applied.append("intent_extractor")

            inp = StageInput(
                prompt=prompt,
                intent=intent,
                token_count=original_tokens,
                system_prompt=system_prompt,
                history=history,
                few_shot_examples=few_shot_examples,
            )

            rewriter_out = self._rewriter.process(inp)
            stages_applied.append("prompt_rewriter")
            rewritten_prompt = rewriter_out.prompt

            inp.metadata["original_prompt"] = original_prompt
            inp.metadata["rewritten_prompt"] = rewritten_prompt

            guard_out = self._semantic_guard.process(inp)
            semantic_similarity = guard_out.metadata.get("similarity", 1.0)
            validated_prompt = guard_out.prompt

            if inp.few_shot_examples:
                few_shot_out = self._few_shot_ranker.process(inp)
                stages_applied.append("few_shot_ranker")
                few_shot_examples = few_shot_out.metadata.get("retained_examples", few_shot_examples)

            if history:
                history_out = self._history_compressor.process(inp)
                stages_applied.append("history_compressor")
                compressed_history = history_out.metadata.get("compressed_history", history)
                prior_context = history_out.metadata.get("prior_context")
                inp.metadata["prior_context"] = prior_context
            else:
                compressed_history = history

            injector_out = self._response_injector.process(inp)
            stages_applied.append("response_format_injector")
            injected_system = injector_out.metadata.get("modified_system_prompt", system_prompt)
            injected_fragment = injector_out.metadata.get("fragment_used")

            halluc_out = self._hallucination_scorer.process(inp)
            stages_applied.append("hallucination_risk_scorer")
            hallucination_risk_tier = HallucinationRiskTier(halluc_out.metadata["risk_tier"])

            inp.metadata["injected_fragment"] = injected_fragment
            budget_out = self._budget_enforcer.process(inp)
            stages_applied.append("token_budget_enforcer")
            final_prompt = budget_out.prompt
            final_system = budget_out.metadata.get("modified_system_prompt", injected_system)

            sent_tokens = budget_out.token_count or self._estimate_tokens(final_prompt)

            response = self._call_llm(final_prompt, final_system)
            stages_applied.append("llm_call")

            validation_result = self._response_validator.validate_with_metadata(
                intent, response
            )
            stages_applied.append("response_validator")

            flag_result = self._hallucination_flagger.flag(response)
            stages_applied.append("hallucination_flagger")

            self._savings_logger.log_call(
                original_input_tokens=original_tokens,
                sent_input_tokens=sent_tokens,
                estimated_output_tokens=self._estimate_tokens(response),
                stages_applied=stages_applied,
                semantic_similarity=semantic_similarity,
                hallucination_risk_tier=hallucination_risk_tier,
                response_validated=validation_result["validation_passed"],
                flags_raised=flag_result["total_flags"],
            )

            if self._dashboard and self._dashboard.is_enabled:
                self._dashboard.log_call(
                    original_tokens=original_tokens,
                    sent_tokens=sent_tokens,
                    similarity=semantic_similarity,
                    hallucination_flags=flag_result["total_flags"],
                )

            flag_categories = list(flag_result["categories"].keys()) if flag_result["has_flags"] else []

            return SlimZeroResult(
                response=response,
                original_prompt=original_prompt,
                sent_prompt=final_prompt,
                original_input_tokens=original_tokens,
                sent_input_tokens=sent_tokens,
                estimated_output_tokens=self._estimate_tokens(response),
                stages_applied=stages_applied,
                semantic_similarity=semantic_similarity,
                hallucination_risk_tier=hallucination_risk_tier,
                response_validated=validation_result["validation_passed"],
                flags_raised=flag_categories,
                metadata={"intent": intent.to_dict()},
            )

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            stages_applied.append(f"error: {type(e).__name__}")

            response = self._call_llm(original_prompt, system_prompt)
            stages_applied.append("llm_call_fallback")

            return SlimZeroResult(
                response=response,
                original_prompt=original_prompt,
                sent_prompt=original_prompt,
                original_input_tokens=original_tokens,
                sent_input_tokens=original_tokens,
                estimated_output_tokens=self._estimate_tokens(response),
                stages_applied=stages_applied,
                semantic_similarity=1.0,
                hallucination_risk_tier=HallucinationRiskTier.LOW,
                response_validated=True,
                flags_raised=[],
                metadata={},
            )

    def run_goal(
        self,
        goal: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        initial_plan: Optional[str] = None,
    ) -> AgentResult:
        """
        Run a goal through the agent loop with SlimZero compression.

        Each step in the agent loop applies SlimZero compression to reduce costs.

        Args:
            goal: The goal to accomplish
            tools: List of tool definitions available to the agent
            initial_plan: Optional initial plan for the goal

        Returns:
            AgentResult with output, audit trail, and statistics
        """
        if not self.agent_mode:
            raise SlimZeroError(
                "agent_mode must be enabled to use run_goal. "
                "Initialize SlimZero with agent_mode=True"
            )

        if self._ralph_loop is None:
            self._init_agent()

        assert self._ralph_loop is not None, "Ralph loop not initialized"

        logger.info(f"Starting agent goal: {goal[:50]}...")

        try:
            agent_output = self._ralph_loop.run(
                goal=goal,
                tools=tools,
                initial_plan=initial_plan,
            )

            audit_trail = json.loads(agent_output.get("audit_log", "[]"))
            total_tokens_saved = self._savings_logger.get_cumulative_stats().get(
                "cumulative_tokens_saved", 0
            )

            output = agent_output.get("result", "unknown")
            if agent_output.get("result") == "max_steps_reached":
                output = f"Goal partially completed after {agent_output['steps']} steps"
            elif agent_output.get("result") == "circuit_breaker":
                output = f"Circuit breaker triggered: {agent_output.get('reason', 'unknown')}"
            elif agent_output.get("result") == "drift_detected":
                output = f"Semantic drift detected at similarity {agent_output.get('similarity', 0):.2f}"

            result = AgentResult(
                goal=goal,
                output=output,
                result=agent_output.get("result", "unknown"),
                steps=agent_output.get("steps", 0),
                total_tokens_saved=total_tokens_saved,
                audit_trail=audit_trail,
                metadata={
                    "agent_result": agent_output.get("result"),
                    "reason": agent_output.get("reason"),
                    "similarity": agent_output.get("similarity"),
                    "compression_stages": self._savings_logger.get_cumulative_stats(),
                },
            )

            logger.info(f"Agent goal complete: {result.result}, steps={result.steps}")
            return result

        except Exception as e:
            logger.error(f"Agent error: {e}")
            return AgentResult(
                goal=goal,
                output=f"Error: {str(e)}",
                result="error",
                steps=0,
                total_tokens_saved=0,
                metadata={"error": str(e)},
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get cumulative savings statistics."""
        return self._savings_logger.get_cumulative_stats()

    def export_stats_json(self, filepath: Optional[str] = None) -> str:
        """Export session statistics to JSON."""
        return self._savings_logger.export_json(filepath)

    def export_stats_markdown(self, filepath: Optional[str] = None) -> str:
        """Export session statistics to Markdown."""
        return self._savings_logger.export_markdown(filepath)
