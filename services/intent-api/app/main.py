from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routes.intent import router as intent_router
from app.routes.session import router as session_router


app = FastAPI()
app.include_router(intent_router)
app.include_router(session_router)


@app.exception_handler(HTTPException)
async def handle_http_exception(_request, exception: HTTPException) -> JSONResponse:
    content = exception.detail if isinstance(exception.detail, dict) else {
        "error": {"code": "HTTP_ERROR", "message": str(exception.detail)}
    }
    return JSONResponse(status_code=exception.status_code, content=content, headers=exception.headers)


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(
    _request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exception.errors(),
            }
        },
    )
