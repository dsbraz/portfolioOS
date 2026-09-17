from datetime import date

from app.domain.exceptions import InvalidInputError


def validate_period_not_future(month: int, year: int) -> None:
    today = date.today()
    if year > today.year or (year == today.year and month > today.month):
        raise InvalidInputError(f"Periodo {month}/{year} nao pode ser no futuro")


def validate_username_no_spaces(username: str) -> None:
    if " " in username:
        raise InvalidInputError("Username nao pode conter espacos")


# bcrypt reads at most 72 bytes; longer passwords would be silently cut.
PASSWORD_MAX_BYTES = 72


def validate_password_max_bytes(password: str) -> None:
    if len(password.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise InvalidInputError(f"Senha nao pode ter mais de {PASSWORD_MAX_BYTES} bytes")
