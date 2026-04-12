"""
SlimZero Plugin API (US-017)

BaseStage interface and plugin system for extending SlimZero pipelines.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from slimzero.schemas import StageInput, StageOutput


class BaseStage(ABC):
    """
    Abstract base class for SlimZero pipeline stages.

    Plugin contract:
    - Must not raise exceptions that halt pipeline
    - Must not make external API calls
    - Plugins that modify prompts must set modified=True so semantic guard re-runs
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stage name."""
        pass

    @property
    def description(self) -> str:
        """Return a description of the stage."""
        return ""

    @abstractmethod
    def process(self, inp: StageInput) -> StageOutput:
        """
        Process the stage input.

        Args:
            inp: StageInput containing the prompt and metadata.

        Returns:
            StageOutput with modified prompt (if applicable).
        """
        pass

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate stage configuration.

        Returns:
            Tuple of (is_valid, error_message).
        """
        return True, None

    def on_error(self, error: Exception) -> StageOutput:
        """
        Handle errors gracefully.

        Args:
            error: The exception that occurred.

        Returns:
            StageOutput that allows pipeline to continue.
        """
        return StageOutput(
            prompt="",
            modified=False,
            notes=f"Stage {self.name} error: {type(error).__name__}",
        )


class PluginRegistry:
    """Registry for SlimZero plugins."""

    def __init__(self):
        """Initialize registry."""
        self._stages: Dict[str, BaseStage] = {}
        self._enabled: List[str] = []

    def register(self, stage: BaseStage) -> None:
        """
        Register a plugin stage.

        Args:
            stage: BaseStage implementation to register.
        """
        is_valid, error = stage.validate()
        if not is_valid:
            raise ValueError(f"Invalid stage '{stage.name}': {error}")

        self._stages[stage.name] = stage

    def unregister(self, name: str) -> None:
        """Unregister a stage by name."""
        if name in self._stages:
            del self._stages[name]
        if name in self._enabled:
            self._enabled.remove(name)

    def get(self, name: str) -> Optional[BaseStage]:
        """Get a registered stage by name."""
        return self._stages.get(name)

    def enable(self, name: str) -> None:
        """Enable a stage for use in pipeline."""
        if name in self._stages and name not in self._enabled:
            self._enabled.append(name)

    def disable(self, name: str) -> None:
        """Disable a stage."""
        if name in self._enabled:
            self._enabled.remove(name)

    def get_enabled(self) -> List[BaseStage]:
        """Get list of enabled stages in order."""
        return [self._stages[name] for name in self._enabled if name in self._stages]

    def list_all(self) -> List[str]:
        """List all registered stage names."""
        return list(self._stages.keys())


def auto_discover() -> List[BaseStage]:
    """
    Auto-discover plugins via Python entry points.

    Returns:
        List of discovered BaseStage implementations.
    """
    discovered: List[BaseStage] = []

    try:
        from importlib.metadata import entry_points
        from typing import Any

        eps = entry_points()
        if hasattr(eps, "get"):
            slimzero_eps: Any = eps.get("slimzero.stages", [])
        else:
            slimzero_eps = [ep for ep in eps if getattr(ep, "group", "") == "slimzero.stages"]

        for ep in slimzero_eps:
            try:
                stage = ep.load()
                if isinstance(stage, BaseStage):
                    discovered.append(stage)
            except Exception:
                continue

    except ImportError:
        pass

    return discovered
