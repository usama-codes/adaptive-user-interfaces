# Adaptive UI Service

## Local setup

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
pre-commit install
cp adaptive_ui_service/.env.example adaptive_ui_service/.env
python -m scripts.build_index
uvicorn main:app --reload
```

The first index build downloads the configured Sentence Transformers model if it
is not cached locally. Set `EMBEDDING_MODEL_NAME` in
`adaptive_ui_service/.env` to select a different model. The generated index is
stored in `adaptive_ui_service/data/index/` and is not committed; rebuild it
after changing the capability manifest or model.

The service listens on `http://127.0.0.1:8000`. Verify it with:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","version":"0.1.0"}
```