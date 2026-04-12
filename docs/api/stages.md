# Pipeline Stages

## Overview

The SlimZero pipeline consists of 8 processing stages:

1. **Intent Extractor** - Parse user intent
2. **Prompt Rewriter** - Compress to imperative form
3. **Semantic Guard** - Validate semantic equivalence
4. **Few-Shot Ranker** - Filter examples by relevance
5. **History Compressor** - Summarize conversation history
6. **Response Format Injector** - Add minimal response instructions
7. **Hallucination Risk Scorer** - Classify query risk level
8. **Token Budget Enforcer** - Apply hard token ceiling

## Stage Classes

### IntentExtractor

```python
from slimzero.stages.intent import IntentExtractor

extractor = IntentExtractor()
intent = extractor.extract("Write a Python function")
```

### PromptRewriter

```python
from slimzero.stages.rewriter import PromptRewriter

rewriter = PromptRewriter(model_name="t5-small")
rewritten = rewriter.rewrite(prompt, token_budget=512)
```

### SemanticGuard

```python
from slimzero.stages.semantic_guard import SemanticGuard

guard = SemanticGuard(threshold=0.92)
is_valid, similarity = guard.validate(original, rewritten)
```

### FewShotRanker

```python
from slimzero.stages.few_shot import FewShotRanker

ranker = FewShotRanker(k=3)
top_examples = ranker.rank(examples_text, query)
```

### HistoryCompressor

```python
from slimzero.stages.history import HistoryCompressor

compressor = HistoryCompressor(window=4)
recent, summary = compressor.compress(history, token_budget=512)
```

### ResponseFormatInjector

```python
from slimzero.stages.injector import ResponseFormatInjector
from slimzero.schemas import OutputFormat

injector = ResponseFormatInjector()
system = injector.inject(system_prompt, OutputFormat.CODE)
```

### HallucinationRiskScorer

```python
from slimzero.stages.hallucination import HallucinationRiskScorer

scorer = HallucinationRiskScorer()
tier, high, medium = scorer.score(query)
```

### TokenBudgetEnforcer

```python
from slimzero.stages.budget import TokenBudgetEnforcer

enforcer = TokenBudgetEnforcer(token_budget=512)
final, system, trimmed = enforcer.enforce(prompt, system_prompt=...)
```
