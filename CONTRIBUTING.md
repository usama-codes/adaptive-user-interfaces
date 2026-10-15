# Contributing

## Branch Structure

main        → sprint-reviewed, stable code only. Never pushed to directly.
develop     → active sprint work. All feature branches merge here.
feature/*   → one branch per task, branched from develop, deleted after merge.

## Branch Naming

feature/<task-id>-short-description

Examples:
  feature/T1.1-fastapi-init
  feature/T1.3-openproject-client
  feature/T2.4-gemini-function-calling

## Starting a Task

git checkout develop
git pull origin develop
git checkout -b feature/T1.x-your-task

## Submitting Work

1. Push your feature branch to origin.
2. Open a PR into develop (not main).
3. PR title: [T1.x] Short description of what was built.
4. PR description must include:
   - What was built (2–3 sentences)
   - How to test it locally (exact commands)
   - Screenshot or terminal output proving it works
   - Checklist of the task's Definition of Done items, each checked
5. At least one other team member must approve before merge.
6. CI must pass (lint + type check + tests) before merge.
7. Delete the feature branch after merge.

## PR into main

Only at sprint review. One PR: develop → main.
PR title: Sprint <N> — <sprint goal one-liner>.
All three members must approve.

## Commit Messages

Format: <type>: <short description>

Types: feat | fix | test | docs | chore | refactor

Examples:
  feat: add OpenProject authenticated HTTP client
  test: add unit tests for session TTL expiry
  docs: update CONTRACTS.md with Intent JSON schema v2
  chore: add ruff to pre-commit config

One logical change per commit. Do not bundle unrelated changes.

## Code Style

Formatter : black (line length 88)
Import sort: isort
Linter     : ruff (rules E, F, I)

All three are enforced by pre-commit hooks. Run pre-commit install
once after cloning. Hooks run automatically on every commit and
fix or flag violations before the commit is finalized.

To run manually:
  pre-commit run --all-files

## Running Tests

pytest                        # run all tests
pytest tests/unit/            # unit tests only
pytest tests/integration/     # integration tests only
pytest -k "test_session"      # run tests matching a name pattern

All tests must pass locally before opening a PR.

## Environment Setup

1. Clone the repo.
2. Create a virtual environment: python -m venv .venv
3. Activate it: source .venv/bin/activate  (Windows: .venv\Scripts\activate)
4. Install dependencies: pip install -r requirements.txt
5. Copy .env.example to .env and fill in all values.
6. Run pre-commit install.
7. Start the server: uvicorn main:app --reload
8. Verify: GET http://localhost:8000/health returns {"status": "ok"}

Refer to ENVIRONMENT_NOTES.md for known issues on specific machines.

## Interface Changes

If your task changes a contract between components (request/response
shape, function signature, config key name), you must update
CONTRACTS.md in the same PR. Do not merge interface changes without
updating the contract document.

If your task involves a significant architectural decision, add an
ADR to docs/adr/ following the existing template before merging.