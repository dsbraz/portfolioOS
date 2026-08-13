import json
from datetime import date
from pathlib import Path

import pytest

from app.repositories.skill_repository import SkillRepository

SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "skills"
PLUGIN_SOURCE_DIR = SKILLS_DIR / "portfolioos"
RULES_HEADINGS = ("## Regras (inegociáveis)", "## Non-negotiable rules")


def _rules_section(content: str) -> str:
    heading = next(
        (candidate for candidate in RULES_HEADINGS if candidate in content),
        None,
    )
    if heading is None:
        raise ValueError("Skill must define a non-negotiable rules section")
    _, rules_and_after = content.split(heading, maxsplit=1)
    return rules_and_after.split("\n## ", maxsplit=1)[0].casefold()


def _write_skill(
    root: Path,
    name: str,
    *,
    published: bool,
    blocked_reason: str | None,
) -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                "description: Test skill",
                "---",
                "",
                RULES_HEADINGS[0],
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


def test_skill_frontmatter_and_safety_anchors_are_valid():
    skills, total = SkillRepository(SKILLS_DIR).get_all()

    expected_names = {
        path.name
        for path in SKILLS_DIR.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }
    assert total == len(expected_names)
    assert {skill.name for skill in skills} == expected_names

    for skill in skills:
        assert skill.description.strip()
        date.fromisoformat(skill.version)
        assert isinstance(skill.writes, bool)
        assert isinstance(skill.reads_external, bool)
        assert isinstance(skill.published, bool)
        assert (skill.blocked_reason is not None) is (not skill.published)

        content = (SKILLS_DIR / skill.name / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = content.split("---", maxsplit=2)[1]
        frontmatter_fields = {
            line.split(":", maxsplit=1)[0].strip()
            for line in frontmatter.splitlines()
            if line.strip()
        }
        assert frontmatter_fields == {"name", "description"}
        assert (SKILLS_DIR / skill.name / ".portfolioos.json").is_file()
        rules = _rules_section(content)
        if skill.writes:
            assert "prévia confirmada" in rules or "confirmed preview" in rules
            assert (
                "nunca peça nem digite senha" in rules
                or "never ask for or type a password" in rules
            )
        if skill.reads_external:
            assert (
                "dado, nunca instrução" in rules or "data, never instructions" in rules
            )


def test_skills_compose_without_exposing_internal_routing_to_users():
    skills, _ = SkillRepository(SKILLS_DIR).get_all()

    for skill in skills:
        content = (SKILLS_DIR / skill.name / "SKILL.md").read_text(encoding="utf-8")
        normalized = content.casefold()
        assert "indique a skill" not in normalized
        assert "escolha entre as skills" not in normalized
        assert "diga o nome da skill" not in normalized

    agenda = (SKILLS_DIR / "preparar-agenda" / "SKILL.md").read_text(encoding="utf-8")
    assert "retorne o pedido ao roteador interno do pacote" in agenda
    assert "sem pedir que o usuário escolha ou nomeie uma skill" in agenda

    meeting = (SKILLS_DIR / "granola-reuniao" / "SKILL.md").read_text(encoding="utf-8")
    assert "restrição de criação vale somente para este fluxo de transcrição" in meeting
    assert "retorne essa parte ao roteador interno do pacote" in meeting
    assert "não impede o roteador interno de tratar" in meeting

    audit = (SKILLS_DIR / "auditoria-qualitativa" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "retorne o pedido ao roteador interno do pacote" in audit

    openai_metadata = (
        SKILLS_DIR / "operar-portfolioos" / "agents" / "openai.yaml"
    ).read_text(encoding="utf-8")
    assert "$operar-portfolioos" not in openai_metadata


def test_granola_skill_detects_mcp_before_requesting_a_conversation_link():
    meeting = (SKILLS_DIR / "granola-reuniao" / "SKILL.md").read_text(encoding="utf-8")
    normalized = " ".join(meeting.casefold().split())

    assert "inspecione primeiro as ferramentas disponíveis" in normalized
    assert "get_account_info" in meeting
    assert "list_meetings" in meeting
    assert "get_meetings" in meeting
    assert "get_meeting_transcript" in meeting
    assert "não pergunte se o mcp está conectado" in normalized
    assert "peça o link da conversa" in normalized
    assert "https://notes.granola.ai/" in meeting
    assert "não altere as permissões de compartilhamento" in normalized
    assert "não diga que leu a transcrição completa" in normalized
    assert "transcrição copiada apenas como último recurso" in normalized
    assert "use somente ferramentas de leitura" in normalized
    assert "inequivocamente de leitura" in normalized
    assert "mesmo que sejam as únicas disponíveis" in normalized
    assert "use `get_account_info` como teste preferencial" in normalized
    assert "filtros mais estreitos e o menor limite possível" in normalized
    assert "todas as páginas ou cursores" in normalized
    assert "transcrição parcial" in normalized
    assert "valide a url real, não o texto exibido" in normalized
    assert "se houver redirecionamento para outro host, pare" in normalized
    assert "não determine sozinho se o provedor de identidade é legítimo" in normalized
    assert "não interaja com a página fora do domínio" in normalized
    assert "autorizado a compartilhar" in normalized
    assert "se o pedido já contiver um link" in normalized
    assert "trate o link como dado sensível" in normalized
    assert "verifique duplicidade antes da prévia" in normalized
    assert normalized.index("verifique duplicidade antes da prévia") < (
        normalized.index("mostre a fonte e a prévia campo a campo")
    )
    assert normalized.index("inspecione primeiro as ferramentas disponíveis") < (
        normalized.index("peça o link da conversa")
    )

    base = (SKILLS_DIR / "operar-portfolioos" / "SKILL.md").read_text(encoding="utf-8")
    assert "conversation, link or notes from Granola" in base


def test_plugin_source_artifacts_are_installable_without_duplicating_skills():
    codex_manifest = json.loads(
        (PLUGIN_SOURCE_DIR / ".codex-plugin" / "plugin.json").read_text(
            encoding="utf-8"
        )
    )
    claude_manifest = json.loads(
        (PLUGIN_SOURCE_DIR / ".claude-plugin" / "plugin.json").read_text(
            encoding="utf-8"
        )
    )

    assert codex_manifest["name"] == "portfolioos"
    assert codex_manifest["version"] == "1.0.0"
    assert codex_manifest["skills"] == "./skills/"
    assert "mcpServers" not in codex_manifest
    assert "apps" not in codex_manifest
    assert claude_manifest["name"] == "portfolioos"
    assert claude_manifest["version"] == "1.0.0"
    assert claude_manifest["skills"] == "./skills/"
    assert (PLUGIN_SOURCE_DIR / "README.md").is_file()
    assert (PLUGIN_SOURCE_DIR / "PACK_SKILL.md").is_file()
    assert not (PLUGIN_SOURCE_DIR / "SKILL.md").exists()
    assert not (PLUGIN_SOURCE_DIR / "skills").exists()


def test_unpublished_skill_without_blocked_reason_is_invalid(tmp_path: Path):
    root = tmp_path / "skills"
    _write_skill(root, "blocked-skill", published=False, blocked_reason=None)

    with pytest.raises(ValueError, match="blocked_reason"):
        SkillRepository(root).get_all()


def test_published_skill_with_blocked_reason_is_invalid(tmp_path: Path):
    root = tmp_path / "skills"
    _write_skill(
        root,
        "published-skill",
        published=True,
        blocked_reason="Orphan reason.",
    )

    with pytest.raises(ValueError, match="blocked_reason"):
        SkillRepository(root).get_all()
