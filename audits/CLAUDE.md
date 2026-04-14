# CLAUDE.md — SlimZero Agent Instructions

> **For:** OpenCode / any AI coding agent working on this repository  
> **Repository:** https://github.com/xt67/SlimZero  
> **Current version:** 0.1.2 (as of April 2026)  
> **Audit status:** Two bugs confirmed live by running the code. Fix these before anything else.

---

## 0. Read this entire file before writing a single line of code

This file contains the exact current state of the codebase, confirmed bugs with line numbers, the correct fixes, and the rules for every file you touch. Do not infer, guess, or hallucinate — everything you need is here.

---

## 1. Project overview in one paragraph

SlimZero is a Python middleware library (`pip install slimzero`) that sits between any app and any LLM API. It runs 8 local pipeline stages before the API call (intent extraction, prompt rewriting, semantic guard, few-shot ranking, history compression, format injection, hallucination scoring, token budget enforcement), calls the API exactly once, then runs 3 local post-processing stages (response validation, hallucination flagging, savings logging). All pipeline work costs zero API tokens. It also includes an autonomous agent loop (Ralph + GSD task graph) with circuit breakers, semantic drift detection, and checkpointing.

---

## 2. Confirmed live bugs — fix these first, in this order

These were verified by running the code directly. Each bug has the exact file, line, and the correct fix.

---

### BUG 1 — Critical: `semantic_guard` stage never appears in `stages_applied`

**File:** `slimzero/core.py`  
**Lines:** ~278–286

**What is wrong:** The semantic guard runs and works correctly, but `stages_applied.append("semantic_guard")` is never called. Every other stage is tracked. Users looking at `result.stages_applied` cannot see whether the guard ran or rejected a rewrite.

**Current code (broken):**
```python
guard_out = self._semantic_guard.process(inp)
semantic_similarity = guard_out.metadata.get("similarity", 1.0)
validated_prompt = guard_out.prompt
inp.prompt = validated_prompt
# ← no stages_applied.append here
```

**Correct fix — add one line after the guard runs:**
```python
guard_out = self._semantic_guard.process(inp)
semantic_similarity = guard_out.metadata.get("similarity", 1.0)
validated_prompt = guard_out.prompt
inp.prompt = validated_prompt
stages_applied.append("semantic_guard")  # ADD THIS LINE
```

---

### BUG 2 — High: `RalphLoop._call_llm` ignores `self.model`, uses hardcoded fallback `"gpt-4o"`

**File:** `slimzero/agent/ralph.py`  
**Lines:** ~502–540

**What is wrong:** `core.py` correctly passes `model=self.model` to `RalphLoop.__init__` (confirmed at line 115). `RalphLoop.__init__` correctly stores it as `self.model` (confirmed at line 162). But `_call_llm` inside RalphLoop hardcodes `"gpt-4o"` for the OpenAI/default branches. So `SlimZero(model="gpt-4o-mini", agent_mode=True).run_goal(...)` sends every agent planning call to `gpt-4o`, not `gpt-4o-mini`.

**Current broken code:**
```python
elif client_module in ("openai", "opencode", "ollama") or "openai" in client_module:
    response = self.api_client.chat.completions.create(
        model="gpt-4o",  # ← hardcoded, wrong
        messages=[{"role": "user", "content": prompt}],
    )

else:
    response = self.api_client.chat.completions.create(
        model="gpt-4o",  # ← hardcoded, wrong
        messages=[{"role": "user", "content": prompt}],
    )
```

**Correct fix — replace `"gpt-4o"` with `self.model` in both places:**
```python
elif client_module in ("openai", "opencode", "ollama") or "openai" in client_module:
    response = self.api_client.chat.completions.create(
        model=self.model,  # ← use self.model
        messages=[{"role": "user", "content": prompt}],
    )

else:
    response = self.api_client.chat.completions.create(
        model=self.model,  # ← use self.model
        messages=[{"role": "user", "content": prompt}],
    )
```

---

### BUG 3 — Medium: `RalphLoop._estimate_tokens` uses word-split, not the shared `count_tokens`

**File:** `slimzero/agent/ralph.py`  
**Line:** ~544–546

**What is wrong:** The `utils/tokenizer.py` module was added specifically to centralise accurate token counting. Every other file in the codebase now uses it. But `ralph.py` still has its own private `_estimate_tokens` that does `len(text.split())`.

