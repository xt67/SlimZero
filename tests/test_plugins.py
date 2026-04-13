"""
Tests for Plugin API (US-017)
"""

import pytest

from slimzero.plugins import BaseStage, PluginRegistry, auto_discover
from slimzero.schemas import StageInput, StageOutput, IntentSchema


class TestPluginStage(BaseStage):
    """Test implementation of BaseStage."""

    @property
    def name(self) -> str:
        return "test_stage"

    @property
    def description(self) -> str:
        return "A test stage"

    def process(self, inp: StageInput) -> StageOutput:
        return StageOutput(prompt=inp.prompt, modified=False)


class TestBaseStage:
    """Tests for BaseStage."""

    def test_stage_has_name(self):
        """Test stage has name property."""
        stage = TestPluginStage()
        assert stage.name == "test_stage"

    def test_stage_has_description(self):
        """Test stage has description property."""
        stage = TestPluginStage()
        assert stage.description == "A test stage"

    def test_stage_process_returns_output(self):
        """Test stage process returns StageOutput."""
        stage = TestPluginStage()
        intent = IntentSchema(core_task="test")
        inp = StageInput(prompt="test", intent=intent, token_count=1)
        out = stage.process(inp)
        assert isinstance(out, StageOutput)

    def test_stage_validate_returns_true(self):
        """Test stage validate returns True by default."""
        stage = TestPluginStage()
        is_valid, error = stage.validate()
        assert is_valid is True
        assert error is None

    def test_stage_on_error(self):
        """Test stage on_error returns StageOutput."""
        stage = TestPluginStage()
        out = stage.on_error(ValueError("test"))
        assert isinstance(out, StageOutput)
        assert "error" in out.notes


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def test_registry_empty(self):
        """Test empty registry."""
        registry = PluginRegistry()
        assert len(registry.list_all()) == 0

    def test_register(self):
        """Test registering a stage."""
        registry = PluginRegistry()
        stage = TestPluginStage()
        registry.register(stage)
        assert "test_stage" in registry.list_all()

    def test_get(self):
        """Test getting a registered stage."""
        registry = PluginRegistry()
        stage = TestPluginStage()
        registry.register(stage)
        retrieved = registry.get("test_stage")
        assert retrieved is stage

    def test_get_nonexistent(self):
        """Test getting nonexistent stage."""
        registry = PluginRegistry()
        assert registry.get("nonexistent") is None

    def test_unregister(self):
        """Test unregistering a stage."""
        registry = PluginRegistry()
        stage = TestPluginStage()
        registry.register(stage)
        registry.unregister("test_stage")
        assert "test_stage" not in registry.list_all()

    def test_enable(self):
        """Test enabling a stage."""
        registry = PluginRegistry()
        stage = TestPluginStage()
        registry.register(stage)
        registry.enable("test_stage")
        enabled = registry.get_enabled()
        assert len(enabled) == 1
        assert enabled[0].name == "test_stage"

    def test_disable(self):
        """Test disabling a stage."""
        registry = PluginRegistry()
        stage = TestPluginStage()
        registry.register(stage)
        registry.enable("test_stage")
        registry.disable("test_stage")
        assert len(registry.get_enabled()) == 0

    def test_get_enabled_empty(self):
        """Test getting enabled stages when none enabled."""
        registry = PluginRegistry()
        assert len(registry.get_enabled()) == 0

    def test_list_all(self):
        """Test listing all registered stages."""
        registry = PluginRegistry()

        class Stage1(BaseStage):
            @property
            def name(self):
                return "stage1"

            def process(self, inp):
                return StageOutput(prompt=inp.prompt)

        class Stage2(BaseStage):
            @property
            def name(self):
                return "stage2"

            def process(self, inp):
                return StageOutput(prompt=inp.prompt)

        registry.register(Stage1())
        registry.register(Stage2())
        assert len(registry.list_all()) == 2


class TestAutoDiscover:
    """Tests for auto_discover."""

    def test_auto_discover_returns_list(self):
        """Test auto_discover returns a list."""
        discovered = auto_discover()
        assert isinstance(discovered, list)
