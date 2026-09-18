"""Build the committed `static/portfolioos.zip` and its manifest from `skills/`.

The folder is already laid out as the uploaded package, so building the archive
is only zipping it. The manifest is what the `/ia` page lists: the published
guides, the workflows kept out, and the date the package content last changed.
Run after changing any skill, from `Server/`:

    python -m scripts.build_skill_pack
"""

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import yaml

SERVER_DIR = Path(__file__).resolve().parent.parent
# At the repository root, beside Client/ and Server/: the guides are product
# content shipped to an agent, not backend code. Only the built archive belongs
# to the server, and it still lands in `Server/static/`.
SKILLS_DIR = SERVER_DIR.parent / "skills"
PACK_SOURCE_DIR = SKILLS_DIR / "portfolioos"
UNPUBLISHED_DIR = SKILLS_DIR / "unpublished"
PACK_PATH = SERVER_DIR / "static" / "portfolioos.zip"
MANIFEST_PATH = SERVER_DIR / "static" / "portfolioos-manifest.json"

# What the guides' frontmatter cannot carry: upload validators accept only `name`
# and `description` there. The order is the order the `/ia` page lists them in.
PUBLISHED: dict[str, dict[str, Any]] = {
    "operar-portfolioos": {
        "title": "Operar toda a plataforma",
        "writes": True,
        "reads_external": True,
    },
    "preparar-agenda": {
        "title": "Preparar agenda de uma startup",
        "writes": False,
        "reads_external": True,
    },
    "granola-reuniao": {
        "title": "Registrar reunião de conselho",
        "writes": True,
        "reads_external": True,
    },
    "cobrar-indicadores": {
        "title": "Cobrar indicadores em falta",
        "writes": True,
        "reads_external": True,
    },
    "apresentacao-portfolio": {
        "title": "Apresentar o portfólio",
        "writes": False,
        "reads_external": True,
    },
}
UNPUBLISHED: dict[str, dict[str, Any]] = {
    "auditoria-qualitativa": {
        "title": "Auditar o portfólio",
        "writes": False,
        "reads_external": True,
        "reason": (
            "Aguardando aprovação da política de trânsito de dados. "
            "Até lá, use apenas com dados de demonstração."
        ),
    },
}

# Fixed timestamp and mode keep the archive identical across rebuilds, so a diff
# on the zip means the skills changed and nothing else.
_ENTRY_DATE_TIME = (2026, 1, 1, 0, 0, 0)
_ENTRY_MODE = 0o100644


def read_frontmatter(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---", maxsplit=2)[1])


def guide_path(name: str) -> Path:
    return PACK_SOURCE_DIR / "skills" / name / "GUIDE.md"


def unpublished_path(name: str) -> Path:
    return UNPUBLISHED_DIR / name / "SKILL.md"


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


def content_digest() -> str:
    """Hash of the packaged files, independent of how the zip compresses them."""
    digest = hashlib.sha256()
    for name, path in pack_entries():
        digest.update(name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def build_manifest(revised_at: str) -> dict[str, Any]:
    def entry(name: str, path: Path, extra: dict[str, Any]) -> dict[str, Any]:
        return {"name": name, "description": read_frontmatter(path)["description"], **extra}

    return {
        "revised_at": revised_at,
        "content_sha256": content_digest(),
        "published": [
            entry(name, guide_path(name), {"title": meta["title"], "writes": meta["writes"]})
            for name, meta in PUBLISHED.items()
        ],
        "unpublished": [
            entry(name, unpublished_path(name), {"title": meta["title"], "reason": meta["reason"]})
            for name, meta in UNPUBLISHED.items()
        ],
    }


def _revised_at() -> str:
    """Keep the committed date while the content is unchanged; today otherwise."""
    if MANIFEST_PATH.exists():
        committed = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if committed["content_sha256"] == content_digest():
            return committed["revised_at"]
    return date.today().isoformat()


def build() -> None:
    PACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(PACK_PATH, "w", compression=ZIP_DEFLATED) as archive:
        for name, path in pack_entries():
            entry = ZipInfo(name, date_time=_ENTRY_DATE_TIME)
            entry.external_attr = _ENTRY_MODE << 16
            entry.compress_type = ZIP_DEFLATED
            archive.writestr(entry, path.read_bytes())

    manifest = build_manifest(_revised_at())
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    build()
    print(f"Wrote {PACK_PATH.relative_to(SERVER_DIR)} and {MANIFEST_PATH.name}")
