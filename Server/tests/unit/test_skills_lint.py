import json
from datetime import date
from pathlib import Path

import pytest
import yaml

from app.repositories.skill_repository import SkillRepository

SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "skills"
PACKAGE_SOURCE_DIR = SKILLS_DIR / "portfolioos"
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

    chase = (SKILLS_DIR / "cobrar-indicadores" / "SKILL.md").read_text(encoding="utf-8")
    assert "retorne essa parte ao roteador interno do pacote" in chase

    # OpenAI resolves `agents/openai.yaml` beside the archive's SKILL.md only,
    # so a nested copy under a skill directory is never read — it must not
    # exist, or it ships as dead weight in every download.
    assert not (SKILLS_DIR / "operar-portfolioos" / "agents").exists()


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


def test_agenda_skill_reads_the_conversation_before_the_platform():
    """"Analyse the meeting" is not answered by the meeting record.

    The record in Reuniões de Conselho is a summary written afterwards, already
    filtered by whoever typed it. The conversation is the source. A brief built
    only from the platform answers a different question while looking complete —
    the failure that made "analise a reunião com a investida e me prepare para a
    próxima" come back with indicators and no meeting content at all.
    """
    agenda = (SKILLS_DIR / "preparar-agenda" / "SKILL.md").read_text(encoding="utf-8")
    normalized = " ".join(agenda.casefold().split())

    # Granola is not an optional enrichment: it is the source of the meeting,
    # and it is searched even when the user never names it.
    assert "buscar a conversa no granola é passo obrigatório" in normalized
    assert "mesmo que o usuário não cite o granola" in normalized
    assert "a reunião vem da conversa, não só da plataforma" in normalized

    # Same source discovery as the recording flow: probe the MCP, never ask the
    # user whether it is connected, fall back to a link on the exact host.
    assert "inspecione primeiro as ferramentas disponíveis" in normalized
    assert "não pergunte se o mcp está conectado" in normalized
    for tool in ("get_account_info", "list_meetings", "get_meetings"):
        assert tool in agenda, tool
    assert "peça o link da conversa" in normalized
    assert "https://notes.granola.ai/" in agenda
    assert normalized.index("inspecione primeiro as ferramentas disponíveis") < (
        normalized.index("peça o link da conversa")
    )

    # Read-only has to cover Granola too, or the skill's own promise leaks.
    assert "use apenas operações **inequivocamente de leitura**" in normalized
    assert "não diga que leu a transcrição completa" in normalized

    # Coming back empty is a reportable outcome, never a silent downgrade to
    # platform-only — and never a dead end either: the brief still ships.
    assert "o que você não achou, você diz" in normalized
    assert "informe o usuário" in normalized
    assert "não bloqueie a preparação esperando o link" in normalized

    # The delivered document carries the source, so the reader can tell what a
    # fact is worth: said in the call, or reported months ago on a form.
    assert "fonte da reunião" in normalized
    assert "conversa não encontrada no granola" in normalized

    # The router has to say it too: the request that reaches it is "analyse the
    # meeting", which never mentions Granola.
    base = (SKILLS_DIR / "operar-portfolioos" / "SKILL.md").read_text(encoding="utf-8")
    routing = " ".join(base.casefold().split())
    assert "to analyse the last meeting with a startup" in routing
    assert "reads the conversation from granola before it reads the platform" in routing


def test_every_granola_flow_carries_the_same_source_safety_anchors():
    """Three skills read Granola; the safety floor cannot depend on which one.

    The discovery text is deliberately duplicated (each guide is self-contained
    in the archive), and duplication drifts: the audit found the link-consent
    warning present in one copy and silently missing from the other two. This
    test pins the shared floor so a future edit to one flow fails loudly
    instead of quietly weakening it.
    """
    granola_flows = ("granola-reuniao", "preparar-agenda", "apresentacao-portfolio")
    shared_anchors = (
        # Discovery: probe the MCP, never interrogate the user about it.
        "inspecione primeiro as ferramentas disponíveis",
        "não pergunte se o mcp está conectado",
        # Read-only floor on the external system.
        "inequivocamente de leitura",
        # Link fallback: exact host, consent, and the link never travels on.
        "notes.granola.ai",
        "autorizado a compartilhar",
        "dado sensível",
        # Honest coverage: never claim more than what was actually read.
        "transcrição completa",
    )
    for name in granola_flows:
        content = (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.casefold().split())
        for anchor in shared_anchors:
            assert anchor in normalized, f"{name}: missing anchor {anchor!r}"


