# Intent API

Standalone FastAPI service for receiving user intent text. It currently validates the request and session, then returns a placeholder response until normalization is implemented.

## Run

From this directory, install the development dependencies and start the service:

```bash
python3 -m pip install -e '.[dev]'
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Run tests with `pytest`.

The session store is process-local and in-memory. It is suitable for the current single-process development service; multiple worker processes will have independent session stores.