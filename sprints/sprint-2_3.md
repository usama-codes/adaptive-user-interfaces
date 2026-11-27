# Sprint 2 Issues (Copy to GitHub UI)

---

## T2.1 — Gemini function-calling integration and intent prompt

**Epic:** normalization | **Type:** feature | **Priority:** high
**Suggested owner:** Member A | **Effort:** Medium | **Branch:** feature/T2.1-gemini-intent

### Description

Convert raw natural-language text into canonical Intent JSON using Gemini 2.5 Flash function calling.

### What to build

- `app/services/normalization_service.py`
- Gemini 2.5 Flash called through the OpenAI-compatible API; key read from `GEMINI_API_KEY` via config
- Function/tool definition generated from `schemas/intent.json` so the model can only return fields the schema allows
- `app/prompts/intent_extraction.py`: system prompt with at least 8 few-shot examples covering time charts, view toggles, column visibility, widget placement
- `async normalize_intent(raw_text: str, user_context: dict) -> dict`
- Add the Intent JSON contract (input, output, error cases) to `CONTRACTS.md`
- Unit tests with the Gemini client mocked: valid response parsed, tool call missing returns a typed error

### Definition of Done

- [ ] 2 or more unit tests pass in CI
- [ ] Manual run: 5 different phrasings return valid Intent JSON from the real Gemini API
- [ ] `CONTRACTS.md` updated in the same PR
- [ ] No API key committed anywhere

### Acceptance Criteria

- Output always conforms to the Intent schema or raises a typed error
- Model, base URL and timeout are configurable via env vars
- Prompt lives in its own file so it can be tuned without code changes

---

## T2.2 — Intent output validation, retry and low-confidence handling

**Epic:** normalization | **Type:** feature | **Priority:** high
**Suggested owner:** Member B | **Effort:** Medium | **Branch:** feature/T2.2-intent-validation
**Depends on:** T2.1

### Description

Make normalization reliable: validate every model output and handle failure gracefully.

### What to build

- Validate normalizer output against `schemas/intent.json` (jsonschema)
- On schema mismatch, retry up to 2 times, feeding the validation error back into the prompt
- After retries are exhausted, raise `IntentValidationError` (already defined in Sprint 1)
- Low-confidence or unresolvable intent returns a user-facing fallback message: `"I couldn't understand that request. Try rephrasing."`
- Unit tests: valid on first try, valid on second try, fails after 3 attempts, low-confidence fallback

### Definition of Done

- [ ] 4 unit tests pass in CI
- [ ] Gibberish input ("asdf qwer") returns the fallback message, not a 500
- [ ] Retry count is logged via loguru

### Acceptance Criteria

- Never returns unvalidated model output downstream
- The retry cap is enforced
- Errors use the global error handler format

---

## T2.3 — Capability manifest

**Epic:** fast-path | **Type:** feature | **Priority:** high
**Suggested owner:** Member C | **Effort:** Medium | **Branch:** feature/T2.3-capability-manifest

### Description

Create the catalogue of UI capabilities that the fast path can retrieve.

### What to build

- `data/capability_manifest.json` with at least 20 entries
- Each entry has: `capability_id`, `name`, `description` (natural language, used for embedding), `category`, `required_permissions` (list of real OpenProject permission names), and `ui_change` (the diff payload the widget will apply)
- Cover: time charts, view toggles, column visibility, widget placement
- `app/models/capability.py` Pydantic model plus a loader with validation
- Add the manifest entry contract to `CONTRACTS.md`
- Unit tests: manifest loads, rejects an entry with a missing field, ids are unique

### Definition of Done

- [ ] 3 unit tests pass in CI
- [ ] All `required_permissions` values checked against real permission names from `GET /api/v3/roles/:id`
- [ ] `CONTRACTS.md` updated

### Acceptance Criteria

- 20 or more entries, each with a distinct and well-written description
- At least 4 entries require elevated permissions, so governance has something to block in Sprint 3

---

## T2.4 — Sentence Transformer embeddings and FAISS index