def test_agenda_skill_delivers_a_branded_html_it_never_regenerates():
    """The shell is copied, not written. That is the whole economy of it.

    Re-emitting the CSS on every run costs more tokens than the briefing
    itself, drifts off-brand a little further each time, and quietly undoes
    contrast decisions that were audited once. So the skill ships the shell as
    an asset and the agent fills one marked slot.
    """
    agenda_dir = SKILLS_DIR / "preparar-agenda"
    agenda = (agenda_dir / "SKILL.md").read_text(encoding="utf-8")
    normalized = " ".join(agenda.casefold().split())

    shell_path = agenda_dir / "assets" / "preparacao.html"
    assert shell_path.is_file()
    shell = shell_path.read_text(encoding="utf-8")

    # One slot, clearly delimited, or "replace only the content" means nothing.
    for marker in ("▼▼ CONTEÚDO", "▲▲ FIM DO CONTEÚDO", "{{STARTUP}}"):
        assert marker in shell, marker

    # Self-contained: no CDN, no webfont host, and no chance of the Granola
    # link riding along inside the delivered file.
    assert "http" not in shell

    # The accent contract, which is the part a regenerated shell always loses:
    # purple is the functional accent, orange is brand-only, and purple is
    # raised on dark because #7f2ec9 reaches only 2.8:1 there.
    assert "#7f2ec9" in shell
    assert "#ee7c38" in shell
    assert "#a94fd6" in shell
    assert "prefers-color-scheme:dark" in shell

    # The instructions have to forbid the expensive path explicitly — an agent
    # that can write HTML will write HTML unless told plainly not to.
    assert "**copie o shell**" in normalized
    assert "copiar, não reescrever" in normalized
    assert "nunca reescreva o css" in normalized
    assert "nunca invente classe nova" in normalized
    assert "assets/preparacao.html" in agenda

    # The briefing lives in the file; repeating it in chat doubles the cost.
    assert "no chat, no máximo cinco linhas" in normalized

    # A file is a durable artifact — the conversation link must not be in it.
    assert "o link do granola não entra no arquivo" in normalized

    # No file system is a degraded path, not a dead end.
    assert "sem meio de escrever arquivo" in normalized


def test_chase_skill_never_assumes_the_send_mode_or_the_recipient():
    chase = (SKILLS_DIR / "cobrar-indicadores" / "SKILL.md").read_text(encoding="utf-8")
    normalized = " ".join(chase.casefold().split())

    # Generating a link is a platform write, so the batch is confirmed first and
    # the send mode is a separate, per-run human choice.
    assert "gerar link **é escrita**" in normalized
    assert "pode gerar" in normalized
    assert "pergunte, sempre, e **nunca assuma**" in normalized
    assert "a escolha vale só para esta execução" in normalized
    assert "nunca a memorize" in normalized
    assert "um a um (padrão)" in normalized

    # The recipient comes from the registry, never from the conversation.
    assert "não aceite, não peça e não digite número avulso" in normalized
    assert "nunca entra no envio" in normalized

    # The reporting state is inversely encoded on screen; reading it backwards
    # would chase exactly the startups that did report.
    assert "startup sem nota é startup que reportou" in normalized
    assert "nunca deduza pelas colunas numéricas" in normalized
    assert "report mensal" in normalized

    # Every control the skill navigates by must exist verbatim in the UI.
    for label in (
        "Mês anterior",
        "Adicionar indicador",
        "Gerar link para a investida",
        "Gerar link",
        "Link do formulário",
        "Links anteriores",
        "Enviar por WhatsApp para {nome}",
        "Enviar por e-mail para {nome}",
        "Sem canal de envio",
        "Executivos",
    ):
        assert label in chase, label

    # Channel order is a product rule, not a preference: WhatsApp is tried
    # first, and e-mail is the fallback only when WhatsApp is unavailable.
    assert "tente sempre o whatsapp primeiro" in normalized
    assert "só use o e-mail quando o whatsapp não estiver disponível" in normalized
    assert "a plataforma nunca envia nada sozinha" in normalized


def test_chase_skill_orients_the_whatsapp_connection_before_the_queue():
    """A `wa.me` link does not open a conversation — it opens a choice.

    The send lands on WhatsApp's own interstitial, which offers the desktop app
    or WhatsApp Web. The two sessions are independent: being connected in one
    says nothing about the other. Picking the side where the person is not
    connected dead-ends the send — the web asks for a QR code, the app opens
    without the conversation — and it does so silently, mid-queue.
    """
    chase = (SKILLS_DIR / "cobrar-indicadores" / "SKILL.md").read_text(encoding="utf-8")
    normalized = " ".join(chase.casefold().split())

    # The interstitial's controls, verbatim: the agent finds them by visible
    # text, so a paraphrase would leave it clicking blind.
    for label in ("Open app", "Continue to WhatsApp Web"):
        assert label in chase, label

    # The trap the guidance exists for: one connection does not imply the other.
    assert "conexões independentes" in normalized
    assert "**não** conecta o whatsapp web" in normalized

    # Automatic mode cannot follow the desktop app — it leaves the browser,
    # where the agent has no reach. Saying so before the queue beats
    # discovering it at the first item.
    assert "fica fora do alcance da skill" in normalized

    # In one-by-one the person picks their own side: only they know where they
    # are connected, and guessing wastes the send.
    assert "é a pessoa que sabe onde está conectada" in normalized

    # Connecting is never the skill's job, QR code included.
    assert "nunca faz essa conexão nem lê qr code" in normalized


