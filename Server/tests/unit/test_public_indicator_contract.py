"""Contract guards for the public reporting zone (RFC-001 §3.4 and §6).

RFC-001 adds no endpoint and no schema change; it reaffirms the contract that
already holds and pins it here, so a field added to one side only breaks a test
instead of quietly widening what an investee can write.
"""

from app.domain.schemas.monthly_indicator import (
    MonthlyIndicatorBase,
    MonthlyIndicatorUpdate,
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


def _bounds(model: type, name: str) -> dict[str, object]:
    """Numeric bounds a field enforces, wherever pydantic stores them."""
    schema = model.model_json_schema()["properties"][name]
    variants = schema.get("anyOf", [schema])
    return {
        key: value
        for variant in variants
        for key, value in variant.items()
        if key in {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"}
    }


def test_public_submit_keeps_the_admin_limits_for_every_shared_field():
    """A limit relaxed on one side only is how a -999 billion value reached the
    database before; the two schemas must constrain each field identically."""
    for name in PublicIndicatorSubmit.model_fields:
        assert _bounds(PublicIndicatorSubmit, name) == _bounds(
            MonthlyIndicatorBase, name
        ), f"{name}: constraints differ between the public and admin schemas"


def test_update_keeps_the_create_limits_for_every_field():
    """An edit is another way in; it must not accept what creation refuses."""
    assert set(MonthlyIndicatorUpdate.model_fields) == set(MonthlyIndicatorBase.model_fields)
    for name in MonthlyIndicatorUpdate.model_fields:
        assert _bounds(MonthlyIndicatorUpdate, name) == _bounds(
            MonthlyIndicatorBase, name
        ), f"{name}: constraints differ between the create and update schemas"


def test_bounds_helper_sees_the_limits():
    # Guards the guards: an empty result would make both checks above vacuous.
    assert _bounds(MonthlyIndicatorBase, "headcount") == {
        "minimum": 0,
        "maximum": 2_147_483_647,
    }
