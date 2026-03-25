---
name: create-backend-pr
description: Steps to create a backend PR that passes CI. Use when implementing any backend feature.
---

# Create Backend PR

## Before coding
1. Check out main and pull latest: `git checkout main && git pull`
2. Create feature branch: `git checkout -b NN-feature-name`
3. Check the execution plan in `.context/plans/startuptracker-execution-plan.md` for what this PR should contain

## While coding
- Keep lines under 100 chars
- Use `from collections.abc import Sequence` not `from typing import Sequence`
- Use `X | None` not `Optional[X]` or `Union[X, None]`
- Import order: stdlib -> third-party -> local (ruff I001 enforces this)
- SQLAlchemy models use `mapped_column()` style, not legacy `Column()` (except for Table associations)
- Pydantic schemas use `model_config = ConfigDict(from_attributes=True)`

## Before pushing
```bash
cd backend
ruff check .            # lint
ruff format .           # format
pytest -v               # test
```
All three must pass — CI runs them separately.

## Creating the PR
1. `git add <specific files>` (never `git add .`)
2. `git commit -m "Description\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"`
3. `git push origin NN-feature-name -u`
4. `gh pr create --base main --title "Short title" --body "## Summary\n- bullets\n\nCloses #N"`

## After PR is created
- Wait for CI to pass
- If CI fails, check `gh run view <id> --log-failed | tail -30`
- Common failures: ruff format (separate from ruff check), line too long in alembic files
