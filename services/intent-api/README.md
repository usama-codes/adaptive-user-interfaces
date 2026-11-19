# Intent API

Standalone FastAPI service for creating sessions and receiving raw user intent text.

## Run

```bash
cd services/intent-api
python3 -m pip install -e '.[dev]'
python3 -m uvicorn app.main:app --reload
```

Create a session for manual testing:

```bash
curl -X POST http://127.0.0.1:8000/sessions \
  -H 'Content-Type: application/json' \
  -d '{"user_id":42}'
```

Submit intent text with the returned `session_id`:

```bash
curl -i -X POST http://127.0.0.1:8000/intent \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"<session-id>","raw_text":"Create a project plan"}'
```

## Test

```bash
python3 -m pytest -q
```

Sessions are process-local and expire after 30 minutes of inactivity.
