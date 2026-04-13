**SlimZero**

Cross-Check Audit Report --- v0.1.2

github.com/xt67/SlimZero · Commit b01c114 · April 2026

Comparing v0.1.1 (previous audit) → v0.1.2 (this audit)

*Verdict: Significant progress on all critical bugs. Two criticals
remain. Quality trajectory is strong.*

**1. Executive Summary**

This is the second audit of SlimZero, cross-checking the v0.1.2 release
against the 12 issues raised in the v0.1.1 audit. The repository was
cloned fresh and all changed files were read in full. The commit history
shows the author addressed the previous audit directly --- commit
acdd249 is titled \"fix: Address audit report critical and high severity
issues.\"

The result is strong forward progress. Nine of the twelve previously
reported issues are now fully or substantially fixed. Two critical
issues remain open, and one new issue was introduced by the update.

  -----------------------------------------------------------------------
  **Overall grade: B+ (up from B−) · Previous criticals: 3 open → 1
  remains · Previous highs: 4 open → 1 remains**

  -----------------------------------------------------------------------

  -----------------------------------------------------------------------------------------------------
  **Previous issue (v0.1.1)**           **Status in v0.1.2**                               **Severity
                                                                                           was**
  ------------------------------------- -------------------------------------------------- ------------
  \_call_llm hardcoded to OpenAI spec   FIXED --- Anthropic, OpenAI, Ollama, OpenCode all  Critical
  only                                  supported                                          

  \_execute_step was a stub (agent does FIXED --- full observe-plan-act-reflect loop       Critical
  nothing)                              implemented                                        

  Zero test coverage / no tests/        OPEN --- tests/ still does not exist. CI pipeline  Critical
  directory                             references it and will fail.                       

  GSD checkpoint used unstable hash()   FIXED --- now uses hashlib.sha256                  High
  for filename                                                                             

  Budget enforcer encodings list had    FIXED --- cleaned to                               High
  garbled Chinese string                \[\"cl100k_base\",\"o200k_base\",\"p50k_base\"\]   

  All dependencies were optional (bare  FIXED --- spacy, sentence-transformers, tiktoken   High
  install did nothing)                  now in base deps                                   

  DEFAULT_TOKEN_BUDGET was 512 (too     FIXED --- raised to 4096                           High
  small)                                                                                   

  Three separate MiniLM instances       FIXED --- SharedEmbeddingModel singleton in        Medium
  (\~240MB wasted RAM)                  utils/embedding.py                                 

  Version mismatch \_\_init\_\_.py vs   FIXED --- both now say 0.1.2                       Medium
  pyproject.toml                                                                           

  DriftHalt did not checkpoint before   FIXED --- \_checkpoint_state() called in DriftHalt Medium
  halting                               handler                                            

  Hallucination scorer returned MEDIUM  FIXED --- now returns LOW, 0, 0 for empty input    Low
  for empty string                                                                         

  SavingsStats.estimated_cost_savings   PARTIALLY FIXED --- uses model_pricing dict, but   Low
  ignored model_pricing dict            always falls back to \"default\" key regardless of 
                                        which model is in use. Cost accuracy still off.    
  -----------------------------------------------------------------------------------------------------

**2. Remaining Critical Issue**

**2.1 No test directory --- CI pipeline will fail on every publish**

**Files: tests/ (missing) · .github/workflows/publish.yml line 33**

The CI/CD workflow added in this update runs pytest tests/ before
publishing to PyPI. Since tests/ does not exist, every tag-triggered
publish will fail at the test step and the package will not be released.
The workflow also runs mypy slimzero/ --- this may pass, but the pytest
step blocks it.

This is now more urgent than in the previous audit because a live GitHub
Actions workflow depends on it. Anyone who forks the repo and tries to
publish will hit the same wall immediately.

  -----------------------------------------------------------------------
  **Risk: The GitHub Actions publish workflow (publish.yml) will fail at
  \"Run tests\" on every execution. pip install slimzero currently works
  because PyPI has the previously uploaded wheel --- but any new release
  is blocked until tests exist.**

  -----------------------------------------------------------------------

**What is needed --- minimum viable test suite**

1.  tests/\_\_init\_\_.py (empty)

2.  tests/test_semantic_guard.py --- verify threshold enforcement,
    fallback similarity, cannot go below 0.80

3.  tests/test_intent_extractor.py --- verify spaCy path and fallback
    path both return valid IntentSchema

4.  tests/test_hallucination_scorer.py --- verify empty string returns
    LOW, HIGH patterns trigger correctly

5.  tests/test_pipeline_e2e.py --- verify sz.call() with model=\"mock\"
    runs without error and returns SlimZeroResult

6.  tests/test_budget_enforcer.py --- verify tiktoken path and trim
    priority order

Estimated time: 3-4 hours. The existing code is testable without any
mocking --- the mock model path already works and most stages have clear
inputs/outputs.

**3. New Issue Introduced in v0.1.2**

**3.1 Ralph.\_call_llm hardcodes model names instead of using
self.model**

**File: slimzero/agent/ralph.py --- \_call_llm() method, lines 502, 510,
520, 535**

The new \_execute_step implementation adds a real LLM call via a private
\_call_llm method inside RalphLoop. However, unlike core.py which
correctly uses self.model, the ralph.py version hardcodes specific model
names:

  -----------------------------------------------------------------------
  **Client type**  **Hardcoded model in   **What user actually passed**
                   ralph.py**             
  ---------------- ---------------------- -------------------------------
  Anthropic        claude-sonnet-4-6      Could be claude-opus-4-6 or any
                                          other

  OpenAI /         gpt-4o                 Could be gpt-4o-mini,
  OpenCode                                gpt-3.5-turbo, etc.

  Ollama (urllib   llama3.2               Could be qwen3, mistral, phi3,
  fallback)                               etc.

  Default fallback gpt-4o                 Same problem as OpenAI case
  -----------------------------------------------------------------------

This means a user who initialises SlimZero with
model=\"claude-opus-4-6\" will have their regular call() use Opus
correctly but run_goal() will silently use Sonnet for all agent planning
steps --- at a lower cost but also lower quality. There is no warning
logged.

**Fix --- one line per branch**

-   Anthropic branch: change model=\"claude-sonnet-4-6\" to
    model=self.model

-   OpenAI branch: change model=\"gpt-4o\" to model=self.model

-   Ollama urllib branch: change \"llama3.2\" to self.model in the JSON
    body

-   Default fallback: change model=\"gpt-4o\" to model=self.model

RalphLoop already stores api_client but not model --- the model string
needs to be passed in from core.py when \_init_agent() is called, stored
as self.model, and used in \_call_llm.

**4. Remaining High Severity Issue**

**4.1 SavingsStats cost calculation still does not use the active
model\'s pricing**

**File: slimzero/schemas.py --- estimated_cost_savings property, line
194**

The previous audit flagged that estimated_cost_savings ignored the
model_pricing dict and used a hardcoded rate. The fix partially
addressed this --- it now reads from model_pricing --- but it always
reads the \"default\" key regardless of which model is actually being
used:

  -----------------------------------------------------------------------
  **default_pricing = self.model_pricing.get(\"default\", {\...}) return
  self.total_savings \* default_pricing\[\"input\"\]**

  -----------------------------------------------------------------------

The model_pricing dict defines separate rates for claude-sonnet-4-6,
claude-opus-4-6, and gpt-4o. Opus input tokens cost 5× more than Sonnet.
If a user is running Opus and saving 1,000 tokens per call, the
dashboard will show the Sonnet saving rate --- a 5× underestimate of
actual cost savings. This makes the savings dashboard misleading for
Opus users.

**Fix**

-   Pass the active model string into SavingsStats at construction time
    or via a method parameter

-   In estimated_cost_savings, look up
    self.model_pricing.get(self.model,
    self.model_pricing\[\"default\"\])

**5. Quality of the Fixes**

The fixes in v0.1.2 are well-implemented --- not just patched but
properly refactored. Specific call-outs:

**5.1 utils/ module --- excellent architecture**

The addition of slimzero/utils/ with SharedEmbeddingModel and
TokenCounter is the right approach. The Singleton pattern for both is
correctly implemented using \_\_new\_\_ with an \_initialized guard. The
SharedEmbeddingModel is used by all three consuming stages
(semantic_guard, few_shot, validator) --- confirmed by grep. This fixes
the 240MB RAM waste cleanly.

One minor note: SharedEmbeddingModel.similarity() still uses a manual
Python zip loop for dot product. This is fine for correctness but numpy
would be \~100× faster for long embeddings. Not a bug --- just worth
knowing for performance tuning later.

**5.2 \_call_llm in core.py --- proper multi-SDK support**

The new \_call_llm implementation in core.py correctly detects the
client type via \_\_module\_\_ inspection, routes to the right SDK
format, and raises SlimZeroInputError (not a silent mock) when no client
is configured. The Anthropic branch correctly uses
client.messages.create() with max_tokens. This is a proper fix, not a
workaround.

**5.3 \_execute_step --- real agent loop**

The agent loop now has real observe-plan-act-reflect logic:
\_build_context() reads recent audit entries, \_build_plan_prompt()
constructs an LLM prompt, \_parse_plan() extracts actionable text,
\_select_action() does keyword-based tool routing, \_execute_action()
dispatches, and \_reflect() logs. This is a functional agent, not a
stub. The action selection (keyword matching for \"search\", \"find\",
etc.) is simple but honest --- it does not pretend to be smarter than it
is.

**5.4 GitHub Actions workflow**

The publish.yml workflow is well-structured: builds, runs tests, runs
mypy, then publishes. It supports both TestPyPI and PyPI targets via
workflow_dispatch, with tag-based automation for releases. The only
problem is the missing tests/ directory that blocks it --- the workflow
itself is correct.

**6. Minor Remaining Items**

These were low-severity findings in the previous audit that remain, and
a few small new observations:

  -----------------------------------------------------------------------------------------------
  **Issue**                **File**                              **Status**     **Fix effort**
  ------------------------ ------------------------------------- -------------- -----------------
  embedding.py uses manual utils/embedding.py                    Unchanged ---  30 min
  Python zip loop for                                            performance    
  cosine similarity                                              only, not a    
  instead of numpy                                               bug            

  SVG diagram files        Root dir                              New in v0.1.2  5 min (move
  committed to repo root                                         --- should be  files)
  (3 files, \~366 lines                                          in             
  each)                                                          docs/images/   

  activate-venv.bat still  Root dir                              Unchanged from 5 min (gitignore)
  in repo root                                                   v0.1.1         

  prd.json still in repo   Root dir                              Unchanged from 5 min (move to
  root (18KB internal                                            v0.1.1         docs/)
  planning doc)                                                                 

  CI workflow runs pytest  publish.yml                           New in v0.1.2  3-4 hrs (write
  tests/ but tests/ does                                         --- blocks all tests)
  not exist                                                      releases       

  scripts/ralph/ contains  scripts/ralph/                        New in v0.1.2  5 min (gitignore
  CLAUDE.md and prompt.md                                        --- not        or remove)
  --- appears to be                                              harmful but    
  internal AI tooling                                            confusing for  
  notes committed                                                open source    
  accidentally                                                   contributors   

  ralph.py                 agent/ralph.py                        New regression 5 min (import and
  \_estimate_tokens still                                        from v0.1.2    use count_tokens)
  uses word-split not the                                        (utils added   
  shared TokenCounter from                                       but ralph did  
  utils                                                          not adopt it)  

  benchmark suite uses     examples/benchmarks/\_\_init\_\_.py   Expected for   10 min (add docs
  model=\"mock\" by                                              CI but should  note)
  default --- cannot                                             be documented  
  measure real token                                                            
  savings without a live                                                        
  API key                                                                       
  -----------------------------------------------------------------------------------------------

**7. Audit Scorecard --- v0.1.1 vs v0.1.2**

  ------------------------------------------------------------------------
  **Dimension**             **v0.1.1 score** **v0.1.2 score** **Change**
  ------------------------- ---------------- ---------------- ------------
  API client compatibility  2/10 --- OpenAI  9/10 ---         ▲ +7
                            only             Anthropic +      
                                             OpenAI + Ollama  

  Agent mode functionality  1/10 --- stub    7/10 --- real    ▲ +6
                            only             loop, minor      
                                             model bug        

  Test coverage             0/10 --- no      0/10 --- still   --- 0
                            tests at all     no tests         

  Token counting accuracy   3/10 ---         8/10 --- shared  ▲ +5
                            word-split       TokenCounter     
                            everywhere       used in pipeline 

  Memory efficiency         4/10 --- 3×      9/10 ---         ▲ +5
                            MiniLM instances singleton shared 
                                             model            

  Dependency configuration  2/10 --- all     8/10 --- core    ▲ +6
                            optional         deps in base     

  Fault prevention          7/10 --- good    9/10 ---         ▲ +2
                            design, drift    DriftHalt        
                            bug              checkpoint fixed 

  Cost reporting accuracy   3/10 ---         5/10 --- uses    ▲ +2
                            hardcoded rate   dict but wrong   
                                             key              

  Repo hygiene              5/10 --- garbled 6/10 --- garbled ▲ +1
                            string, .bat     fixed, SVGs      
                            file             added to root    

  CI/CD readiness           N/A --- no       3/10 ---         ▲ new
                            workflow         workflow exists  
                                             but will fail    

  Overall                   3.7/10           6.4/10           ▲ +2.7
  ------------------------------------------------------------------------

**8. Priority Fix List for v0.1.3**

Three fixes will move SlimZero from B+ to A-:

  -------------------------------------------------------------------------------
  **Priority**   **Fix**                        **Effort**   **Impact**
  -------------- ------------------------------ ------------ --------------------
  1 --- Critical Write tests/ directory with 5  3-4 hrs      Unblocks CI/CD
                 basic test files                            publish pipeline
                                                             entirely

  2 --- Critical Fix ralph.\_call_llm to use    15 min       Agent mode uses the
  (new)          self.model not hardcoded model              model the user
                 names                                       actually specified

  3 --- High     Fix SavingsStats to look up    20 min       Accurate cost
                 active model in model_pricing               reporting for Opus
                 dict                                        users (5×
                                                             difference)

  4 --- Minor    Move SVG files from root to    5 min        Clean repo root
                 docs/images/                                

  5 --- Minor    Fix ralph.\_estimate_tokens to 5 min        Consistent token
                 use shared count_tokens()                   counting throughout

  6 --- Minor    Remove scripts/ralph/CLAUDE.md 5 min        Cleaner open source
                 from public repo (internal                  presentation
                 notes)                                      
  -------------------------------------------------------------------------------

**9. Final Verdict**

The progress from v0.1.1 to v0.1.2 is substantial and clearly
intentional. The author read the previous audit carefully and addressed
it methodically --- 9 of 12 issues resolved in a single update. The
quality of the fixes is good: the utils/ refactor is properly
architected, the API client routing is correctly implemented, and the
agent loop is now a real implementation rather than a stub.

The two remaining critical issues are both addressable in a single
focused session. Writing 5-6 test files takes a few hours. Fixing the
hardcoded model names in ralph.py is a 15-minute change. After those two
fixes, SlimZero will be a library that installs correctly, works with
all major LLM providers, runs a real agent loop, and has a CI pipeline
that actually passes.

The project is on a strong trajectory. The architecture remains sound,
the PRD-to-code translation is faithful, and the new additions
(benchmark suite, CI workflow, utils module) show engineering maturity.
A v0.1.3 with tests and the model-name fix would be a genuinely
publishable, promotable open-source library.

  -----------------------------------------------------------------------
  **Estimated time to reach a solid, promotable v0.1.3: 4-5 hours of
  focused work (dominated by writing the test suite).**

  -----------------------------------------------------------------------

*--- End of SlimZero Cross-Check Audit Report v0.1.2 ---*
