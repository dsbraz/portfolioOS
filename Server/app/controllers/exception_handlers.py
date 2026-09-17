"""Map domain exceptions to HTTP responses once, for every route.

Controllers let `InvalidInputError` and `ConflictError` propagate. The request's
session dependency sees the exception first and rolls back; only then does the
handler answer, with the same `{"detail": ...}` body an `HTTPException` produces.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions import ConflictError, InvalidInputError


async def _invalid_input(_: Request, error: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(error)})


async def _conflict(_: Request, error: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(error)})


def register_exception_handlers(app: FastAPI) -> None:
    # No handler for plain ValueError: Pydantic's ValidationError subclasses it.
    app.add_exception_handler(InvalidInputError, _invalid_input)
    app.add_exception_handler(ConflictError, _conflict)
