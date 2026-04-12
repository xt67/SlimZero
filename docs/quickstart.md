# Quick Start

## Three-Line Integration

```python
from slimzero import SlimZero

sz = SlimZero(model="gpt-4o")
result = sz.call(prompt="Explain Python decorators please")
print(result.response)
```

## With API Client

```python
from openai import OpenAI
from slimzero import SlimZero

client = OpenAI()
sz = SlimZero(model="gpt-4o", api_client=client)

result = sz.call(
    prompt="Please could you help me understand async/await in Python?",
    system_prompt="You are a helpful coding assistant."
)
print(result.response)
```

## Configuration Options

```python
sz = SlimZero(
    model="gpt-4o",
    token_budget=512,        # Max tokens
    sim_threshold=0.92,      # Semantic similarity threshold
    few_shot_k=3,           # Few-shot examples to keep
    history_window=4,        # Conversation history turns
    hallucination_guard=True,
    response_validation=True,
)
```

## Getting Statistics

```python
stats = sz.get_stats()
print(f"Total calls: {stats['total_calls']}")
print(f"Tokens saved: {stats['cumulative_tokens_saved']}")

# Export to JSON
json_data = sz.export_stats_json()

# Export to Markdown
md_data = sz.export_stats_markdown()
```
