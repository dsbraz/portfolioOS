from datetime import date
from unittest.mock import patch

import pytest

from app.domain.validators import (
    normalize_contact_email,
    normalize_international_phone,
    validate_period_not_future,
    validate_username_no_spaces,
)


def test_current_month_is_valid():
    today = date.today()
    validate_period_not_future(today.month, today.year)


def test_past_month_is_valid():
    validate_period_not_future(1, 2020)


def test_future_month_same_year_raises():
    with patch("app.domain.validators.date") as mock_date:
        mock_date.today.return_value = date(2026, 2, 15)
        with pytest.raises(ValueError, match="futuro"):
            validate_period_not_future(3, 2026)


def test_future_year_raises():
    with pytest.raises(ValueError, match="futuro"):
        validate_period_not_future(1, 2099)


def test_december_of_past_year_is_valid():
    validate_period_not_future(12, 2024)


def test_username_without_space_is_valid():
    validate_username_no_spaces("valid_username")


def test_username_with_space_raises():
    with pytest.raises(ValueError, match="Username"):
        validate_username_no_spaces("invalid user")


# --- Phone: the country prefix is mandatory (product decision, 2026-08-19) ---
#
# The fund's executives are not all in Brazil, so the number cannot be guessed
# from its length. Requiring the prefix is what makes the stored value
# unambiguous — and it is what stops a local-format foreign number from being
# read as a Brazilian one.


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("+55 11 91234-5678", "+5511912345678"),
        ("+351 912 345 678", "+351912345678"),
        ("+1 415 555 1234", "+14155551234"),
        ("+44 20 7946 0958", "+442079460958"),
        # Separators, parentheses and non-breaking spaces are presentation only.
        ("+55 (11) 91234-5678", "+5511912345678"),
    ],
)
def test_international_phone_is_normalized_to_e164(raw, expected):
    assert normalize_international_phone(raw) == expected


def test_absent_phone_stays_absent():
    assert normalize_international_phone(None) is None
    assert normalize_international_phone("") is None
    assert normalize_international_phone("   ") is None


@pytest.mark.parametrize(
    "raw",
    [
        "11 91234-5678",  # Brazilian, no prefix
        "(415) 555-1234",  # foreign in local format — the dangerous one
        "912345678",
        "0055 11 91234-5678",  # international access code is not a prefix
    ],
)
def test_phone_without_country_prefix_raises(raw):
    with pytest.raises(ValueError, match="código do país"):
        normalize_international_phone(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "+55",  # prefix alone
        "+1234",  # too short to be a real subscriber line
        "+55119123456789012",  # beyond E.164's 15 digits
        "+abc",
    ],
)
def test_phone_that_is_not_a_valid_e164_number_raises(raw):
    with pytest.raises(ValueError, match="[Tt]elefone"):
        normalize_international_phone(raw)


# --- Contact e-mail: the fallback channel when WhatsApp is not available ---
#
# The e-mail is an address the product will compose a message to, so it is
# validated at registration for the same reason the phone is: an address that
# cannot be reached is better refused than discovered at send time.


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("ana@startup.com.br", "ana@startup.com.br"),
        ("  Ana@Startup.com.br  ", "ana@startup.com.br"),
        ("john.miller+fundo@example.co.uk", "john.miller+fundo@example.co.uk"),
    ],
)
def test_contact_email_is_normalized(raw, expected):
    assert normalize_contact_email(raw) == expected


def test_absent_contact_email_stays_absent():
    assert normalize_contact_email(None) is None
    assert normalize_contact_email("") is None
    assert normalize_contact_email("   ") is None


@pytest.mark.parametrize(
    "raw",
    [
        "ana arroba startup",
        "ana@",
        "@startup.com",
        "ana@startup",
        "ana @startup.com",
        "ana@@startup.com",
    ],
)
def test_invalid_contact_email_raises(raw):
    with pytest.raises(ValueError, match="[Ee]-?mail"):
        normalize_contact_email(raw)
