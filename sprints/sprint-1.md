# Sprint 1 Issues (Copy to GitHub UI)

---

## T1.1 — FastAPI project initialization

**Epic:** infrastructure | **Type:** feature | **Priority:** high

### Description

Initialize the FastAPI application with proper folder structure, configuration management, and health check endpoint.

### What to build

- Directory structure: `app/` containing `routes/`, `services/`, `models/`, `core/`
- `main.py` at the repo root that wires up the FastAPI app and mounts all routers
- `app/core/config.py` reads all environment variables using Pydantic's `BaseSettings`
  - All variables must have explicit types
  - No raw `os.getenv` calls anywhere else in the codebase
- Health check route `GET /health` returns `{"status": "ok", "version": "0.1.0"}`
- Uvicorn configured to run on port 8000
- `requirements.txt` with pinned versions committed
- `.env.example` with all required keys (but no values) committed

### Definition of Done

- [ ] `uvicorn main:app --reload` starts with no errors
- [ ] `GET /health` returns HTTP 200 with correct JSON body
- [ ] A second team member can clone the repo fresh, run `pip install -r requirements.txt`, fill in `.env` from `.env.example`, and start the server in under 5 minutes with no additional guidance needed

### Acceptance Criteria

- FastAPI app initializes without warnings
- Config loads correctly from environment variables
- All three team members can run the server locally

---

## T1.2 — Pre-commit hooks and GitHub Actions CI

**Epic:** infrastructure | **Type:** feature | **Priority:** high

### Description

Set up code quality enforcement via pre-commit hooks and CI pipeline to ensure all committed code passes linting, formatting, and tests.

### What to build

- `.pre-commit-config.yaml` with three hooks:
  - `black` (code formatter)
  - `isort` (import sorter)
  - `ruff` (linter with rules E, F, I)
- GitHub Actions workflow at `.github/workflows/ci.yml`:
  - Triggers on every push to `develop` and `main`
  - Steps: checkout → Python 3.11 setup → install dependencies → `pre-commit run --all-files` → `pytest`
- CI status badge added to `README.md`

### Definition of Done

- [ ] `.pre-commit-config.yaml` committed and all three hooks are runnable locally
- [ ] `.github/workflows/ci.yml` created and runs successfully on push
- [ ] All three team members have run `pre-commit install` locally
- [ ] Pushing a Python file with an unused import to `develop` causes CI to fail
- [ ] Fixing the import and pushing again causes CI to pass
- [ ] CI status badge visible on `README.md`

### Acceptance Criteria

- Pre-commit hooks automatically fix formatting violations before commits
- CI pipeline enforces the same standards on every push
- No code can be merged to `develop` if CI fails

---

## T1.3 — OpenProject authenticated HTTP client

**Epic:** bff | **Type:** feature | **Priority:** high

### Description

Build a reusable, typed HTTP client for the OpenProject API with proper authentication, retry logic, and error handling.

### What to build

- `app/core/openproject_client.py` with an `OpenProjectClient` class wrapping `httpx.AsyncClient`
- Constructor reads `OPENPROJECT_URL` and `OPENPROJECT_API_TOKEN` from config
- Every request injects the header `Authorization: Token <token>`
- Implement `async get(path: str, params: dict = None)` and `async post(path: str, body: dict)`
- Both methods enforce a 10-second timeout
- On HTTP 5xx responses, retry up to 2 times with exponential backoff (1s, 2s)
- On HTTP 401, raise `OpenProjectAuthError`
- On any other error, raise `OpenProjectAPIError` with status code and response body attached
- Unit tests using `respx` (mock library for httpx) covering:
  - Successful GET request
  - HTTP 401 raises `OpenProjectAuthError`
  - HTTP 500 triggers retries then raises `OpenProjectAPIError`
  - Timeout raises appropriate error

### Definition of Done

- [ ] 4 unit tests pass in CI
- [ ] Client instantiated manually and `client.get("/api/v3/users/me")` returns authenticated user JSON from local OpenProject
- [ ] Error classes defined in `app/core/exceptions.py`
- [ ] Retry logic verified via test mocks

### Acceptance Criteria

- Client handles authentication correctly
- Retries work as expected on transient failures
- All error cases have appropriate exception types
- Code is testable via `respx` mocks

