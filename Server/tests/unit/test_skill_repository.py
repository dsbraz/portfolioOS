import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest

from app.repositories.skill_repository import SkillRepository


def _write_plugin_sources(skills_dir: Path) -> Path:
    plugin_dir = skills_dir / "portfolioos"
    codex_manifest = {
        "name": "portfolioos",
        "version": "1.0.0",
        "description": "Test portfolioOS plugin",
        "author": {"name": "portfolioOS"},
        "skills": "./skills/",
        "interface": {
            "displayName": "portfolioOS",
            "shortDescription": "Use portfolioOS with Agent Skills.",
            "longDescription": "Agent Skills for portfolioOS workflows.",
            "developerName": "portfolioOS",
            "category": "Productivity",
            "capabilities": ["Read", "Write"],
            "defaultPrompt": "Help me use portfolioOS.",
        },
    }
    claude_manifest = {
        "name": "portfolioos",
        "version": "1.0.0",
        "description": "Test portfolioOS plugin",
        "author": {"name": "portfolioOS"},
    }
    artifacts = {
        ".codex-plugin/plugin.json": json.dumps(codex_manifest, indent=2) + "\n",
        ".claude-plugin/plugin.json": json.dumps(claude_manifest, indent=2) + "\n",
        "README.md": "# Install\n\nUpload `portfolioos.zip` as one skill.\n",
        "PACK_SKILL.md": (
            "---\n"
            "name: portfolioos\n"
            "description: Route portfolioOS tasks to bundled skills.\n"
            "---\n\n"
            "## Bundled skills\n\n"
            "<!-- portfolioos:published-skills -->\n"
        ),
    }
    for relative_path, content in artifacts.items():
        path = plugin_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return plugin_dir


