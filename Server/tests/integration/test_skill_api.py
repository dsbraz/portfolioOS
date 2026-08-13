import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from httpx import AsyncClient
from jose import jwt

from app.config import settings


def _write_plugin_sources(skills_dir: Path) -> None:
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


def _frontmatter(skill_file: Path) -> dict[str, str]:
    block = skill_file.read_text(encoding="utf-8").split("---", maxsplit=2)[1]
    return {
        key.strip(): value.strip()
        for line in block.splitlines()
        if ":" in line
        for key, value in [line.split(":", maxsplit=1)]
    }


def _catalog_metadata(skill_dir: Path) -> dict[str, object]:
    return json.loads((skill_dir / ".portfolioos.json").read_text(encoding="utf-8"))


def _visible_files(skill_dir: Path) -> set[str]:
    return {
        str(path.relative_to(skill_dir)).replace("\\", "/")
        for path in skill_dir.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and not any(
            part.startswith(".") or part == "__pycache__"
            for part in path.relative_to(skill_dir).parts
        )
    }


def _write_skill(
    root: Path,
    name: str,
    *,
    published: bool = True,
    blocked_reason: str | None = None,
) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                "description: Integration test skill",
                "---",
                "",
                f"# {name}",
            ]
        ),
        encoding="utf-8",
    )
    catalog_metadata = {
        "version": "2026-08-13",
        "writes": False,
        "reads_external": False,
        "published": published,
    }
    if blocked_reason is not None:
        catalog_metadata["blocked_reason"] = blocked_reason
    (skill_dir / ".portfolioos.json").write_text(
        json.dumps(catalog_metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    return skill_dir


@pytest.mark.asyncio
async def test_catalog_lists_all_known_skills_with_state_specific_fields(
    anon_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "skills_public", True)
    skills_dir = Path(settings.skills_dir)
    skill_dirs = sorted(
        path
        for path in skills_dir.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )

    response = await anon_client.get("/api/skills")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"items", "total"}
    assert payload["total"] == len(skill_dirs)
    assert {item["name"] for item in payload["items"]} == {
        path.name for path in skill_dirs
    }

    by_name = {item["name"]: item for item in payload["items"]}
    for skill_dir in skill_dirs:
        frontmatter = _frontmatter(skill_dir / "SKILL.md")
        catalog_metadata = _catalog_metadata(skill_dir)
        item = by_name[skill_dir.name]
        assert item["description"] == frontmatter["description"]
        assert item["version"] == catalog_metadata["version"]
        assert item["writes"] is catalog_metadata["writes"]
        assert item["reads_external"] is catalog_metadata["reads_external"]
        assert item["published"] is catalog_metadata["published"]
        if item["published"]:
            assert "blocked_reason" not in item
            assert set(item["files"]) == _visible_files(skill_dir)
        else:
            assert item["blocked_reason"] == catalog_metadata["blocked_reason"]
            assert "files" not in item


@pytest.mark.asyncio
async def test_download_returns_exact_recursive_prefixed_package(
    anon_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    skills_dir = tmp_path / "skills"
    skill_dir = _write_skill(skills_dir, "nested-skill")
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
    monkeypatch.setattr(settings, "skills_dir", str(skills_dir))
    monkeypatch.setattr(settings, "skills_public", True)

    response = await anon_client.get("/api/skills/nested-skill.zip")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["content-disposition"] == (
        'attachment; filename="nested-skill.zip"'
    )
    with ZipFile(BytesIO(response.content)) as archive:
        assert set(archive.namelist()) == {
            "nested-skill/SKILL.md",
            "nested-skill/references/guide.md",
        }


@pytest.mark.asyncio
async def test_pack_download_contains_all_and_only_published_skills(
    anon_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    skills_dir = tmp_path / "skills"
    _write_plugin_sources(skills_dir)
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
    (references_dir / "guide.md").write_text("Alpha guide", encoding="utf-8")
    (beta_dir / "run.py").write_text("print('beta')", encoding="utf-8")
    (blocked_dir / "private.txt").write_text("Blocked", encoding="utf-8")
    (alpha_dir / ".secret").write_text("Secret", encoding="utf-8")
    cache_dir = alpha_dir / "scripts" / "__pycache__"
    cache_dir.mkdir(parents=True)
    (cache_dir / "compiled.pyc").write_bytes(b"compiled")
    (alpha_dir / "guide-link.md").symlink_to(references_dir / "guide.md")
    monkeypatch.setattr(settings, "skills_dir", str(skills_dir))
    monkeypatch.setattr(settings, "skills_public", True)

    response = await anon_client.get("/api/skills.zip")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["content-disposition"] == (
        'attachment; filename="portfolioos.zip"'
    )
    with ZipFile(BytesIO(response.content)) as archive:
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
        assert b"Upload `portfolioos.zip` as one skill" in archive.read(
            "portfolioos/README.md"
        )
        root_skill = archive.read("portfolioos/SKILL.md").decode()
        assert "<!-- portfolioos:published-skills -->" not in root_skill
        assert "skills/operar-portfolioos/SKILL.md" in root_skill
        assert "skills/alpha-skill/SKILL.md" in root_skill
        assert "skills/beta-skill/SKILL.md" in root_skill
        assert "blocked-skill" not in root_skill
        assert (
            json.loads(archive.read("portfolioos/.codex-plugin/plugin.json"))["skills"]
            == "./skills/"
        )


@pytest.mark.asyncio
async def test_download_openapi_declares_zip_binary_response(
    anon_client: AsyncClient,
):
    response = await anon_client.get("/openapi.json")

    assert response.status_code == 200
    operation = response.json()["paths"]["/api/skills/{name}.zip"]["get"]
    content = operation["responses"]["200"]["content"]

    assert content == {
        "application/zip": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }


@pytest.mark.asyncio
async def test_pack_download_openapi_declares_zip_binary_response(
    anon_client: AsyncClient,
):
    response = await anon_client.get("/openapi.json")

    assert response.status_code == 200
    operation = response.json()["paths"]["/api/skills.zip"]["get"]

    assert operation["responses"]["200"]["content"] == {
        "application/zip": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }


@pytest.mark.asyncio
async def test_download_returns_404_for_blocked_and_unknown_skills(
    anon_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    skills_dir = tmp_path / "skills"
    _write_skill(
        skills_dir,
        "blocked-skill",
        published=False,
        blocked_reason="Awaiting approval.",
    )
    monkeypatch.setattr(settings, "skills_dir", str(skills_dir))
    monkeypatch.setattr(settings, "skills_public", True)

    blocked = await anon_client.get("/api/skills/blocked-skill.zip")
    unknown = await anon_client.get("/api/skills/unknown-skill.zip")

    assert blocked.status_code == 404
    assert unknown.status_code == 404


@pytest.mark.asyncio
async def test_skills_access_switch_applies_to_index_and_download(
    anon_client: AsyncClient,
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    skills_dir = Path(settings.skills_dir)
    published_name = next(
        path.name
        for path in skills_dir.iterdir()
        if path.is_dir()
        and (path / "SKILL.md").is_file()
        and _catalog_metadata(path)["published"] is True
    )
    package_url = f"/api/skills/{published_name}.zip"

    monkeypatch.setattr(settings, "skills_public", True)
    assert (await anon_client.get("/api/skills")).status_code == 200
    assert (await anon_client.get("/api/skills.zip")).status_code == 200
    assert (await anon_client.get(package_url)).status_code == 200

    monkeypatch.setattr(settings, "skills_public", False)
    assert (await anon_client.get("/api/skills")).status_code == 401
    assert (await anon_client.get("/api/skills.zip")).status_code == 401
    assert (await anon_client.get(package_url)).status_code == 401
    assert (await client.get("/api/skills")).status_code == 200
    assert (await client.get("/api/skills.zip")).status_code == 200
    assert (await client.get(package_url)).status_code == 200


@pytest.mark.asyncio
async def test_closed_catalog_rejects_token_with_non_string_subject(
    anon_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "skills_public", False)
    token = jwt.encode({"sub": 123}, settings.secret_key, algorithm="HS256")

    response = await anon_client.get(
        "/api/skills",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
