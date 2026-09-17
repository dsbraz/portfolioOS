class ConflictError(Exception):
    """Raised when an operation conflicts with existing state."""


class InvalidInputError(ValueError):
    """Raised when input breaks a business rule.

    A plain `ValueError` stays reserved for invariants (e.g. `Period`): reaching
    one means a bug, not bad input.
    """
