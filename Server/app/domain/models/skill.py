from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    version: str
    writes: bool
    reads_external: bool
    published: bool
    blocked_reason: str | None
    files: list[str] | None