def _write_skill(
    skills_dir: Path,
    name: str,
    *,
    published: bool = True,
    blocked_reason: str | None = None,
    version: str = "2026-08-13",
    writes: bool = False,
    reads_external: bool = False,
) -> Path:
    skill_dir = skills_dir / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                "description: Test skill",
                "---",
                "",
                f"# {name}",
            ]
        ),
        encoding="utf-8",
    )
    catalog_metadata = {
        "version": version,
        "writes": writes,
        "reads_external": reads_external,
        "published": published,
    }
    if blocked_reason is not None:
        catalog_metadata["blocked_reason"] = blocked_reason
    (skill_dir / ".portfolioos.json").write_text(
        json.dumps(catalog_metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    return skill_dir


@pytest.fixture
def skills_dir(tmp_path: Path) -> Path:
    root = tmp_path / "skills"
    root.mkdir()
    _write_skill(root, "known-skill")
    return root


@pytest.fixture
def repository(skills_dir: Path) -> SkillRepository:
    return SkillRepository(skills_dir)


@pytest.mark.parametrize(
    "name",
    ["..", "../../etc/passwd", "/etc/passwd", ""],
)
def test_get_package_rejects_names_outside_known_skill_directories(
    repository: SkillRepository,
    name: str,
):
    assert repository.get_package(name) is None


def test_list_ignores_files_and_directories_without_skill_markdown(
    skills_dir: Path,
    repository: SkillRepository,
):
    (skills_dir / "README.md").write_text("Not a skill", encoding="utf-8")
    (skills_dir / "incomplete").mkdir()
    _write_plugin_sources(skills_dir)

    items, total = repository.get_all()

    assert total == 1
    assert [item.name for item in items] == ["known-skill"]


def test_unpublished_skill_has_block_reason_and_no_files(skills_dir: Path):
    _write_skill(
        skills_dir,
        "blocked-skill",
        published=False,
        blocked_reason="Awaiting approval.",
    )

    items, _ = SkillRepository(skills_dir).get_all()
    blocked = next(item for item in items if item.name == "blocked-skill")

    assert blocked.published is False
    assert blocked.blocked_reason == "Awaiting approval."
    assert blocked.files is None


def test_skill_frontmatter_rejects_non_standard_fields(skills_dir: Path):
    skill_file = skills_dir / "known-skill" / "SKILL.md"
    skill_file.write_text(
        "---\n"
        "name: known-skill\n"
        "description: Test skill\n"
        "version: 2026-08-13\n"
        "---\n\n"
        "# known-skill\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported frontmatter fields: version"):
        SkillRepository(skills_dir).get_all()


def test_catalog_metadata_sidecar_is_required(skills_dir: Path):
    (skills_dir / "known-skill" / ".portfolioos.json").unlink()

    with pytest.raises(ValueError, match="catalog metadata is missing"):
        SkillRepository(skills_dir).get_all()


def test_catalog_metadata_sidecar_must_contain_valid_json(skills_dir: Path):
    (skills_dir / "known-skill" / ".portfolioos.json").write_text(
        "{invalid",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid catalog metadata JSON"):
        SkillRepository(skills_dir).get_all()


def test_package_is_recursive_prefixed_and_excludes_ignored_paths(
    skills_dir: Path,
    repository: SkillRepository,
):
    skill_dir = skills_dir / "known-skill"
    references = skill_dir / "references"
    references.mkdir()
    (references / "guide.md").write_text("Guide", encoding="utf-8")
    (skill_dir / ".secret").write_text("Secret", encoding="utf-8")
    hidden_dir = skill_dir / ".hidden"
    hidden_dir.mkdir()
    (hidden_dir / "data.txt").write_text("Hidden", encoding="utf-8")
    cache_dir = skill_dir / "scripts" / "__pycache__"
    cache_dir.mkdir(parents=True)
    (cache_dir / "compiled.pyc").write_bytes(b"compiled")

    package = repository.get_package("known-skill")

    assert package is not None
    with ZipFile(BytesIO(package)) as archive:
        assert set(archive.namelist()) == {
            "known-skill/SKILL.md",
            "known-skill/references/guide.md",
        }
        assert not any(
            name.endswith(".portfolioos.json") for name in archive.namelist()
        )


def test_pack_contains_only_published_skills_under_common_root(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    plugin_dir = _write_plugin_sources(skills_dir)
    _write_skill(skills_dir, "operar-portfolioos")
    alpha_dir = _write_skill(skills_dir, "alpha-skill")
    beta_dir = _write_skill(skills_dir, "beta-skill")
    blocked_dir = _write_skill(
        skills_dir,
        "blocked-skill",
        published=False,
        blocked_reason="Awaiting approval.",
    )
    references_dir = alpha_dir / "references"
    references_dir.mkdir()
    guide_file = references_dir / "guide.md"
    guide_file.write_text("Alpha guide", encoding="utf-8")
    (beta_dir / "run.py").write_text("print('beta')", encoding="utf-8")
    (blocked_dir / "private.txt").write_text("Blocked", encoding="utf-8")
    (alpha_dir / ".secret").write_text("Secret", encoding="utf-8")
    cache_dir = alpha_dir / "scripts" / "__pycache__"
    cache_dir.mkdir(parents=True)
    (cache_dir / "compiled.pyc").write_bytes(b"compiled")
    (alpha_dir / "guide-link.md").symlink_to(guide_file)
    (plugin_dir / ".internal").write_text("Internal", encoding="utf-8")
    (plugin_dir / "readme-link.md").symlink_to(plugin_dir / "README.md")

    package = SkillRepository(skills_dir).get_pack()

    with ZipFile(BytesIO(package)) as archive:
        assert set(archive.namelist()) == {
            "portfolioos/.claude-plugin/plugin.json",
            "portfolioos/.codex-plugin/plugin.json",
            "portfolioos/README.md",
            "portfolioos/SKILL.md",
            "portfolioos/skills/alpha-skill/SKILL.md",
            "portfolioos/skills/alpha-skill/references/guide.md",
            "portfolioos/skills/beta-skill/SKILL.md",
            "portfolioos/skills/beta-skill/run.py",
            "portfolioos/skills/operar-portfolioos/SKILL.md",
        }
        assert (
            archive.read("portfolioos/skills/alpha-skill/references/guide.md")
            == b"Alpha guide"
        )
        assert archive.read("portfolioos/skills/beta-skill/run.py") == b"print('beta')"

        codex_manifest = json.loads(
            archive.read("portfolioos/.codex-plugin/plugin.json")
        )
        claude_manifest = json.loads(
            archive.read("portfolioos/.claude-plugin/plugin.json")
        )
        assert codex_manifest["name"] == "portfolioos"
        assert codex_manifest["version"] == "1.0.0"
        assert codex_manifest["skills"] == "./skills/"
        assert "mcpServers" not in codex_manifest
        assert "apps" not in codex_manifest
        assert claude_manifest["name"] == "portfolioos"
        assert claude_manifest["version"] == "1.0.0"
        root_skill = archive.read("portfolioos/SKILL.md").decode()
        assert "<!-- portfolioos:published-skills -->" not in root_skill
        assert (
            "[`operar-portfolioos`](skills/operar-portfolioos/SKILL.md): Test skill"
            in root_skill
        )
        assert "[`alpha-skill`](skills/alpha-skill/SKILL.md): Test skill" in root_skill
        assert "[`beta-skill`](skills/beta-skill/SKILL.md): Test skill" in root_skill
        assert "blocked-skill" not in root_skill


def test_pack_requires_published_base_skill(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    _write_plugin_sources(skills_dir)
    _write_skill(skills_dir, "specialized-skill")

    with pytest.raises(ValueError, match="Required base skill is missing"):
        SkillRepository(skills_dir).get_pack()

    _write_skill(
        skills_dir,
        "operar-portfolioos",
        published=False,
        blocked_reason="Awaiting approval.",
    )

    with pytest.raises(ValueError, match="Required base skill is unpublished"):
        SkillRepository(skills_dir).get_pack()


def test_pack_requires_skill_index_marker(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    plugin_dir = _write_plugin_sources(skills_dir)
    _write_skill(skills_dir, "operar-portfolioos")
    (plugin_dir / "PACK_SKILL.md").write_text(
        "---\nname: portfolioos\ndescription: Test pack.\n---\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Plugin skill index marker is missing"):
        SkillRepository(skills_dir).get_pack()


def test_pack_rejects_template_reference_to_unpublished_skill(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    plugin_dir = _write_plugin_sources(skills_dir)
    _write_skill(skills_dir, "operar-portfolioos")
    _write_skill(
        skills_dir,
        "blocked-skill",
        published=False,
        blocked_reason="Awaiting approval.",
    )
    template_path = plugin_dir / "PACK_SKILL.md"
    template_path.write_text(
        template_path.read_text(encoding="utf-8")
        + "\nRead `skills/blocked-skill/SKILL.md`.\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="wrapper references unpublished or unknown skills: blocked-skill",
    ):
        SkillRepository(skills_dir).get_pack()


def test_pack_requires_installable_plugin_artifacts(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    _write_skill(skills_dir, "operar-portfolioos")

    with pytest.raises(ValueError, match="Plugin artifact is missing"):
        SkillRepository(skills_dir).get_pack()


def test_pack_rejects_symlinked_plugin_source_directory(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    _write_skill(skills_dir, "operar-portfolioos")
    external_skills_dir = tmp_path / "external-skills"
    external_skills_dir.mkdir()
    plugin_dir = _write_plugin_sources(external_skills_dir)
    (skills_dir / "portfolioos").symlink_to(plugin_dir, target_is_directory=True)

    with pytest.raises(ValueError, match="Plugin directory must not be a symlink"):
        SkillRepository(skills_dir).get_pack()


def test_unpublished_skill_has_no_package(skills_dir: Path):
    _write_skill(
        skills_dir,
        "blocked-skill",
        published=False,
        blocked_reason="Awaiting approval.",
    )

    assert SkillRepository(skills_dir).get_package("blocked-skill") is None


@pytest.mark.parametrize("version", ["20260813", "2026-8-13", "13/08/2026"])
def test_version_requires_the_documented_yyyy_mm_dd_format(
    tmp_path: Path,
    version: str,
):
    root = tmp_path / "skills"
    _write_skill(root, "dated-skill", version=version)

    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        SkillRepository(root).get_all()
