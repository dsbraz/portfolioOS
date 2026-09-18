import json
import re
from datetime import date
from pathlib import PurePosixPath
from zipfile import ZipFile

import scripts.build_skill_pack as build_skill_pack
from scripts.build_skill_pack import (
    MANIFEST_PATH,
    PACK_PATH,
    PACK_SOURCE_DIR,
    PUBLISHED,
    UNPUBLISHED,
    UNPUBLISHED_DIR,
    build_manifest,
    guide_path,
    pack_entries,
    read_frontmatter,
)

LINK_PATTERN = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


def _committed_pack() -> dict[str, bytes]:
    with ZipFile(PACK_PATH) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def test_committed_pack_matches_the_source_folder():
    # The zip is committed, so a change to a skill without rebuilding it would
    # ship stale instructions. Run `python -m scripts.build_skill_pack`.
    expected = {name: path.read_bytes() for name, path in pack_entries()}

    assert _committed_pack() == expected


def test_pack_has_exactly_one_skill_entrypoint_at_its_root():
    # Claude and ChatGPT reject an archive holding more than one SKILL.md.
    entrypoints = [
        name for name in _committed_pack() if PurePosixPath(name).name == "SKILL.md"
    ]

    assert entrypoints == ["portfolioos/SKILL.md"]


def test_pack_ships_openai_metadata_beside_the_entrypoint():
    # OpenAI reads `<dir holding SKILL.md>/agents/openai.yaml`; elsewhere it is ignored.
    names = set(_committed_pack())

    assert "portfolioos/agents/openai.yaml" in names
    assert not any(
        name.endswith("agents/openai.yaml") and name != "portfolioos/agents/openai.yaml"
        for name in names
    )


def test_unpublished_skills_stay_out_of_the_pack():
    assert not any("auditoria-qualitativa" in name for name in _committed_pack())


def test_entrypoint_index_lists_every_bundled_guide():
    wrapper = (PACK_SOURCE_DIR / "SKILL.md").read_text(encoding="utf-8")
    guides = sorted(
        path.relative_to(PACK_SOURCE_DIR).as_posix()
        for path in PACK_SOURCE_DIR.glob("skills/*/GUIDE.md")
    )
    indexed = sorted(
        link for link in LINK_PATTERN.findall(wrapper) if link.endswith("GUIDE.md")
    )

    assert guides
    assert indexed == guides


def test_entrypoint_index_repeats_each_guide_description_verbatim():
    """The index is the routing surface; a stale copy sends the agent elsewhere.

    Each line restates the guide's own frontmatter `description`, and nothing
    regenerates it — so a guide whose purpose changed kept advertising the old
    one, which is how `preparar-agenda` went on promising a brief built from
    the platform after it had been rewritten to start from the conversation.
    The manifest derives the same text from the same place, so the three copies
    must agree.
    """
    wrapper = (PACK_SOURCE_DIR / "SKILL.md").read_text(encoding="utf-8")
    for name in PUBLISHED:
        descricao = read_frontmatter(guide_path(name))["description"]
        linha = f"- [`{name}`](skills/{name}/GUIDE.md): {descricao}"
        assert linha in wrapper, f"índice desatualizado para {name}"


def test_every_relative_link_in_the_pack_resolves():
    for path in PACK_SOURCE_DIR.rglob("*.md"):
        for link in LINK_PATTERN.findall(path.read_text(encoding="utf-8")):
            if "://" in link:
                continue
            assert (path.parent / link).is_file(), f"{path}: broken link {link}"


def test_guides_keep_the_standard_frontmatter():
    for guide in PACK_SOURCE_DIR.glob("skills/*/GUIDE.md"):
        frontmatter = guide.read_text(encoding="utf-8").split("---", maxsplit=2)[1]
        fields = {
            line.split(":", maxsplit=1)[0].strip()
            for line in frontmatter.splitlines()
            if line.strip()
        }
        assert fields == {"name", "description"}
        assert f"name: {guide.parent.name}" in frontmatter


def test_committed_manifest_matches_the_source():
    # The `/ia` page lists the package from this file, so it goes stale exactly
    # like the zip does. Rebuilding also moves `revised_at` when content changed.
    committed = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert committed == build_manifest(committed["revised_at"])


def test_manifest_catalog_covers_every_workflow_and_nothing_else():
    guides = {path.parent.name for path in PACK_SOURCE_DIR.glob("skills/*/GUIDE.md")}
    kept_out = {path.parent.name for path in UNPUBLISHED_DIR.glob("*/SKILL.md")}

    assert set(PUBLISHED) == guides
    assert set(UNPUBLISHED) == kept_out


def test_rebuild_keeps_the_revision_date_until_the_content_changes(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    monkeypatch.setattr(build_skill_pack, "MANIFEST_PATH", manifest)

    manifest.write_text(
        json.dumps(build_manifest("2026-01-02")), encoding="utf-8"
    )
    assert build_skill_pack._revised_at() == "2026-01-02"

    manifest.write_text(
        json.dumps({**build_manifest("2026-01-02"), "content_sha256": "stale"}),
        encoding="utf-8",
    )
    assert build_skill_pack._revised_at() == date.today().isoformat()
