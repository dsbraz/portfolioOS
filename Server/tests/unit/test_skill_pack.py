import re
from pathlib import PurePosixPath
from zipfile import ZipFile

from scripts.build_skill_pack import PACK_PATH, PACK_SOURCE_DIR, pack_entries

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

