from datetime import date


def validate_period_not_future(month: int, year: int) -> None:
    today = date.today()
    if year > today.year or (year == today.year and month > today.month):
        raise ValueError(f"Periodo {month}/{year} nao pode ser no futuro")


def validate_username_no_spaces(username: str) -> None:
    if " " in username:
        raise ValueError("Username nao pode conter espacos")
