import logging

import uvicorn
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

import v1
from entities import BaseResponse
from entities.errors import (
    AlreadyTakenError,
    APIError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from settings import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    separate_input_output_schemas=False,
)


app.include_router(v1.router, prefix="/v1")


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"message": exc.message})


@app.exception_handler(AlreadyTakenError)
async def already_taken_exception_handler(request: Request, exc: AlreadyTakenError):
    return JSONResponse(status_code=403, content={"message": exc.message})


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(status_code=401, content={"message": exc.message})


@app.exception_handler(ForbiddenError)
async def forbidden_error_handler(request: Request, exc: ForbiddenError):
    return JSONResponse(status_code=403, content={"message": exc.message})


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    logger.warning(
        "APIError 503 path=%s message=%s",
        request.url.path,
        exc.message,
    )
    return JSONResponse(status_code=503, content={"message": exc.message})


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=400, content={"message": exc.message})


@app.get("/", response_model=BaseResponse)
async def root() -> BaseResponse:
    return BaseResponse(message="ok")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        reload=True,
    )
