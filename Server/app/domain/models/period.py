from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Period:
    """A reporting month. Field order (year, month) drives chronological ordering."""

    year: int
    month: int

    def __post_init__(self) -> None:
        if not 1 <= self.month <= 12:
            raise ValueError("Mes deve estar entre 1 e 12")

    @property
    def key(self) -> int:
        """Sortable integer encoding, e.g. Jul/2026 -> 202607."""
        return self.year * 100 + self.month

    @classmethod
    def from_key(cls, key: int) -> "Period":
        return cls(year=key // 100, month=key % 100)

    def previous(self) -> "Period":
        if self.month == 1:
            return Period(year=self.year - 1, month=12)
        return Period(year=self.year, month=self.month - 1)
