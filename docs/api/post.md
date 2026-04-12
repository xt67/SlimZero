# Post-Processing

Post-processing stages validate and analyze LLM responses.

## ResponseValidator

Validates that responses address the parsed intent.

```python
from slimzero.post.validator import ResponseValidator

validator = ResponseValidator(threshold=0.60)
is_valid, similarity = validator.validate(intent, response)
```

## HallucinationFlagger

Detects potential hallucinations in responses.

```python
from slimzero.post.flagger import HallucinationFlagger

flagger = HallucinationFlagger()
result = flagger.flag(response)
# {'has_flags': True, 'total_flags': 3, 'categories': {...}}
```

## SavingsLogger

Tracks token savings statistics.

```python
from slimzero.post.logger import SavingsLogger

logger = SavingsLogger(cost_per_1k_tokens=0.002)
logger.log_call(
    original_input_tokens=100,
    sent_input_tokens=80,
    semantic_similarity=0.95,
)

stats = logger.get_cumulative_stats()
```

## Exporting

```python
# JSON export
json_data = logger.export_json()
logger.export_json("session.json")

# Markdown export
md_data = logger.export_markdown()
logger.export_markdown("session.md")
```