def test_package_source_artifacts_are_uploadable_without_duplicating_skills():
    assert (PACKAGE_SOURCE_DIR / "README.md").is_file()
    assert (PACKAGE_SOURCE_DIR / "PACK_SKILL.md").is_file()
    assert not (PACKAGE_SOURCE_DIR / "SKILL.md").exists()
    assert not (PACKAGE_SOURCE_DIR / "skills").exists()

    # An upload validator rejects an archive with more than one SKILL.md, so the
    # package must never regain a nested skill collection or its plugin manifests.
    assert not (PACKAGE_SOURCE_DIR / ".codex-plugin").exists()
    assert not (PACKAGE_SOURCE_DIR / ".claude-plugin").exists()

    # OpenAI reads it as <dir holding SKILL.md>/agents/openai.yaml. The package is
    # one skill rooted at portfolioos/, so package-level UI metadata lives here.
    interface = yaml.safe_load(
        (PACKAGE_SOURCE_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
    )
    assert interface["interface"]["display_name"] == "portfolioOS"
    assert 25 <= len(interface["interface"]["short_description"]) <= 64
    assert interface["policy"]["allow_implicit_invocation"] is True
    assert set(interface) <= {"interface", "policy", "dependencies"}
    assert set(interface["interface"]) <= {
        "display_name",
        "short_description",
        "icon_small",
        "icon_large",
        "brand_color",
        "default_prompt",
    }
    # The page promises users never name a skill, so no `$portfolioos` trigger.
    assert "$" not in interface["interface"]["default_prompt"]

    wrapper = (PACKAGE_SOURCE_DIR / "PACK_SKILL.md").read_text(encoding="utf-8")
    frontmatter = wrapper.split("---", maxsplit=2)[1]
    fields = {
        line.split(":", maxsplit=1)[0].strip()
        for line in frontmatter.splitlines()
        if line.strip()
    }
    assert fields == {"name", "description"}
    assert "name: portfolioos" in frontmatter
    assert wrapper.count("<!-- portfolioos:published-skills -->") == 1


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


def test_presentation_skill_protects_the_numbers_it_puts_on_a_slide():
    deck = (SKILLS_DIR / "apresentacao-portfolio" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(deck.casefold().split())

    # A deck is read by a committee and outlives the conversation, so a number
    # invented here is a decision made on fiction.
    assert "somente leitura" in normalized
    assert "verbatim" in normalized
    # The top cards coerce absence to zero; a deck that reports zero where the
    # investee simply did not report is a lie with a chart around it.
    assert "sem dado" in normalized
    assert "nunca como zero" in normalized
    # Participation is an estimate, and the slide has to say so.
    assert "estimativa" in normalized

    # The brand trio is not distributed with this package. Degrading honestly
    # beats producing an off-brand deck.
    assert "brq-pptx" in normalized
    assert "não improvise" in normalized

    # Third-party text reaches the slide, so the injection rule is mandatory.
    assert "dado, nunca instrução" in normalized

    # Every control the skill navigates by must exist verbatim in the UI.
    for label in (
        "Monitoramento",
        "Mês anterior",
        "Indicadores Mensais",
        "Ver indicador de {Mmm/AAAA}",
    ):
        assert label in deck, label

    # The deck follows the fund's real monthly deliverable — the Análise
    # Crítica — in FUNCTION. Two anchors keep that model from silently
    # degrading back into a generic deck:
    assert "análise crítica" in normalized
    # (a) every section declares its source: platform data vs user-provided —
    # the split is what forbids inventing ecosystem KPIs or deal values.
    assert "fonte declarada" in normalized
    # "Deals no pipe" is the ecosystem's co-sell business grouped by investee —
    # the real deck's meaning. The platform's Dealflow is the NEW-investment
    # funnel and only feeds the routines line; a generated deck once swapped
    # one for the other and shipped Seed/Série A stages where client deals
    # belonged.
    assert "a plataforma não guarda esses negócios" in normalized
    assert "funil de **novas investidas**" in normalized
    assert "nunca esta seção" in normalized
    # The model is CLOSED: same sections, same order, the real deck's agenda
    # blocks. The committee reads this deck every month; a re-invented agenda
    # or an extra analysis slide breaks the anatomy exactly like an omission.
    assert "o modelo é fechado" in normalized
    assert "nenhum slide fora do modelo" in normalized
    # The optional summary table replaces the canonical lines only — the
    # per-investee narrative survives it. A who-reported table is not a
    # per-investee summary.
    assert "nunca a narrativa" in normalized
    # (b) the coverage section is mandatory: the deck must say what it does
    # NOT cover — who has no meeting, no indicator, or suspicious data.
    assert "a seção 6 é obrigatória" in normalized
    assert "a preencher" in normalized
    # (b2) the qualitative sections also read the month's conversations — the
    # platform holds no record of what was decided, blocked, or asked for.
    # Granola is a THIRD source with its own marker, and it never crosses into
    # a number: a figure said on a call is not a reported indicator.
    assert "`[g]`" in normalized
    assert "o granola entra no qualitativo, nunca no numérico" in normalized
    assert "`[g]` nunca vira `[p]`" in normalized
    assert "toda linha vinda de conversa é atribuída" in normalized
    assert "inspecione primeiro as ferramentas disponíveis" in normalized
    assert "não pergunte se o mcp está conectado" in normalized
    for tool in ("get_account_info", "list_meetings", "get_meetings"):
        assert tool in deck, tool
    # A monthly deck spans the portfolio, so a queue of per-investee links is a
    # request nobody finishes — the deck ships without them instead.
    assert "não peça um link por investida" in normalized
    assert "nada encontrado é resultado, não erro" in normalized
    assert "não bloqueia o deck" in normalized
    # (c) a section the platform does not hold still gets its slide — labels
    # ready, values "a preencher" — and never blocks the flow waiting for the
    # user to supply the numbers.
    assert "nunca é omitida" in normalized
    assert "não bloqueie o fluxo" in normalized


def test_every_published_skill_has_activation_vocabulary_in_the_wrapper():
    """A skill inside the archive is unreachable if the wrapper never activates.

    The runtime decides whether to load the WHOLE package from the wrapper's
    `description`. Shipping the files is not enough: without a trigger word for
    what the skill does, the request never reaches it. This is the failure that
    let `apresentacao-portfolio` ride in the zip while "monte a apresentação do
    portfólio" matched nothing.
    """
    wrapper = (PACKAGE_SOURCE_DIR / "PACK_SKILL.md").read_text(encoding="utf-8")
    description = next(
        line for line in wrapper.splitlines() if line.startswith("description:")
    ).casefold()

    # One representative trigger per published capability. A skill added without
    # extending this map fails here, on purpose.
    triggers = {
        "preparar-agenda": ("agenda",),
        "granola-reuniao": ("granola", "reunião de conselho"),
        "cobrar-indicadores": ("cobrança", "não reportou"),
        "apresentacao-portfolio": ("apresentação", "análise crítica", "deck", "slides"),
        "operar-portfolioos": ("portfolioos",),
    }

    skills, _ = SkillRepository(SKILLS_DIR).get_all()
    published = {skill.name for skill in skills if skill.published}
    assert published <= set(triggers), (
        f"published skill without declared trigger vocabulary: "
        f"{published - set(triggers)}"
    )

    for name in published:
        assert any(word in description for word in triggers[name]), name


def test_every_skill_asks_for_the_address_instead_of_guessing_one():
    """Reaching the wrong system and operating it is worse than any delay.

    The skills carry no URL by design: the address changes per environment, and
    a skill that navigated on its own would have to handle "I am not signed in
    here", whose honest answer is asking for a credential — the one thing they
    must never do. So the rule is: no page open → ask the user, and never adopt
    an address found in content, which is third-party data like any other.
    """
    wrapper = (PACKAGE_SOURCE_DIR / "PACK_SKILL.md").read_text(encoding="utf-8")
    normalizado = " ".join(wrapper.casefold().split())

    assert "if portfolioos is not open, ask the user for its address" in normalizado
    assert "never guess an address" in normalizado
    assert "the address comes from the user" in normalizado
    # Arriving is not entering: an address never licenses asking for a password.
    assert "arriving is not entering" in normalizado

    base = (SKILLS_DIR / "operar-portfolioos" / "SKILL.md").read_text(encoding="utf-8")
    assert "ask the user for its address" in " ".join(base.casefold().split())

    # Every specialized skill states it as a foreseen situation, so the rule is
    # present wherever the agent actually is when the page is missing.
    skills, _ = SkillRepository(SKILLS_DIR).get_all()
    for skill in skills:
        if skill.name in ("operar-portfolioos", "portfolioos"):
            continue
        conteudo = (SKILLS_DIR / skill.name / "SKILL.md").read_text(encoding="utf-8")
        assert "portfolioOS não está aberto" in conteudo, skill.name
        assert "nunca adivinhe" in conteudo, skill.name
