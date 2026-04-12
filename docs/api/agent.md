# Agent Components

## GSDTaskGraph

Task decomposition with networkx DiGraph.

```python
from slimzero.agent.gsd import GSDTaskGraph, GSDTask, TaskStatus

graph = GSDTaskGraph(goal="Build a web app")
graph.decompose('[{"task_id": "t1", "description": "Design DB"}]')

ready = graph.get_ready_tasks()
graph.update_task_status("t1", TaskStatus.COMPLETED, output="schema")
```

## RalphLoop

Autonomous agent loop with fault prevention.

```python
from slimzero.agent.ralph import RalphLoop

loop = RalphLoop(
    max_steps=20,
    drift_threshold=0.75,
)

result = loop.run(
    goal="Fix the login bug",
    tools=[{"name": "search", "parameters": {...}}]
)
```

### Features

- **Circuit Breaker**: Max steps/tokens limits
- **Semantic Drift Detection**: Compares plan to goal embeddings
- **Tool Validation**: Checks arguments before execution
- **Action Audit**: Logs all tool calls

### Circuit Breaker

```python
loop = RalphLoop(
    max_steps=20,
    max_retries_per_step=3,
    max_total_tokens=100000,
)
```

### Drift Detection

```python
loop = RalphLoop(drift_threshold=0.75)  # similarity threshold
```
