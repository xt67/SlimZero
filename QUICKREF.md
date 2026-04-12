# Ralph & GSD Quick Reference

## Ralph Commands

```bash
# Run Ralph with default settings (10 iterations)
./scripts/ralph/ralph.sh

# Run Ralph with 20 iterations
./scripts/ralph/ralph.sh 20

# Using Claude Code instead of Amp
./scripts/ralph/ralph.sh --tool claude 10
```

## Check Ralph Status

```bash
# See which stories are done
cat prd.json | jq '.userStories[] | {id, title, passes}'

# View learnings from iterations
cat progress.txt

# Check git history
git log --oneline -10
```

## GSD Quick Start

```bash
# Initialize GSD in this project
npx get-shit-done-cc@latest

# Use in Claude Code (after installing)
/gsd-help
/gsd-new-project
/gsd-plan
```

## Key Files to Know

| File | Purpose |
|------|---------|
| `prd.json` | Ralph task list (mark stories `passes: true` when done) |
| `progress.txt` | Iteration learnings and context |
| `scripts/ralph/AGENTS.md` | Patterns discovered during iterations |
| `.claude/` | Claude Code configuration |
| `.gsd/` | GSD tool and utilities |
| `docs/SETUP.md` | Detailed setup and workflow guide |

## Important for Ralph Success

1. **Keep stories small** - Each story should fit in one AI context window
2. **Update AGENTS.md** - Ralph auto-updates this with discovered patterns
3. **Add quality checks** - Tests and type-checking are essential feedback loops
4. **Initialize git** - Ralph needs git history to track progress
5. **Test in browser** - UI stories need "Verify in browser" acceptance criteria

## Workflow Tips

- Start with `prd.json` containing 1-3 high-priority stories
- Run Ralph with a reasonable iteration limit (10-20)
- Check progress.txt after each run to see what was learned
- Update prd.json as needed and re-run Ralph
- Archive completes in `archive/` for history

---

For full details, see `docs/SETUP.md`