**Current broken code:**
```python
def _estimate_tokens(self, text: str) -> int:
    """Estimate token count."""
    return len(text.split())
```

**Correct fix:**
```python
def _estimate_tokens(self, text: str) -> int:
    """Count tokens using shared counter."""
    from slimzero.utils import count_tokens
    return count_tokens(text)
```

---

### BUG 4 — Low: Test `test_run_circuit_breaker` assertion is wrong

**File:** `tests/test_ralph.py`  
**Lines:** ~148–152

**What is wrong:** The test creates `RalphLoop(max_steps=1)` and asserts `result["result"] == "circuit_breaker"`. But verified by running the actual code: with `max_steps=1`, the loop runs 1 step (step_count becomes 1), the step returns `done=True` (because no api_client), so the loop exits the while loop and hits `return {"result": "max_steps_reached", ...}`. The circuit breaker only fires when `step_count >= max_steps` at the START of iteration — by the time `max_steps=1` is checked, one step already ran and returned done. The result is `"max_steps_reached"`, not `"circuit_breaker"`.

**Current broken test:**
```python
def test_run_circuit_breaker(self):
    loop = RalphLoop(max_steps=1)
    result = loop.run("Test goal")
    assert result["result"] == "circuit_breaker"  # ← WRONG
```

**Correct fix — use max_steps=0 or check the actual circuit breaker path:**
```python
def test_run_circuit_breaker(self):
    """Test circuit breaker raises when step count exceeds limit."""
    loop = RalphLoop(max_steps=5)
    loop._step_count = 5  # Manually set to trigger circuit breaker
    with pytest.raises(SlimZeroCircuitBreaker):
        loop._check_circuit_breaker()

def test_run_returns_max_steps_result(self):
    """Test run returns max_steps_reached when loop exhausts steps."""
    loop = RalphLoop(max_steps=1)
    result = loop.run("Test goal")
    assert result["result"] == "max_steps_reached"
```

---

## 3. Architecture — do not change this

The architecture is correct and must not be altered. Every component exists for a specific reason.

```
slimzero/
├── core.py                  # SlimZero class — pipeline runner and LLM router
├── schemas.py               # Frozen dataclasses: IntentSchema, StageInput, StageOutput, SlimZeroResult, AgentResult, SavingsStats
├── exceptions.py            # Full exception hierarchy — all inherit SlimZeroError
├── __init__.py              # Public API — exports SlimZero, schemas, exceptions
├── __main__.py              # CLI entrypoint
├── stages/                  # 8 pre-processing pipeline stages
│   ├── intent.py            # Stage 1: spaCy NLP → IntentSchema
│   ├── rewriter.py          # Stage 2: T5-small / Ollama / rule-based compression
│   ├── semantic_guard.py    # Stage 3: MiniLM cosine similarity — NON-BYPASSABLE
│   ├── few_shot.py          # Stage 4: rank few-shot examples by relevance
│   ├── history.py           # Stage 5: compress old turns to summary
│   ├── injector.py          # Stage 6: append minimal-response fragment
│   ├── hallucination.py     # Stage 7: classify risk, inject uncertainty instruction
│   └── budget.py            # Stage 8: tiktoken hard cap, trim by priority
├── post/                    # 3 post-processing stages (run after API call)
│   ├── validator.py         # Check response addresses intent (cosine sim)
│   ├── flagger.py           # 80-pattern hallucination heuristic scan
│   └── logger.py            # Per-call stats, cumulative dashboard, JSON/MD export
├── agent/
│   ├── ralph.py             # Observe-plan-act-reflect loop + circuit breakers
│   └── gsd.py               # networkx task graph + checkpoint/resume
├── utils/
│   ├── tokenizer.py         # Shared TokenCounter singleton (tiktoken)
│   └── embedding.py         # Shared SharedEmbeddingModel singleton (MiniLM)
├── plugins/                 # BaseStage ABC + PluginRegistry + auto_discover()
└── dashboard/               # Rich live terminal dashboard
```

### The one inviolable rule

The semantic guard in `stages/semantic_guard.py` **cannot be disabled**. Its minimum threshold is 0.80 (enforced in `__init__` with a `ValueError`). Do not add any parameter or code path that allows bypassing it. This is the central safety guarantee of the library.

---

