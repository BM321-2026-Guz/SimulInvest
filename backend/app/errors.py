from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """OpenAPI'deki Error şemasına ({code, message}) dönüşen uygulama hatası."""

    def __init__(
        self, status_code: int, code: str, message: str, headers: dict[str, str] | None = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers


def _error(
    status_code: int, code: str, message: str, headers: dict[str, str] | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"code": code, "message": message}, headers=headers
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return _error(exc.status_code, exc.code, exc.message, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(p) for p in first.get("loc", []) if p != "body")
        message = f"{field}: {first.get('msg', 'Geçersiz istek.')}" if field else "Geçersiz istek."
        return _error(400, "VALIDATION_ERROR", message)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException):
        return _error(exc.status_code, "HTTP_ERROR", str(exc.detail))
