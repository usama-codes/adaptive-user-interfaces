# Adaptive UI Service

## Local setup

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pre-commit install
cp adaptive_ui_service/.env.example adaptive_ui_service/.env
uvicorn main:app --reload
```

The service listens on `http://127.0.0.1:8000`. Verify it with:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","version":"0.1.0"}
```