# Installation

## Basic Installation

```bash
pip install slimzero
```

## With All Dependencies

```bash
pip install slimzero[all]
```

## Optional Extras

```bash
# Agent support (networkx)
pip install slimzero[agent]

# Dashboard support (rich)
pip install slimzero[dashboard]

# Development dependencies
pip install slimzero[dev]
```

## Dependencies

SlimZero requires Python 3.10+ and uses these optional dependencies:

- `spacy` - Intent extraction
- `sentence-transformers` - Semantic similarity
- `tiktoken` - Token counting
- `transformers` - Text rewriting
- `networkx` - Task graphs
- `rich` - Dashboard

## Verifying Installation

```python
from slimzero import SlimZero
sz = SlimZero()
result = sz.call("Hello world")
print(result.response)
```
