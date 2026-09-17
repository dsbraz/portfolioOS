import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.controllers.exception_handlers import register_exception_handlers
from app.domain.exceptions import ConflictError, InvalidInputError


def _app(seen: list[type[Exception]]) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    async def transaction():
        # Stands in for `get_session`, which rolls back when the request fails.
        try:
            yield
        except Exception as error:
            seen.append(type(error))
            raise

    raising = {
        "conflict": ConflictError("Ja existe"),
        "invalid": InvalidInputError("Periodo no futuro"),
        "bug": ValueError("invariante"),
    }

    @app.get("/{kind}", dependencies=[Depends(transaction)])
    async def route(kind: str):
        raise raising[kind]

    return app


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("kind", "status", "detail", "error"),
    [
        ("conflict", 409, "Ja existe", ConflictError),
        ("invalid", 400, "Periodo no futuro", InvalidInputError),
        # A plain ValueError is a bug, not bad input (Pydantic errors subclass it).
        ("bug", 500, None, ValueError),
    ],
)
async def test_domain_exceptions_map_to_status_after_the_transaction_saw_them(
    kind, status, detail, error
):
    seen: list[type[Exception]] = []
    transport = ASGITransport(app=_app(seen), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/{kind}")

    assert response.status_code == status
    if detail is not None:
        assert response.json() == {"detail": detail}
    assert seen == [error]
