# Architecture

## Pipeline Overview

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────────┐
│  Pipeline Stages                            │
├─────────────────────────────────────────────┤
│  1. Intent Extractor                        │
│  2. Prompt Rewriter                         │
│  3. Semantic Guard                          │
│  4. Few-Shot Ranker                         │
│  5. History Compressor                      │
│  6. Response Format Injector                 │
│  7. Hallucination Risk Scorer                │
│  8. Token Budget Enforcer                   │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────┐
│   LLM API   │
└─────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  Post-Processing                            │
├─────────────────────────────────────────────┤
│  9. Response Validator                      │
│  10. Hallucination Flagger                  │
│  11. Savings Logger                         │
└─────────────────────────────────────────────┘
    │
    ▼
  Response
```

## Components

### Stages

Processing stages that transform prompts. Each stage:
- Takes `StageInput`
- Returns `StageOutput`
- Can modify prompt with `modified=True`

### Post-Processing

Response analysis and validation:
- Response validation against intent
- Hallucination detection
- Statistics logging

### Agent

- **GSD**: Task decomposition graph
- **Ralph**: Autonomous loop with fault prevention

### Plugins

Custom stages via `BaseStage` interface.