**Epic:** fast-path | **Type:** feature | **Priority:** high
**Suggested owner:** Member A | **Effort:** Large | **Branch:** feature/T2.4-faiss-index
**Depends on:** T2.3

### Description

Embed the manifest and build a similarity index for top-k retrieval.

### What to build

- `app/services/retrieval_service.py`
- Embed each manifest `description` with a Sentence Transformers model (e.g. `all-MiniLM-L6-v2`)
- Persist vectors and the FAISS index to disk (`data/index/`), rebuilt via a script `scripts/build_index.py`
- Cosine similarity (normalized vectors with an inner-product index)
- `retrieve(query: str, k: int = 5) -> list[ScoredCapability]`; load the index once at startup
- Unit tests: a known query returns the expected capability in the top 3, k is respected, an empty index is handled

### Definition of Done

- [ ] 3 unit tests pass in CI
- [ ] `scripts/build_index.py` runs from a fresh clone
- [ ] Retrieval of 5 sample queries checked by hand

### Acceptance Criteria

- The index is not rebuilt on every request
- Scores are returned with each result
- Embedding model name is configurable

---

## T2.5 — Role/permission post-filter and confidence threshold

**Epic:** fast-path | **Type:** feature | **Priority:** high
**Suggested owner:** Member B | **Effort:** Medium | **Branch:** feature/T2.5-filter-threshold
**Depends on:** T2.4, Sprint 1 T1.5

### Description

Filter retrieved capabilities by the user's permissions and decide whether the match is confident enough.

### What to build

- Post-filter: drop capabilities whose `required_permissions` are not a subset of the user's `PermissionSet` (from `get_user_permissions`)
- Confidence threshold read from env var `FAST_PATH_THRESHOLD` (default 0.80)
- `fast_path_lookup(intent, permission_set) -> FastPathResult` with status `hit`, `low_confidence` or `permission_filtered`, plus the capability and score when present
- Unit tests: hit, below threshold, all results filtered out, threshold changed via env

### Definition of Done

- [ ] 4 unit tests pass in CI
- [ ] Same query returns a hit for an admin and a filtered/miss result for a viewer on the local OpenProject

### Acceptance Criteria

- Filtering is applied after retrieval and before the threshold check
- Threshold is not hard-coded
- Result type is documented in `CONTRACTS.md`

---

## T2.6 — Wire POST /intent end to end, session creation and routing stub

**Epic:** routing | **Type:** feature | **Priority:** high
**Suggested owner:** Member C | **Effort:** Large | **Branch:** feature/T2.6-intent-pipeline
**Depends on:** T2.1, T2.2, T2.5

### Description

Replace the Sprint 1 stub so `POST /intent` runs the real pipeline, and give the widget a way to obtain a session.

### What to build

- `POST /session`: resolves the current OpenProject user through `OpenProjectClient` (`/api/v3/users/me`), creates a session, returns `session_id`
- `POST /intent` now runs: session lookup → permissions → normalize → fast-path lookup → response
- `app/services/router.py`: a `route(intent, permission_set)` function that tries the fast path first; on `low_confidence` it returns a "slow path not available yet" placeholder (the slow path is wired in Sprint 3)
- Response body: `{"status": "ok" | "fallback" | "rejected", "intent": {...}, "capability": {...} | null, "message": "..."}`
- Update the Sprint 1 integration tests and add new ones for each status

### Definition of Done

- [ ] Integration tests pass in CI, with Gemini and OpenProject mocked
- [ ] Manual curl: session → intent returns a capability for an admin
- [ ] Response contract added to `CONTRACTS.md`

### Acceptance Criteria

- Each pipeline stage's failure maps to the correct HTTP status via the global handler
- Latency per stage is logged

---

## T2.7 — Chat widget embedded in OpenProject

**Epic:** intent-widget | **Type:** feature | **Priority:** high
**Suggested owner:** Member A | **Effort:** Large | **Branch:** feature/T2.7-widget-embed

### Description

Create the in-product chat widget that captures intent.

### What to build

