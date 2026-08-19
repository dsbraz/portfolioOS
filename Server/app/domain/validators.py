import re
from datetime import date

# E.164: a leading "+", then 8 to 15 digits (country code included). The lower
# bound rejects a bare prefix or a stub; the upper bound is the standard's.
_E164 = re.compile(r"^\+\d{8,15}$")

# Separators people type. Everything else — including a leading "00" access
# code — is refused rather than repaired, because repairing means guessing.
_PHONE_SEPARATORS = re.compile(r"[\s ().\-/]")


def normalize_international_phone(value: str | None) -> str | None:
    """Normalizes a registered phone to E.164, requiring the country prefix.

    The fund's executives are not all in Brazil, so a number's country cannot be
    inferred from its length: a 10-digit foreign number in local format is
    indistinguishable from a Brazilian one. Demanding the "+" prefix is what
    keeps the stored value unambiguous — and an indicator link is write access
    to a period, so sending it to a misread number hands that write to a
    stranger.

    Absence stays absence (`None`); anything present must be a valid E.164
    number or the call raises `ValueError`.
    """
    if value is None:
        return None

    stripped = value.strip()
    if not stripped:
        return None

    candidate = _PHONE_SEPARATORS.sub("", stripped)

    if not candidate.startswith("+"):
        raise ValueError(
            "Telefone deve incluir o código do país, começando com + "
            "(ex.: +55 11 91234-5678)"
        )

    if not _E164.match(candidate):
        raise ValueError(
            "Telefone invalido: informe um numero E.164 valido, "
            "com codigo do pais e de 8 a 15 digitos"
        )

    return candidate


def validate_period_not_future(month: int, year: int) -> None:
    today = date.today()
    if year > today.year or (year == today.year and month > today.month):
        raise ValueError(f"Periodo {month}/{year} nao pode ser no futuro")


def validate_username_no_spaces(username: str) -> None:
    if " " in username:
        raise ValueError("Username nao pode conter espacos")
