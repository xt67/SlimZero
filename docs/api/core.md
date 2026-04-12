# Core API

## SlimZero Class

```python
from slimzero import SlimZero

sz = SlimZero(
    model="gpt-4o",
    api_client=None,
    token_budget=512,
    sim_threshold=0.92,
    few_shot_k=3,
    history_window=4,
    hallucination_guard=True,
    response_validation=True,
    agent_mode=False,
    max_agent_steps=20,
    max_retries=3,
    drift_threshold=0.75,
    dashboard=False,
    log_file=None,
)
```

### Methods

#### `call()`

Process a prompt through the SlimZero pipeline.

```python
result = sz.call(
    prompt="Your prompt here",
    system_prompt="Optional system prompt",
    history=None,           # List of conversation turns
    few_shot_examples=None,   # List of examples
)
```

Returns: `SlimZeroResult`

#### `get_stats()`

Get cumulative savings statistics.

```python
stats = sz.get_stats()
# {'total_calls': 10, 'cumulative_tokens_saved': 500, ...}
```

#### `export_stats_json()`

Export statistics as JSON string or file.

```python
json_str = sz.export_stats_json()
sz.export_stats_json("stats.json")
```

#### `export_stats_markdown()`

Export statistics as Markdown.

```python
md_str = sz.export_stats_markdown()
sz.export_stats_markdown("stats.md")
```

## SlimZeroResult

```python
@dataclass
class SlimZeroResult:
    response: str
    original_prompt: str
    sent_prompt: str
    original_input_tokens: int
    sent_input_tokens: int
    estimated_output_tokens: int
    stages_applied: List[str]
    semantic_similarity: Optional[float]
    hallucination_risk_tier: HallucinationRiskTier
    response_validated: bool
    flags_raised: List[str]
```

### Properties

- `input_token_savings`: `int` - Tokens saved
- `input_token_savings_percent`: `float` - Savings as percentage