- Self-contained widget (vanilla JS or a small bundle) under `widget/`: floating button, chat panel, input box, submit button, message list
- Injection into OpenProject via a custom script/plugin method (document the exact method in `ENVIRONMENT_NOTES.md`)
- Widget calls `POST /session` on load and keeps `session_id` in memory
- BFF base URL configurable; CORS enabled on the BFF for the OpenProject origin

### Definition of Done

- [ ] Widget appears on a real OpenProject page on all three members' machines
- [ ] Typing and submitting adds a message to the panel
- [ ] Injection steps written in `ENVIRONMENT_NOTES.md`

### Acceptance Criteria

- Does not break OpenProject's own UI
- Widget code is not coupled to a specific page

---

## T2.8 — Widget to BFF integration and response rendering

**Epic:** intent-widget | **Type:** feature | **Priority:** high
**Suggested owner:** Member B | **Effort:** Medium | **Branch:** feature/T2.8-widget-bff
**Depends on:** T2.6, T2.7

### Description

Connect the widget to the BFF and show results to the user.

### What to build

- Submit sends `{session_id, raw_text}` to `POST /intent`, with a loading indicator
- Render by status: `ok` shows the capability name and description, `fallback` shows the rephrase message, `rejected` shows the reason
- Network errors and an expired session (401) are handled; on 401 the widget requests a new session and retries once

### Definition of Done

- [ ] Demo: typing "show a chart of work over time" displays a capability in the widget
- [ ] Demo: gibberish shows the fallback message
- [ ] Error states checked by stopping the BFF

### Acceptance Criteria

- The user never sees raw JSON or a stack trace
- The input is disabled while a request is in flight

---

## T2.9 — Spike: threshold tuning and fast-path benchmark

**Epic:** fast-path | **Type:** spike | **Priority:** medium
**Suggested owner:** Member C | **Effort:** Small (2 days max) | **Branch:** feature/T2.9-threshold-spike
**Depends on:** T2.4, T2.5

### Description

Find a defensible confidence threshold and produce the first latency and accuracy numbers for the mid-defense.

### What to build

- Run the 18-case harness plus at least 30 extra phrasings at thresholds 0.75, 0.80, 0.85
- Record: correct-hit rate, wrong-hit rate, fallback rate, and retrieval latency (P1 and Pmax)
- Output: `docs/spikes/spike-1-fast-path-threshold.md` with question, approach, results table, conclusion, recommended threshold

### Definition of Done

- [ ] Note committed to `docs/spikes/`
- [ ] `FAST_PATH_THRESHOLD` default updated if the result justifies it
- [ ] Results table is ready to paste into a mid-defense slide

### Acceptance Criteria

- Numbers come from actual runs, not estimates
- The recommended threshold is justified by the trade-off

---

**Sprint 2 review:** Dec 9. Demo: widget → intent → capability, plus the benchmark table.

# Sprint 3 Issues (Copy to GitHub UI)

---

## T3.1 — Schema validation and safety classification

**Epic:** governance | **Type:** feature | **Priority:** high
**Suggested owner:** Member B | **Effort:** Medium | **Branch:** feature/T3.1-schema-safety

### Description

First two governance gates: structural validity and safety.

### What to build

