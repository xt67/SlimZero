# SlimZero

**Zero-overhead prompt compression for LLM APIs**

SlimZero optimizes LLM API calls by compressing prompts before sending while ensuring semantic equivalence and minimal response padding.

## Features

- **Prompt Compression**: Strip filler, convert hedged to imperative, reduce token overhead
- **Semantic Guard**: Cosine similarity validation to prevent meaning drift
- **Hallucination Prevention**: Risk scoring and uncertainty instruction injection
- **Token Budget Enforcement**: Hard ceiling with priority-based trimming
- **Response Minimization**: Format injection for minimal outputs
- **Agent Orchestration**: GSD task graphs and Ralph agent loop

## Quick Start

```python
from slimzero import SlimZero

sz = SlimZero(model="gpt-4o")
result = sz.call(prompt="Please could you explain how Python decorators work?")
print(result.response)
print(f"Tokens saved: {result.input_token_savings_percent:.1f}%")
```

## CLI Usage

```bash
pip install slimzero
slimzero "Explain machine learning"
```

## See Also

- [Installation](installation.md)
- [Quick Start](quickstart.md)
- [API Reference](api/core.md)