## 4. Coding rules — follow these exactly

### 4.1 Token counting — always use the shared utility

**Never write `len(text.split())`** anywhere in the codebase. Always import and use the shared counter:

```python
from slimzero.utils import count_tokens
n = count_tokens(text)
```

The `TokenCounter` in `utils/tokenizer.py` is a Singleton keyed by encoding name. It loads tiktoken once and reuses it. Word-split is only used as an internal fallback inside `TokenCounter` itself when tiktoken is unavailable.

### 4.2 Embeddings — always use the shared model

**Never instantiate `SentenceTransformer` directly** anywhere outside `utils/embedding.py`. Always use:

```python
from slimzero.utils import get_embedding_model
model = get_embedding_model()  # returns SharedEmbeddingModel singleton
sim = model.similarity(text1, text2)
embeddings = model.encode([text1, text2])
```

`SharedEmbeddingModel` is a Singleton. Loading MiniLM twice wastes 80MB RAM and 2–3 seconds of startup. Three stages use embeddings (semantic_guard, few_shot, validator) — they must all share one instance.

### 4.3 API routing — follow the existing pattern in `core.py`

The `_call_llm` method in `core.py` is the canonical pattern for multi-SDK routing. Always detect client type via `type(self.api_client).__module__.split('.')[0]` and route to the right SDK call. The same pattern is now (partially) in `ralph.py` — keep them consistent.

```python
client_module = type(self.api_client).__module__.split('.')[0]

if client_module == "anthropic":
    # anthropic.messages.create(model=self.model, max_tokens=..., system=..., messages=[...])
elif client_module in ("openai", "opencode", "ollama") or "openai" in client_module:
    # client.chat.completions.create(model=self.model, messages=[...])
elif client_class == "ollama":
    # urllib raw call to localhost:11434
else:
    # default to OpenAI spec
```

**Always use `self.model`** — never hardcode a model name.

### 4.4 Exception rules

- All exceptions must inherit from `SlimZeroError` in `exceptions.py`
- Log the error with `logger.error(...)` or `logger.warning(...)` **before** raising
- Never raise a bare `Exception` — use the typed hierarchy
- `SlimZeroSemanticRejection` is not an error — log it at `INFO` level, do not surface it to the user
- Never suppress the LLM response — flags are metadata, the response always reaches the caller

### 4.5 Pipeline stage rules

Every stage class must follow this contract:

```python
class MyStage:
    def process(self, inp: StageInput) -> StageOutput:
        try:
            # ... stage logic ...
            return StageOutput(prompt=result, modified=True, notes="...", metadata={...})
        except Exception as e:
            logger.warning(f"MyStage failed: {e}. Passing through unchanged.")
            return StageOutput(prompt=inp.prompt, modified=False, notes=f"error: {e}")
```

- A stage **must never raise an exception** that reaches `core.py` — catch internally
- A stage **must never make an API call** — local inference only
- If a stage modifies the prompt, set `modified=True`
- Put all diagnostic data in `metadata` dict — this is what the tests and dashboard read

### 4.6 Schema rules

- `IntentSchema` is a **frozen dataclass** — do not add mutable fields
- `StageInput` and `StageOutput` are mutable — `inp.prompt = new_prompt` is valid in `core.py`
- `SlimZeroResult` properties (`input_token_savings`, `input_token_savings_percent`) are computed — do not store them
- All dataclasses must implement `to_dict()` returning a JSON-serialisable dict

### 4.7 Dependency rules

**Base dependencies** (always installed, `pip install slimzero`):
- `spacy>=3.7` — intent extraction
- `sentence-transformers>=2.7` — semantic guard, few-shot ranking, response validation
- `tiktoken>=0.7` — token counting

**Optional dependencies:**
- `transformers>=4.40` — T5-small rewriter (extras: `[transformers]`)
- `networkx>=3.3` — GSD task graph (extras: `[agent]`)
- `rich>=13.7` — live dashboard (extras: `[dashboard]`)

**Never add a new base dependency without updating `pyproject.toml` `dependencies` list.**  
**Never import a base dependency without a try/except fallback** — the library must degrade gracefully when packages are unavailable (e.g., spaCy model not downloaded).

---

## 5. Test rules — all tests must pass

Tests are in `tests/`. Run with: `pytest tests/ -v --tb=short`

### 5.1 What each test file covers

