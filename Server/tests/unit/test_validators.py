from datetime import date
from unittest.mock import patch

import pytest

from app.domain.validators import (
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
