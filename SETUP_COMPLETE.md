# SlimZero v1 - Ralph & GSD Setup Complete ✅

## What's Been Set Up

### ✅ Ralph (Autonomous AI Agent Loop)
Ralph is now configured to autonomously iterate on user stories from `prd.json`.

**Installed Files:**
- `scripts/ralph/ralph.sh` - Main loop script
- `scripts/ralph/prompt.md` - Amp template
- `scripts/ralph/CLAUDE.md` - Claude Code template
- `scripts/ralph/AGENTS.md` - Discovered patterns log
- `scripts/ralph/prd.json.example` - Example format

**How it works:**
1. Reads stories from `prd.json` with `passes: false`
2. Picks highest priority story
3. Spawns fresh AI instance (Amp or Claude Code)
4. Implements that story in one iteration
5. Runs quality checks (tests, typecheck)
6. Updates `prd.json` to `passes: true`
7. Appends learnings to `progress.txt`
8. Repeats until all stories pass or iterations exhausted

### ✅ GSD (Get Shit Done - Spec-Driven Development)
GSD is installed and ready for use in Claude Code.

**Installed in:**
- `.gsd/` - Core tool, commands, agents, SDK
- `.claude/` - Claude Code skills (PRD and Ralph skills)

**Key GSD Features:**
- Context engineering to prevent quality degradation
- Built-in quality gates (pre-flight, revision, escalation, abort)
- Schema drift detection
- Scope reduction prevention
- Works with Claude Code, OpenCode, Gemini, Kilo, and more

### ✅ Project Files Created

| File | Purpose |
|------|---------|
| `prd.json` | Ralph task list (main control file) |
| `progress.txt` | Iteration learnings and context |
| `docs/SETUP.md` | Detailed setup and workflow guide |
| `QUICKREF.md` | Quick reference for common commands |

### ✅ Project Structure

```
SlimZero v1/
├── scripts/ralph/           # Ralph loop and templates
│   ├── ralph.sh            # Main executable
│   ├── prompt.md           # Amp prompt template
│   ├── CLAUDE.md           # Claude Code template
│   └── AGENTS.md           # Pattern discoveries
│
├── .claude/                # Claude Code config
│   └── skills/             # Ralph/PRD skills
│
├── .gsd/                   # GSD tool installation
│   ├── commands/           # GSD commands
│   ├── agents/             # GSD agents
│   └── sdk/                # GSD SDK
│
├── prd.json               # Ralph user stories (EDIT THIS)
├── progress.txt           # Iteration progress
├── docs/SETUP.md          # Setup guide
├── QUICKREF.md            # Quick reference
├── archive/               # Previous run backups
├── tasks/                 # Task documentation
└── [PRD files]            # Your original PRD files
```

---

## Quick Start

### 1. Update prd.json with Your Stories

Edit `prd.json` and add your actual user stories:

```json
{
  "title": "SlimZero v1",
  "description": "Your project description",
  "branchName": "main",
  "userStories": [
    {
      "id": "story-1",
      "title": "User Authentication",
      "description": "Implement user login and registration",
      "acceptanceCriteria": [
        "Users can sign up with email and password",
        "Login works correctly",
        "Tests pass"
      ],
      "priority": 1,
      "passes": false
    }
  ]
}
```

### 2. Initialize Git

```bash
git init
git add .
git commit -m "Initial SlimZero setup with Ralph and GSD"
```

### 3. Add Quality Checks

Edit `scripts/ralph/prompt.md` to add your test and typecheck commands.

### 4. Run Ralph

```bash
./scripts/ralph/ralph.sh
```

Ralph will iterate on your stories until they all pass!

---

## How to Use GSD

### In Claude Code

```
/gsd-help                # Get help
/gsd-new-project         # Initialize GSD planning
/gsd-map-codebase        # Index your codebase
/gsd-plan [description]  # Create a plan
```

### With Ralph

GSD and Ralph complement each other:
- Use **GSD** for real-time planning and problem-solving in Claude Code
- Use **Ralph** for autonomous, iterative implementation of user stories
- Together they provide both spec-driven development AND autonomous execution

---

## Important Notes

### Ralph Best Practices

1. **Keep stories small** - Each should fit in one AI context window
2. **Separate concerns** - Don't bundle "add auth + add API" into one story
3. **Add acceptance criteria** - Make stories testable and specific
4. **Use git** - Ralph relies on git history for memory
5. **Update AGENTS.md** - Ralph auto-updates this; review it between runs
6. **Quality checks matter** - Tests and linting catch regressions

### Right-Sized Stories

✅ Good:
- Add a database column and migration
- Add a UI component to existing page
- Fix a specific bug
- Add API endpoint for one resource

❌ Too big:
- "Build the entire dashboard"
- "Add authentication"
- "Refactor the entire backend"

---

## Next Steps

1. **Review your PRD** - Ensure you have it in the required format
2. **Update prd.json** - Add your actual user stories
3. **Initialize git** - `git init && git add . && git commit -m "initial"`
4. **Add quality checks** - Update `scripts/ralph/prompt.md`
5. **Run Ralph** - Execute `./scripts/ralph/ralph.sh`
6. **Monitor progress** - Check `progress.txt` and `prd.json`

---

## Files to Read

- **`docs/SETUP.md`** - Detailed setup and workflow guide
- **`QUICKREF.md`** - Common commands and tips
- **`scripts/ralph/prd.json.example`** - Example PRD format
- **`scripts/ralph/AGENTS.md`** - Discovered patterns and gotchas
- **`.gsd/README.md`** - GSD documentation

---

## Troubleshooting

**Ralph won't run:**
- Make sure git is initialized: `git init`
- Check ralph.sh has execute permissions: `chmod +x scripts/ralph/ralph.sh`
- Verify Amp or Claude Code is installed
- Confirm jq is installed (used for JSON parsing)

**GSD commands not found:**
- Run `npx get-shit-done-cc@latest` to update/install
- Verify Claude Code is version 2.1.88+

**Stories not completing:**
- Check `progress.txt` for learnings and errors
- Review `prd.json` - stories might be too large
- Ensure quality checks (tests, typecheck) are in prompt
- Check `.git/config` to verify git is properly initialized

---

**Setup completed:** 2026-04-11 17:15 UTC  
**Ralph Version:** Latest  
**GSD Version:** Latest  
**Status:** ✅ Ready to Start

See `docs/SETUP.md` for comprehensive guide. See `QUICKREF.md` for common commands.