| File | Tests |
|------|-------|
| `test_slimzero.py` | Core class init, call(), mock mode, stats export |
| `test_semantic_guard.py` | Threshold enforcement, validation, process(), fallback |
| `test_ralph.py` | ToolValidator, ActionAuditor, RalphLoop circuit breakers |
| `test_plugins.py` | BaseStage ABC, PluginRegistry |
| `test_validator.py` | ResponseValidator similarity, off-task flagging |
| `test_hallucination.py` | HallucinationRiskScorer risk tiers, empty input |
| `test_flagger.py` | HallucinationFlagger pattern matches |
| `test_budget.py` | TokenBudgetEnforcer trimming, within-budget pass-through |
| `test_intent.py` | IntentExtractor fallback path, format detection |
| `test_few_shot.py` | FewShotRanker example detection, ranking |
| `test_history.py` | HistoryCompressor window, compression |
| `test_injector.py` | ResponseFormatInjector fragment selection, skip logic |
| `test_logger.py` | SavingsLogger call logging, stats, export |
| `test_gsd.py` | GSDTaskGraph decompose, checkpoint, resume |

### 5.2 Test correctness rules

Every test must verify **real behaviour**, not just method existence. These patterns are wrong:

```python
# WRONG — only tests that the method exists
def test_has_call(self):
    sz = SlimZero()
    assert hasattr(sz, "call")

# RIGHT — tests actual behaviour
def test_call_compresses_filler_prompt(self):
    sz = SlimZero(model="mock")
    result = sz.call("Could you please maybe explain Python decorators?")
    assert result.sent_input_tokens <= result.original_input_tokens
    assert isinstance(result, SlimZeroResult)
```

### 5.3 The `model="mock"` test pattern

Use `SlimZero(model="mock")` for all pipeline tests that do not need a real LLM response. This is a supported mode — it returns `[Mock response for: ...]`. Never make real API calls in tests.

```python
sz = SlimZero(model="mock")
result = sz.call("Explain gradient descent")
assert result.response.startswith("[Mock response")
```

### 5.4 Tests that must not be broken

These test assertions are correct and must continue to pass:

```python
# semantic guard minimum threshold is 0.80
assert MIN_THRESHOLD == 0.80

# semantic guard rejects threshold below minimum
with pytest.raises(ValueError):
    SemanticGuard(threshold=0.5)

# empty prompt raises SlimZeroInputError
with pytest.raises(SlimZeroInputError):
    sz.call("")

# empty string in hallucination scorer → LOW risk
tier, high, medium = scorer.score("")
assert tier == HallucinationRiskTier.LOW
```

### 5.5 The circuit breaker test — fixed version (see Bug 4 above)

The existing `test_run_circuit_breaker` in `test_ralph.py` has a wrong assertion. Replace it with:

```python
def test_circuit_breaker_raises_on_step_limit(self):
    """Circuit breaker raises when manually triggered."""
    loop = RalphLoop(max_steps=5)
    loop._step_count = 5
    with pytest.raises(SlimZeroCircuitBreaker):
        loop._check_circuit_breaker()

def test_run_returns_max_steps_when_exhausted(self):
    """Run returns max_steps_reached when loop exhausts all steps."""
    loop = RalphLoop(max_steps=1)
    result = loop.run("Test goal")
    assert result["result"] == "max_steps_reached"
    assert result["steps"] == 1
```

---

## 6. File-by-file rules — what you can and cannot change

### `slimzero/core.py`
- ✅ Fix: add `stages_applied.append("semantic_guard")` after line 284
- ✅ Add: `check_dependencies()` method that returns dict of which stages are in fallback mode
- ❌ Do not: change `DEFAULT_TOKEN_BUDGET = 4096`
- ❌ Do not: change the pipeline stage order (1-8 are fixed)
- ❌ Do not: add any code path that bypasses the semantic guard

### `slimzero/agent/ralph.py`
- ✅ Fix: replace `model="gpt-4o"` with `model=self.model` in `_call_llm` (2 occurrences)
- ✅ Fix: replace `_estimate_tokens` body with `from slimzero.utils import count_tokens; return count_tokens(text)`
- ✅ The `_execute_step` implementation is correct — do not simplify it back to a stub
- ✅ The `_checkpoint_state()` call in the `SlimZeroDriftHalt` handler is correct — do not remove it
- ❌ Do not: change the circuit breaker logic or drift threshold defaults

