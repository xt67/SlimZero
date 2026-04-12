# SlimZero

**Zero-overhead prompt compression, response minimisation, hallucination guarding, and autonomous agent orchestration.**

[![PyPI Version](https://img.shields.io/pypi/v/slimzero.svg)](https://pypi.org/project/slimzero/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

SlimZero is a model-agnostic Python middleware library that sits between any application and any LLM API. It performs four jobs - **none of which cost a single API token**:

- **Prompt Compression** - Automatically rewrites user prompts to be shorter and clearer (40-70% input token reduction)
- **Response Minimisation** - Pre-conditions the LLM to answer concisely (30-50% output token reduction)
- **Hallucination Guarding** - Detects hallucination-prone queries and validates responses locally
- **Agent Orchestration** - Integrated Ralph loop with GSD task decomposition and circuit breakers

## Installation

```bash
pip install slimzero

# With agent support (Ralph loop, GSD task graph)
pip install slimzero[agent]

# With dashboard
pip install slimzero[dashboard]

# Everything
pip install slimzero[all]
```

## Quick Start

```python
from slimzero import SlimZero

# Three lines to add SlimZero to any project
sz = SlimZero(model="claude-sonnet-4-6")
result = sz.call(prompt="Explain gradient descent in detail please.")
print(result.response)
```

## Key Features

### Zero API Token Cost
All compression, classification, and validation logic runs locally using lightweight models:
- **spaCy** for intent extraction
- **T5-small** for prompt rewriting
- **sentence-transformers** for semantic similarity
- **tiktoken** for token counting

### Semantic Safety
Every compression is validated by a semantic similarity gate. Rewrites must preserve meaning before reaching the LLM:
- Default threshold: 0.92
- Minimum threshold: 0.80 (non-bypassable)
- Rejected rewrites use the original prompt

### Hallucination Guarding
Local classification and validation - no extra API calls:
- **HIGH risk**: Specific dates, numbers, citations, current facts → uncertainty instruction injected
- **MEDIUM risk**: Named entities with verifiable attributes → verification instruction injected
- **LOW risk**: Creative, opinion, open-ended queries → no action

### Agent Mode
Autonomous task execution with fault prevention:
- **Circuit breakers**: Max steps, retries, and token budgets
- **Semantic drift detection**: Alerts when agent diverges from goal
- **Tool validation**: Rejects invalid tool calls before execution
- **Checkpointing**: Resume from any failed state

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER PROMPT                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: Intent Extractor (spaCy)                        │
│  - Extract core_task, entities, output_format, constraints  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 2: Prompt Rewriter (T5-small)                       │
│  - Strip filler, merge duplicates, convert to imperative     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Stage 3: Semantic Guard (MiniLM) ◄── NON-BYPASSABLE       │
│  - Reject if similarity < 0.92                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Stages 4-8: Few-Shot Ranker, History Compressor,          │
│               Response Format Injector, Hallucination Scorer │
│               Token Budget Enforcer                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM API CALL                             │
│                    (ONLY API CALL)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Post-Processing: Response Validator, Hallucination Flag,    │
│                   Savings Logger                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    OPTIMIZED RESPONSE                       │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

```python
from slimzero import SlimZero

sz = SlimZero(
    model="claude-sonnet-4-6",       # Target model
    api_client=my_client,            # Optional: wrap existing client
    token_budget=4096,               # Hard token ceiling
    sim_threshold=0.92,              # Semantic similarity gate
    few_shot_k=3,                    # Keep top-k few-shot examples
    history_window=4,                 # Recent turns to keep verbatim
    hallucination_guard=True,         # Enable hallucination scoring
    response_validation=True,         # Validate response intent
    agent_mode=False,                # Enable Ralph loop
    max_agent_steps=20,              # Circuit breaker: max steps
    drift_threshold=0.75,            # Semantic drift detection
    dashboard=True,                  # Show live savings
    log_file="slimzero.jsonl",      # Structured log output
)
```

## Agent Mode

```python
from slimzero import SlimZero

sz = SlimZero(model="claude-opus-4-6", agent_mode=True)

result = sz.run_goal(
    goal="Research the top 5 vector databases and write a comparison report.",
    tools=[search_tool, read_tool, write_tool]
)

print(result.response)
# Audit trail available in result.metadata['audit_trail']
```

## Supported Providers

- Anthropic (Claude)
- OpenAI (GPT-4, GPT-3.5)
- Google (Gemini)
- Ollama (local models)
- Any OpenAI-spec compatible API

## Benchmarks (Targets)

| Metric | Target |
|--------|--------|
| Input token reduction | 40-70% |
| Output token reduction | 30-50% |
| Meta-token cost | 0 |
| Semantic similarity (accepted rewrites) | > 0.94 |
| Rewrite rejection rate | < 8% |
| Local pipeline latency (CPU) | < 150ms |
| Local pipeline latency (GPU) | < 40ms |

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
