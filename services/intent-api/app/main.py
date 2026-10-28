from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.routes.intent import router as intent_router


app = FastAPI()
app.include_router(intent_router)


@app.exception_handler(HTTPException)
async def handle_http_exception(_request, exception: HTTPException) -> JSONResponse:
    if isinstance(exception.detail, dict):
        content = exception.detail
    else:
        content = {
            "error": {
                "code": "HTTP_ERROR",
                "message": str(exception.detail),
            }
        }
    return JSONResponse(
        status_code=exception.status_code,
        content=content,
        headers=exception.headers,
    )