### `slimzero/utils/embedding.py`
- ✅ The `SharedEmbeddingModel` Singleton is correct — do not add a second model loader anywhere
- ⚠️ Known: `similarity()` uses a Python `zip` loop for dot product — numpy would be faster, but do not change this yet (it would add numpy as a dependency)

### `slimzero/schemas.py`
- ✅ `SavingsStats` now has `model` field and `estimated_cost_savings` uses `model_pricing` — correct
- ❌ Do not: add mutable fields to `IntentSchema` (it is frozen)
- ❌ Do not: remove `to_dict()` from any schema class

### `slimzero/stages/semantic_guard.py`
- ❌ Do not: add any parameter that allows disabling the guard
- ❌ Do not: lower `MIN_THRESHOLD` below `0.80`
- ❌ Do not: change the `ValueError` that fires when threshold < MIN_THRESHOLD

### `pyproject.toml`
- ✅ `spacy`, `sentence-transformers`, `tiktoken` are in base `dependencies` — correct
- ❌ Do not: move them back to `optional-dependencies`
- ✅ When bumping version: update both `version = "..."` in `pyproject.toml` AND `__version__ = "..."` in `slimzero/__init__.py` — they must always match

### `tests/test_ralph.py`
- ✅ Fix: replace `test_run_circuit_breaker` with the two correct tests described in Bug 4 above

---

## 7. What NOT to add or change

- ❌ Do not add `numpy` as a dependency — the manual dot product loop is intentional
- ❌ Do not add any LLM call inside a pipeline stage — stages are local-only
- ❌ Do not change `DEFAULT_THRESHOLD = 0.92` in `semantic_guard.py`
- ❌ Do not merge `utils/embedding.py` and `utils/tokenizer.py` into one file — they have separate concerns
- ❌ Do not add async support without first adding it to `core.py`'s `call()` method signature
- ❌ Do not add any stage that calls the target LLM as part of compression — that is the one design rule that makes SlimZero different from every competing tool
- ❌ Do not remove the `model="mock"` support path — it is used by all tests
- ❌ Do not change `pyproject.toml`'s `[project.entry-points."slimzero.stages"]` — this is how community plugins are discovered
- ❌ Do not commit `activate-venv.bat`, `prd.json`, or `scripts/ralph/CLAUDE.md` (internal notes) — add them to `.gitignore` if not already there

---

## 8. How to verify your changes are correct

After making any change, run these checks in order:

```bash
# 1. Syntax and import check
python -c "import slimzero; print('import ok')"

# 2. End-to-end pipeline check
python -c "
from slimzero import SlimZero
sz = SlimZero(model='mock')
result = sz.call('Could you please maybe explain gradient descent in really simple terms?')
print('stages_applied:', result.stages_applied)
print('semantic_guard in stages:', 'semantic_guard' in result.stages_applied)
assert 'semantic_guard' in result.stages_applied, 'FAIL: semantic_guard missing from stages'
print('original_tokens:', result.original_input_tokens)
print('sent_tokens:', result.sent_input_tokens)
print('PASS')
"

# 3. Model routing check for agent
python -c "
from slimzero.agent.ralph import RalphLoop
r = RalphLoop(model='claude-opus-4-6')
assert r.model == 'claude-opus-4-6', 'FAIL: model not stored'
# Verify _call_llm would use self.model (check via source inspection)
import inspect
src = inspect.getsource(r._call_llm)
assert 'self.model' in src, 'FAIL: _call_llm still hardcodes model name'
assert 'gpt-4o\"' not in src, 'FAIL: gpt-4o still hardcoded'
print('PASS: model routing correct')
"

# 4. Semantic guard threshold enforcement
python -c "
from slimzero.stages.semantic_guard import SemanticGuard, MIN_THRESHOLD
assert MIN_THRESHOLD == 0.80
try:
    SemanticGuard(threshold=0.5)
    print('FAIL: should have raised ValueError')
except ValueError:
    print('PASS: threshold enforcement works')
"

# 5. Hallucination scorer empty string
python -c "
from slimzero.stages.hallucination import HallucinationRiskScorer
from slimzero.schemas import HallucinationRiskTier
h = HallucinationRiskScorer()
tier, a, b = h.score('')
assert tier == HallucinationRiskTier.LOW, f'FAIL: got {tier}'
print('PASS: empty string → LOW risk')
"

# 6. Run full test suite
pytest tests/ -v --tb=short
```

