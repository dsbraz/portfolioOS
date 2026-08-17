"""Contract guards for the public reporting zone (RFC-001 §3.4 and §6).

RFC-001 adds no endpoint and no schema change; it reaffirms the contract that
already holds and pins it here, so a field added to one side only breaks a test
instead of quietly widening what an investee can write.
"""

from app.domain.schemas.monthly_indicator import (
    MonthlyIndicatorBase,
    PublicIndicatorData,
    PublicIndicatorSubmit,
)

# `comments` is the fund's own note; `month`/`year` come from the token.
ADMIN_ONLY_FIELDS = {"comments", "month", "year"}


def test_public_submit_covers_exactly_the_reportable_zone():
    assert set(PublicIndicatorSubmit.model_fields) == (
        set(MonthlyIndicatorBase.model_fields) - ADMIN_ONLY_FIELDS
    )


def test_public_schemas_never_carry_the_fund_note():
    assert "comments" not in PublicIndicatorSubmit.model_fields
    assert "comments" not in PublicIndicatorData.model_fields


def test_public_submit_keeps_the_admin_limits_for_every_shared_field():
    """A limit relaxed on one side only is how a -999 billion value reached the
    database before; the two schemas must constrain each field identically."""
    for name, public_field in PublicIndicatorSubmit.model_fields.items():
        admin_field = MonthlyIndicatorBase.model_fields[name]
        assert public_field.annotation == admin_field.annotation, (
            f"{name}: type differs between the public and admin schemas"
        )
        assert [str(m) for m in public_field.metadata] == [
            str(m) for m in admin_field.metadata
        ], f"{name}: constraints differ between the public and admin schemas"
