# SlimZero Setup Guide

## Ralph - Autonomous AI Agent Loop

Ralph is an autonomous loop that implements PRD items one at a time. Each iteration runs fresh AI instances (Amp or Claude Code) with clean context.

### Using Ralph

1. **Update prd.json** with your user stories (see prd.json.example in scripts/ralph/)
2. **Run Ralph** to iterate on stories:
   ```bash
   ./scripts/ralph/ralph.sh [max_iterations]
   ```
   Default: 10 iterations

### Ralph Key Files
- `prd.json` - User stories with status tracking
- `progress.txt` - Learnings and context for iterations
- `scripts/ralph/prompt.md` - Prompt template for Amp
- `scripts/ralph/CLAUDE.md` - Prompt template for Claude Code
- `scripts/ralph/AGENTS.md` - Auto-updated with discovered patterns
- `archive/` - Previous run archives

### Ralph Requirements
- One of: Amp CLI (default) or Claude Code
- `jq` installed (for parsing)
- Git repository initialized

---

## GSD - Get Shit Done (Spec-Driven Development)

GSD is a powerful spec-driven development system for Claude Code that prevents context rot.

### Using GSD

Install GSD in your project:
```bash
npx get-shit-done-cc@latest
```

Then access GSD commands in Claude Code:
- `/gsd-help` - Get help
- `/gsd-new-project` - Initialize new GSD project
- `/gsd-map-codebase` - Index current codebase state
- `/gsd-plan` - Create development plan

### GSD Benefits
- Context engineering prevents quality degradation as context fills
- Built-in quality gates catch real problems
- Spec-driven approach ensures consistent implementation
- Works with Claude Code, OpenCode, Gemini, Kilo, and more

### GSD Structure
- `.gsd/` - GSD tool files and utilities
- `.claude/` - Claude Code configuration and skills

---

## Recommended Workflow

1. **For one-off features:** Use Ralph with prd.json
2. **For complex projects:** Use GSD's planning + Ralph execution
3. **For real-time coding:** Use GSD commands in Claude Code directly
4. **For iteration:** Ralph tracks progress via prd.json and progress.txt

---

## Project Structure

```
.
├── prd.json                 # Ralph user stories (task list)
├── progress.txt             # Ralph iteration learnings
├── scripts/ralph/           # Ralph loop and templates
├── .claude/                 # Claude Code configuration
├── .gsd/                    # GSD tool files
├── archive/                 # Previous Ralph run archives
├── tasks/                   # Task documentation
└── docs/                    # Project documentation
```

---

## Quality Checks

Ralph needs feedback loops to work effectively:
- Add typecheck command to scripts/ralph/prompt.md
- Add test command to scripts/ralph/prompt.md
- Ensure CI stays green between iterations

---

## Next: Expand Your PRD

Edit `prd.json` and add your actual user stories following this format:

```json
{
  "id": "unique-story-id",
  "title": "Story Title",
  "description": "What needs to be done",
  "acceptanceCriteria": [
    "Specific, testable criteria"
  ],
  "priority": 1,
  "passes": false
}
```

Then run: `./scripts/ralph/ralph.sh`
