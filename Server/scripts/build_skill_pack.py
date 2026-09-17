"""Build the committed `static/portfolioos.zip` from `skills/portfolioos/`.

The folder is already laid out as the uploaded package, so building is only
zipping it. Run after changing any skill, from `Server/`:

    python -m scripts.build_skill_pack
"""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

SERVER_DIR = Path(__file__).resolve().parent.parent
PACK_SOURCE_DIR = SERVER_DIR / "skills" / "portfolioos"
PACK_PATH = SERVER_DIR / "static" / "portfolioos.zip"

# Fixed timestamp and mode keep the archive identical across rebuilds, so a diff
# on the zip means the skills changed and nothing else.
_ENTRY_DATE_TIME = (2026, 1, 1, 0, 0, 0)
_ENTRY_MODE = 0o100644


def pack_entries() -> list[tuple[str, Path]]:
    """Archive name and source path of every packaged file, in archive order."""
    return sorted(
        (f"{PACK_SOURCE_DIR.name}/{path.relative_to(PACK_SOURCE_DIR).as_posix()}", path)
        for path in PACK_SOURCE_DIR.rglob("*")
        if path.is_file()
        and not any(
            part.startswith(".") or part == "__pycache__"
            for part in path.relative_to(PACK_SOURCE_DIR).parts
        )
    )


def build(output: Path = PACK_PATH) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for name, path in pack_entries():
            entry = ZipInfo(name, date_time=_ENTRY_DATE_TIME)
            entry.external_attr = _ENTRY_MODE << 16
            entry.compress_type = ZIP_DEFLATED
            archive.writestr(entry, path.read_bytes())


if __name__ == "__main__":
    build()
    print(f"Wrote {PACK_PATH.relative_to(SERVER_DIR)}")