- `app/services/governance_service.py`
- Gate 1: validate the proposed capability/diff against a JSON schema (`schemas/diff.json`, create it) before any permission check
- Gate 2: rule-based safety classifier that flags destructive or out-of-scope actions (delete, bulk update outside the user's project scope, unknown action types)
- Each gate returns `GateResult(passed: bool, reason: str)`
- Unit tests: valid diff passes both, malformed diff fails gate 1, destructive action fails gate 2

### Definition of Done

- [ ] 5 or more unit tests pass in CI
- [ ] `schemas/diff.json` and gate contract added to `CONTRACTS.md`

### Acceptance Criteria

- Gates run in a fixed order (schema → safety)
- Rejection reasons are specific enough to show to the user

---

## T3.2 — RBAC check and rejection fallback

**Epic:** governance | **Type:** feature | **Priority:** high
**Suggested owner:** Member C | **Effort:** Medium | **Branch:** feature/T3.2-rbac-reject
**Depends on:** T3.1

### Description

Final governance gate and the user-facing rejection behaviour.

### What to build

- Gate 3: compare the capability's `required_permissions` with the user's `PermissionSet` (re-checked here even though the fast path filters, so governance is the single source of truth)
- `govern(proposal, permission_set) -> GovernanceDecision` combining all three gates, with `approved` or `rejected` plus reasons
- On rejection: nothing is stored; the response is `status: "rejected"` with a plain-language message
- Unit tests: admin approved, viewer rejected for an elevated capability, rejected proposal produces no side effects

### Definition of Done

- [ ] 4 or more unit tests pass in CI
- [ ] Manual check with a real admin and a real viewer on local OpenProject

### Acceptance Criteria

- Approval requires all three gates to pass
- Rejection is logged with user, capability and reason

---

## T3.3 — PostgreSQL schema and docker-compose

**Epic:** diff-store | **Type:** feature | **Priority:** high
**Suggested owner:** Member A | **Effort:** Medium | **Branch:** feature/T3.3-postgres-schema

### Description

Database foundation for versioned diffs.

### What to build

- `docker-compose.yml` with PostgreSQL for local development; `DATABASE_URL` from config
- Migrations (Alembic) creating: `versions` (`version_id`, `parent_id`, `user_id`, `project_id`, `is_active`, `created_at`), `diffs` (`diff_id`, `version_id`, `payload` JSONB), `audit_log` (`user_id`, `project_id`, `action`, `version_id`, `timestamp`)
- Async DB session dependency (SQLAlchemy or asyncpg)
- Document the schema and the version-chain rule in `ARCHITECTURE.md` or an ADR

### Definition of Done

- [ ] `docker compose up` plus the migration command works from a fresh clone on all three machines
- [ ] Schema tests pass in CI (Postgres service container in the workflow)
- [ ] ADR committed

### Acceptance Criteria

- Exactly one active version per user and project, enforced
- Migrations are repeatable

---

## T3.4 — Diff write endpoint and audit trail

**Epic:** diff-store | **Type:** feature | **Priority:** high
**Suggested owner:** Member B | **Effort:** Medium | **Branch:** feature/T3.4-diff-write-audit
**Depends on:** T3.3

### Description

Persist approved diffs as new versions and make history queryable.

### What to build

- `POST /diffs`: stores an approved diff as a new version whose parent is the current active version, marks it active, writes an audit row, returns `version_id`
- `GET /diffs/audit?user_id=&project_id=`: chronological list of audit entries
- `GET /diffs/active?user_id=&project_id=`: returns the active version's diff chain (the widget uses this on load to restore state)
- Integration tests for each endpoint, including parent/active pointer behaviour

### Definition of Done

- [ ] 5 or more integration tests pass in CI
- [ ] Three sequential writes show a correct parent chain in the DB

### Acceptance Criteria

- Writes are transactional (version, diff and audit row succeed or fail together)
- Contracts in `CONTRACTS.md`

---

## T3.5 — Rollback endpoint and undo button

**Epic:** diff-store | **Type:** feature | **Priority:** high
**Suggested owner:** Member C | **Effort:** Medium | **Branch:** feature/T3.5-rollback
**Depends on:** T3.4

### Description

Make every change reversible, from the API to the widget.

### What to build

- `POST /diffs/:version_id/rollback`: sets the parent version active, writes an audit row of type `rollback`
- Rolling back the root version returns the default (no-diff) state
- Widget undo button calling the endpoint and updating the UI state
- Integration tests: rollback restores the prior version, rolling back the root, a non-existent version returns 404

### Definition of Done

- [ ] 3 or more integration tests pass in CI
- [ ] Live demo: apply a change, press undo, UI returns to the previous state

### Acceptance Criteria

- Rollback never deletes history
- Audit trail shows the rollback

---

## T3.6 — Pipeline integration: governance and diff store into /intent

**Epic:** integration | **Type:** feature | **Priority:** high
**Suggested owner:** Member A | **Effort:** Large | **Branch:** feature/T3.6-pipeline-integration
**Depends on:** T3.2, T3.4

### Description

Connect every component into one flow.

### What to build

- Extend the router so `POST /intent` runs: normalize → fast path → governance → (approved) store diff → respond
- Response includes `version_id` and the `ui_change` payload for the widget to apply
- Rejected and fallback paths remain side-effect free
- Integration tests across the whole flow with Gemini mocked and a real test DB

### Definition of Done

- [ ] Full-flow integration tests pass in CI (approved, rejected, fallback)
- [ ] One real intent traverses the real pipeline locally and a row appears in the DB
- [ ] `CONTRACTS.md` reflects the final response shape

### Acceptance Criteria

- No component is bypassed
- Failure in any stage returns a standard error body

---

## T3.7 — Widget applies approved diffs and restores state

**Epic:** intent-widget | **Type:** feature | **Priority:** high
**Suggested owner:** Member B | **Effort:** Large | **Branch:** feature/T3.7-widget-apply-diff
**Depends on:** T3.6

### Description

The visible part of the demo: the OpenProject UI actually changes.

### What to build

- Widget interprets `ui_change` for at least 4 change types (e.g. toggle column visibility, show/hide a chart panel, switch view, move a widget)
- Calls `GET /diffs/active` on load and re-applies the active version so changes persist across refreshes
- Shows the applied change description and the version in the chat panel

### Definition of Done

- [ ] Live demo of 4 distinct UI changes in OpenProject
- [ ] Refresh keeps the change; undo removes it
- [ ] Rejected request shows the reason, with no UI change

### Acceptance Criteria

- Unknown change types are ignored safely and reported, not crashed on
- No full page reload is needed to apply a change

---

## T3.8 — Minimal slow path (stretch)

**Epic:** slow-path | **Type:** feature | **Priority:** low
**Suggested owner:** Member C | **Effort:** Large | **Branch:** feature/T3.8-slow-path-min
**Depends on:** T3.6

### Description

Prove the capability-gap fallback with a small agent loop. Drop this first if the sprint is behind.

### What to build

- On a fast-path `low_confidence` miss, call Gemini with tools `get_manifest_entry` and `synthesize_component`, capped at `MAX_RETRIES=3`
- Output normalized to the same proposal structure as the fast path, then sent through governance like everything else
- If the loop fails, return the standard fallback message
- Unit tests with the model mocked: success, retry then success, cap reached

### Definition of Done

- [ ] 3 unit tests pass in CI
- [ ] One request that the fast path misses is handled by the slow path and passes governance
- [ ] If not finished: move to the next sprint and document the status honestly in the mid-defense slides

### Acceptance Criteria

- Output is structurally identical to the fast-path output
- Slow path can never bypass governance

---

## T3.9 — End-to-end tests, permission-violation test and demo script

**Epic:** integration | **Type:** feature | **Priority:** high
**Suggested owner:** Member A | **Effort:** Medium | **Branch:** feature/T3.9-e2e-demo

### Description

Prove the MVP works and rehearse the mid-defense demonstration.

### What to build

- E2E tests against the real local OpenProject: fast-path approved and stored, permission violation blocked, rollback restores state
- Re-run the 18-case harness through the full pipeline and record accuracy and latency
- `docs/DEMO_SCRIPT.md`: ordered demo steps with the exact phrases to type, one admin and one viewer account, and a fallback plan if Gemini or the network fails
- Full dry run with all three members at least once before the sprint review

### Definition of Done

- [ ] E2E tests pass locally (documented how to run them)
- [ ] Results table (accuracy, latency, permission-violation outcomes) committed in `docs/`
- [ ] Dry run completed and timed

### Acceptance Criteria

- The demo works with no manual fixes mid-run
- Every number on the mid-defense slides traces back to a committed result

---

**Sprint 3 review:** Dec 23. Demo: the full MVP flow, plus the results table.
