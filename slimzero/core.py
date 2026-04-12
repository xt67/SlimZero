"""
SlimZero Core Module

Main SlimZero class and pipeline runner.
"""

from typing import Optional, Any, List

from slimzero.schemas import (
    IntentSchema,
    StageInput,
    StageOutput,
    SlimZeroResult,
    OutputFormat,
    HallucinationRiskTier,
    SavingsStats,
)
from slimzero.exceptions import (
    SlimZeroError,
    SlimZeroInputError,
)


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
        self.token_budget = token_budget
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

    def call(self, prompt: str, system_prompt: Optional[str] = None) -> SlimZeroResult:
        """
        Process a single prompt through the SlimZero pipeline.

        Args:
            prompt: The user prompt to process
            system_prompt: Optional system prompt to prepend

        Returns:
            SlimZeroResult with optimized response
        """
        raise NotImplementedError("Pipeline implementation pending US-013")

    def run_goal(self, goal: str, tools: Optional[List[Any]] = None):
        """
        Run a goal through the agent loop (requires agent_mode=True).

        Args:
            goal: The goal to accomplish
            tools: List of tools available to the agent

        Returns:
            Agent result with audit trail
        """
        if not self.agent_mode:
            raise SlimZeroError(
                "agent_mode must be enabled to use run_goal"
            )
        raise NotImplementedError("Agent implementation pending US-015")