---

## T1.4 — User roles and memberships retrieval

**Epic:** bff | **Type:** feature | **Priority:** high

### Description

Fetch and parse OpenProject memberships and role information for a given user.

### What to build

- `app/services/permissions_service.py`
- Define a `Membership` dataclass with fields:
  - `project_id: int`
  - `project_name: str`
  - `role_ids: list[int]`
- Implement `async get_user_memberships(user_id: int, client: OpenProjectClient) -> list[Membership]`
  - Calls `GET /api/v3/memberships` with filter for the given user
  - Parses `_embedded.elements` array
  - Maps each element to a `Membership` object
- Unit tests using `respx`-mocked responses covering:
  - User with memberships in 2 projects (assert 2 Membership objects returned)
  - User with no memberships (assert empty list)
  - API error propagation (assert `OpenProjectAPIError` is raised)

### Definition of Done

- [ ] 3 unit tests pass in CI
- [ ] Function called against local OpenProject instance with real user_id
- [ ] Returned data verified against OpenProject admin UI

### Acceptance Criteria

- Correctly parses OpenProject API response format
- Handles users with multiple project memberships
- Handles users with no memberships gracefully
- All dataclasses are properly typed

---

## T1.5 — Permission scope retrieval

**Epic:** bff | **Type:** feature | **Priority:** high

### Description

Retrieve role permissions and compose them into a user's effective permission set for a given project.

### What to build

- Continue in `app/services/permissions_service.py`
- Define a `PermissionSet` dataclass:
  - `user_id: int`
  - `project_id: int`
  - `permissions: list[str]`
- Implement `async get_role_permissions(role_id: int, client: OpenProjectClient) -> list[str]`
  - Calls `GET /api/v3/roles/:id`
  - Extracts permissions array
- Implement `async get_user_permissions(user_id: int, project_id: int, client: OpenProjectClient) -> PermissionSet`
  - Composes `get_user_memberships` and `get_role_permissions`
  - Finds user's memberships in the given project
  - Fetches permissions for each role
  - Deduplicates permissions
  - Returns a PermissionSet
- Unit tests covering:
  - User with 2 roles in a project where roles have overlapping permissions (verify deduplication)
  - User not a member of the given project (assert empty PermissionSet, no error)
  - API error in role fetch (assert error is propagated)

### Definition of Done

- [ ] 3 unit tests pass in CI
- [ ] `get_user_permissions` called against local OpenProject
- [ ] Returns non-empty PermissionSet for an admin user
- [ ] Returns restricted PermissionSet for a viewer-role user
- [ ] Results verified against OpenProject role configuration in UI

### Acceptance Criteria

- Permission deduplication works correctly
- Handles users with no permissions in a project
- Proper error propagation from the OpenProject API

---

## T1.6 — In-memory session store

**Epic:** bff | **Type:** feature | **Priority:** high

### Description

Implement a thread-safe, TTL-based in-memory session store for tracking user sessions during intent processing.

### What to build

- `app/core/session.py`
- Define a `Session` dataclass:
  - `session_id: str`
  - `user_id: int`
  - `created_at: datetime`
  - `last_accessed: datetime`
- Implement a `SessionStore` class backed by a plain Python dict with methods:
  - `create_session(user_id: int) -> Session` (generates UUID4, stores, returns)
  - `get_session(session_id: str) -> Session | None` (returns None and deletes if older than 30 minutes)
  - `delete_session(session_id: str) -> None`
  - `update_last_accessed(session_id: str) -> None`
- Register `SessionStore` as a FastAPI dependency using `Depends`
- Unit tests covering:
  - Create and immediately get returns the session
  - Get after 31 minutes (with patched datetime) returns None and removes entry
  - Delete then get returns None
  - Dependency injection works correctly

### Definition of Done

- [ ] 4 unit tests pass in CI
- [ ] `SessionStore` injected into a test route via `Depends` and functional
- [ ] TTL expiry verified with datetime mocking
- [ ] Can be used as a dependency in route handlers

### Acceptance Criteria

- Sessions expire correctly after 30 minutes of inactivity
- Session CRUD operations are atomic
- Works seamlessly with FastAPI dependency injection

---

## T1.7 — `POST /intent` endpoint