All 6 checks must pass before committing.

---

## 9. Common mistakes to avoid

| Mistake | Why it's wrong | Correct approach |
|---------|---------------|-----------------|
| `len(text.split())` for token counting | Gives ~75% of real count, breaks budget enforcement | `from slimzero.utils import count_tokens; count_tokens(text)` |
| `SentenceTransformer("all-MiniLM-L6-v2")` directly | Loads 80MB model again, wastes RAM | `from slimzero.utils import get_embedding_model; get_embedding_model()` |
| Hardcoding `"gpt-4o"` or `"claude-sonnet-4-6"` in any method | Ignores user's model choice | Use `self.model` |
| `return {"done": True}` in `_execute_step` | Stubs out the agent — it does nothing | Keep the full observe-plan-act-reflect implementation |
| Adding `try/except` that swallows exceptions silently | Hides bugs | Log with `logger.warning(...)` then return a safe fallback `StageOutput` |
| Writing `stages_applied.append("semantic_guard")` in the wrong place | Tracks it even when guard was skipped | Append only after `guard_out = self._semantic_guard.process(inp)` succeeds |
| Changing `dependencies = []` back to empty | Library does nothing on bare install | `spacy`, `sentence-transformers`, `tiktoken` must stay in base dependencies |
| Lowering `MIN_THRESHOLD` | Breaks the one inviolable safety rule | Do not touch it |
| Forgetting to bump `__init__.py` when bumping `pyproject.toml` version | Creates version mismatch that confuses users | Always update both |

---

## 10. Commit message format

Use conventional commits:

```
fix: <what was broken and what you did>        # bug fixes
feat: <what new capability was added>           # new features  
perf: <what performance was improved>           # optimisations
test: <what tests were added or fixed>          # test changes
chore: <version bump, gitignore, cleanup>       # maintenance
docs: <readme, docstring, comment changes>      # docs only
refactor: <restructuring without behaviour change>
```

Examples:
```
fix: add semantic_guard to stages_applied in core.py pipeline
fix: use self.model in ralph._call_llm instead of hardcoded gpt-4o
test: fix test_run_circuit_breaker assertion to match actual behaviour
fix: use count_tokens in ralph._estimate_tokens
```

---

## 11. Current known limitations (do not try to fix these now)

These are documented limitations, not bugs. Do not attempt to fix them in the current sprint:

1. **T5-small rewriter produces poor output** — T5-small is not fine-tuned for prompt compression. The rule-based path actually produces more reliable results. This is a research problem, not a code bug.
2. **Cosine similarity uses Python loop** — `utils/embedding.py similarity()` uses `zip()` loop instead of numpy. This is ~100× slower than numpy for long embeddings. Acceptable for now because adding numpy as a dependency would increase install size.
3. **No streaming support** — `call()` is synchronous and returns the full response. Streaming would require significant API changes.
4. **No multimodal support** — images and binary content are not handled by any stage.
5. **SharedEmbeddingModel breaks if model name changes mid-session** — The Singleton logic checks `model_name != cls._model_name` in `__new__` but the comparison may not trigger correctly for all edge cases. Good enough for now.

---

## 12. Summary of what needs to be done right now

Do these tasks in this exact order:

1. **Fix Bug 1** — add `stages_applied.append("semantic_guard")` in `core.py` (5 minutes)
2. **Fix Bug 2** — replace `"gpt-4o"` with `self.model` in `ralph._call_llm` (5 minutes)
3. **Fix Bug 3** — replace ralph's `_estimate_tokens` body with `count_tokens` call (5 minutes)
4. **Fix Bug 4** — fix `test_run_circuit_breaker` assertion in `tests/test_ralph.py` (10 minutes)
5. **Run all 6 verification checks** from Section 8 — confirm everything passes
6. **Run `pytest tests/ -v`** — confirm all tests pass
7. **Commit** with message: `fix: semantic_guard tracking, model naming, token counting, test assertion`
8. **Bump version** to `0.1.3` in both `pyproject.toml` and `slimzero/__init__.py`
9. **Commit** with message: `chore: bump version to 0.1.3`

Total estimated time: 30–45 minutes.
