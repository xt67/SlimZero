# Plugin API

Extend SlimZero with custom pipeline stages.

## BaseStage

```python
from slimzero.plugins import BaseStage
from slimzero.schemas import StageInput, StageOutput

class MyStage(BaseStage):
    @property
    def name(self) -> str:
        return "my_stage"

    @property
    def description(self) -> str:
        return "Custom processing stage"

    def process(self, inp: StageInput) -> StageOutput:
        # Process the input
        return StageOutput(
            prompt=inp.prompt.upper(),
            modified=True,
            notes="Converted to uppercase"
        )
```

## PluginRegistry

```python
from slimzero.plugins import PluginRegistry

registry = PluginRegistry()
registry.register(MyStage())
registry.enable("my_stage")
```

## Auto-Discovery

Plugins can be auto-discovered via entry points:

```toml
# pyproject.toml
[project.entry-points."slimzero.stages"]
my_stage = "mypackage.mystages:MyStage"
```

## Rules

- Plugins must not raise exceptions that halt the pipeline
- Plugins must not make external API calls
- Plugins that modify prompts must set `modified=True`
