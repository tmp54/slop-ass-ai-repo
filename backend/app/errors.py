"""One error shape for every failure: {"error": {"code", "message", "details"}}."""

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.ai.interface import AIPipelineError
from app.state_machine import ForbiddenActor, InvalidTransition


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def _response(status: int, code: str, message: str, details=None) -> JSONResponse:
    body = {"error": {"code": code, "message": message, "details": jsonable_encoder(details)}}
    return JSONResponse(status_code=status, content=body)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api(_: Request, exc: ApiError):
        return _response(exc.status, exc.code, exc.message)

    @app.exception_handler(ForbiddenActor)
    async def _forbidden(_: Request, exc: ForbiddenActor):
        return _response(403, "forbidden_role", str(exc))

    @app.exception_handler(InvalidTransition)
    async def _invalid(_: Request, exc: InvalidTransition):
        return _response(409, "invalid_transition", str(exc))

    @app.exception_handler(AIPipelineError)
    async def _ai(_: Request, exc: AIPipelineError):
        return _response(502, "ai_unavailable", str(exc) or "AI pipeline failed")

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        return _response(422, "validation_error", "Request validation failed", exc.errors())

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        code = "not_found" if exc.status_code == 404 else "http_error"
        return _response(exc.status_code, code, str(exc.detail))
