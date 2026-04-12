# Configuration

## Token Budget

```python
sz = SlimZero(token_budget=512)  # Default: 512
```

## Semantic Similarity Threshold

```python
sz = SlimZero(sim_threshold=0.92)  # Default: 0.92
```

Higher values = stricter semantic equivalence requirements.

## Few-Shot Examples

```python
sz = SlimZero(few_shot_k=3)  # Keep top 3 examples
```

## History Window

```python
sz = SlimZero(history_window=4)  # Keep last 4 turns verbatim
```

## Hallucination Guard

```python
sz = SlimZero(hallucination_guard=True)  # Default: True
```

## Response Validation

```python
sz = SlimZero(response_validation=True)  # Default: True
```

## Agent Mode

```python
sz = SlimZero(
    agent_mode=True,
    max_agent_steps=20,
    drift_threshold=0.75,
)
```