**Epic:** bff | **Type:** feature | **Priority:** high

### Description

Create the main HTTP endpoint that receives raw user intent text and validates it against the Intent JSON schema.

### What to build

- `app/routes/intent.py`
- Define a Pydantic request model `IntentRequest`:
  - `session_id: str`
  - `raw_text: str` (min length 1, max length 2000)
- Implement `POST /intent`:
  - Validate request body against `IntentRequest` (FastAPI validates via Pydantic)
  - Look up `session_id` in SessionStore
  - If not found, return HTTP 401 with error code `SESSION_NOT_FOUND`
  - Load `schemas/intent.json` (already in repo from Week 1)
  - Return HTTP 202 with body: `{"status": "received", "intent": null, "message": "normalization not yet implemented"}`
  - Call `session_store.update_last_accessed(session_id)`
- Integration tests using FastAPI's `TestClient` covering:
  - Valid session_id and raw_text returns 202
  - Missing session_id field returns 422
  - Valid session_id but empty raw_text returns 422
  - Non-existent session_id returns 401

### Definition of Done

- [ ] 4 integration tests pass in CI
- [ ] Endpoint hit manually via curl with valid session_id
- [ ] Returns HTTP 202 with correct response body
- [ ] Invalid requests return appropriate HTTP status codes

### Acceptance Criteria

- Request validation works correctly
- Session lookup and TTL update function properly
- Error responses use the global error handler format
- Endpoint ready to accept intent text from the frontend widget

---

## T1.8 — Structured logging and global error handler

**Epic:** infrastructure | **Type:** feature | **Priority:** medium

### Description

Set up JSON-structured logging and a centralized exception handler for all API errors.

### What to build

- `app/core/logging_config.py`:
  - Configure `loguru` with JSON output format
  - Add FastAPI middleware that logs every request: method, path, HTTP status, response time (ms), session_id (if present)
- `app/core/exceptions.py`:
  - Define typed exception classes:
    - `OpenProjectAuthError` → HTTP 401
    - `SessionNotFoundError` → HTTP 401
    - `IntentValidationError` → HTTP 422
    - `OpenProjectAPIError` → HTTP 502
  - Register global exception handler on FastAPI app
  - Catches all typed exceptions and returns: `{"error": {"code": "<ERROR_CODE>", "message": "<message>"}}`
  - For unhandled exceptions: catch `Exception`, log full stack trace, return HTTP 500 with `{"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}}`
  - Never expose internal stack traces in response body
- Unit/integration tests covering:
  - Each typed exception returns correct HTTP status and error code
  - Unhandled exception returns 500 with standardized body
  - Stack trace not exposed in response

### Definition of Done

- [ ] All tests pass in CI
- [ ] Triggering each typed exception returns correct HTTP status
- [ ] Unhandled exceptions return 500 with no stack trace in body
- [ ] All test runs produce JSON-structured logs in CI output

### Acceptance Criteria

- Logging format is machine-readable JSON
- Error responses are consistent across all endpoints
- Internal errors do not leak sensitive information

---

## T1.9 — Environment verification

**Epic:** infrastructure | **Type:** feature | **Priority:** high

### Description

Verify that all three team members have the local environment fully configured and ready to develop.

### What to build

This is not a code task. Each team member confirms all of the following by end of today:

- Local OpenProject instance running and `GET /api/v3/users/me` with API token returns user JSON
- Python 3.11+ installed
- Virtual environment created from `requirements.txt`
- `pre-commit install` run successfully
- Feature branch created from `develop` for first assigned task

Create `ENVIRONMENT_NOTES.md` in repo root and commit:

- Record any environment discrepancies found (OS differences, port conflicts, OpenProject build issues on specific machines)
- This document is updated whenever a new environment dependency is introduced

### Definition of Done

- [ ] All three team members post confirmation in team channel
- [ ] All confirmations include evidence (e.g., screenshot of `GET /api/v3/users/me` response)
- [ ] `ENVIRONMENT_NOTES.md` committed to `develop`
- [ ] No team member is blocked by environment issues

### Acceptance Criteria

- All three members can start the BFF server
- All three members can authenticate to their local OpenProject instance
- CI environment is verified to work (CI badge visible on README)

---
