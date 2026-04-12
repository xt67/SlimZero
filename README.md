# SlimZero v1 - Documentation Index

## Start Here
- **`SETUP_COMPLETE.md`** ← 📍 You are here
- **`QUICKREF.md`** - Commands and quick tips
- **`docs/SETUP.md`** - Detailed guides and workflows

## Understanding the Tools

### Ralph (Autonomous AI Agent Loop)
- **What:** Runs AI coding tools iteratively to implement user stories
- **How:** Reads `prd.json`, picks next story, spawns fresh AI instance, implements, tests, commits
- **Why:** Allows autonomous feature development with memory via git history
- **Files:** `scripts/ralph/` directory
- **Read:** `scripts/ralph/prd.json.example` for format

### GSD (Get Shit Done)
- **What:** Spec-driven development system for Claude Code
- **How:** Provides context engineering and quality gates to prevent quality degradation
- **Why:** Makes Claude Code more reliable for larger projects
- **Files:** `.gsd/` directory, `.claude/skills/` 
- **Read:** `.gsd/README.md` for full documentation

## Key Files Explained

| File | What It Is | Edit? | Why |
|------|-----------|-------|-----|
| `prd.json` | Ralph task list | YES | Add your user stories here |
| `progress.txt` | Iteration progress | READ | See what Ralph learned |
| `scripts/ralph/prompt.md` | Amp instructions | MAYBE | Add project-specific checks |
| `scripts/ralph/CLAUDE.md` | Claude Code instructions | MAYBE | Customize for your project |
| `scripts/ralph/AGENTS.md` | Discovered patterns | READ | Contains project insights |
| `.gsd/` | GSD tool | NO | Leave as-is |
| `.claude/` | Claude config | NO | Leave as-is |
| `archive/` | Previous runs | READ | Historical context |

## Workflows

### Minimal: Ralph Only (One-off Features)
```
1. Update prd.json with your story
2. Run: ./scripts/ralph/ralph.sh
3. Monitor progress.txt
```

### Complete: Ralph + GSD (Complex Projects)
```
1. Use /gsd-new-project to plan
2. Convert plan to prd.json stories
3. Run Ralph to implement: ./scripts/ralph/ralph.sh
4. Use /gsd-plan for new features
```

### Real-Time: GSD Commands (Live Coding)
```
In Claude Code:
- /gsd-help for available commands
- /gsd-new-project to initialize
- /gsd-plan [description] to create plans
```

## Project Structure at a Glance

```
SlimZero v1/
│
├── 📋 Configuration
│   ├── prd.json              ← EDIT THIS (user stories)
│   ├── progress.txt          ← Iteration history
│   └── scripts/ralph/        ← Ralph tool
│       ├── ralph.sh          (main loop)
│       ├── prompt.md         (Amp template)
│       └── CLAUDE.md         (Claude Code template)
│
├── 🛠️ Tools
│   ├── .gsd/                 ← GSD installation
│   └── .claude/              ← Claude Code config
│
├── 📚 Documentation
│   ├── SETUP_COMPLETE.md     (this file)
│   ├── QUICKREF.md           (commands)
│   ├── docs/SETUP.md         (detailed guide)
│   └── docs/                 (other docs)
│
└── 📦 Directories
    ├── archive/              ← Previous Ralph runs
    └── tasks/                ← Task docs
```

## Common Tasks

### Run Ralph
```bash
./scripts/ralph/ralph.sh
```

### Check Status
```bash
cat prd.json | jq '.userStories[] | {id, title, passes}'
```

### See Learnings
```bash
cat progress.txt
```

### Use GSD
```
In Claude Code, run:
/gsd-help
/gsd-new-project
/gsd-plan
```

### Add a Story
Edit `prd.json` and add to `userStories` array:
```json
{
  "id": "unique-id",
  "title": "Story Title",
  "description": "What to do",
  "acceptanceCriteria": ["Specific testable criteria"],
  "priority": 1,
  "passes": false
}
```

## Recommended Reading Order

1. **`QUICKREF.md`** (5 min) - Get the commands
2. **`SETUP_COMPLETE.md`** (10 min) - Understand what's installed
3. **`docs/SETUP.md`** (15 min) - Learn the workflow
4. **`scripts/ralph/prd.json.example`** (5 min) - See story format
5. **`.gsd/README.md`** (20 min) - Deep dive on GSD

## Getting Help

### Ralph Questions
- See: `scripts/ralph/prd.json.example`
- See: `scripts/ralph/AGENTS.md` (discovered patterns)
- See: `docs/SETUP.md` (detailed guide)

### GSD Questions
- Run: `/gsd-help` in Claude Code
- See: `.gsd/README.md`
- See: `.gsd/docs/`

### General Setup Issues
- See: `docs/SETUP.md` → Troubleshooting section
- Check: `progress.txt` for error messages
- Verify: Git is initialized, tools are installed

## Next Immediate Steps

1. ✅ Setup is complete (you're here)
2. **→ Open `QUICKREF.md` for immediate next steps**
3. → Review your PRD and update `prd.json`
4. → Initialize git: `git init && git add . && git commit -m "initial"`
5. → Run Ralph: `./scripts/ralph/ralph.sh`

---

**Status:** ✅ Ready to Build  
**Last Updated:** 2026-04-11 17:15 UTC  
**Maintenance:** Minimal - Ralph and GSD are mostly self-contained

Open **`QUICKREF.md`** next → 
