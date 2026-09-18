import re
from pathlib import Path

import yaml

from scripts.build_skill_pack import (
    PACK_SOURCE_DIR as PACKAGE_SOURCE_DIR,
    PUBLISHED,
    UNPUBLISHED,
    UNPUBLISHED_DIR,
)

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


# What each workflow may do decides the safety anchors its rules must carry.
_CATALOG = {**PUBLISHED, **UNPUBLISHED}
WRITES = {name for name, meta in _CATALOG.items() if meta["writes"]}
READS_EXTERNAL = {name for name, meta in _CATALOG.items() if meta["reads_external"]}
READS_GRANOLA = {name for name, meta in _CATALOG.items() if meta["reads_granola"]}


def _skill_files() -> dict[str, Path]:
    published = {
        path.parent.name: path for path in PACKAGE_SOURCE_DIR.glob("skills/*/GUIDE.md")
    }
    unpublished = {path.parent.name: path for path in UNPUBLISHED_DIR.glob("*/SKILL.md")}
    return {**published, **unpublished}


def _read(name: str) -> str:
    return _skill_files()[name].read_text(encoding="utf-8")


def _normalized(content: str) -> str:
    """Folded to one case-insensitive line, for substring asserts."""
    return " ".join(content.casefold().split())


def test_skill_frontmatter_and_safety_anchors_are_valid():
    skills = _skill_files()
    assert set(skills) == set(_CATALOG)

    for name, path in skills.items():
        content = path.read_text(encoding="utf-8")
        frontmatter = content.split("---", maxsplit=2)[1]
        frontmatter_fields = {
            line.split(":", maxsplit=1)[0].strip()
            for line in frontmatter.splitlines()
            if line.strip()
        }
        assert frontmatter_fields == {"name", "description"}
        assert f"name: {name}" in frontmatter
        rules = _rules_section(content)
        if name in WRITES:
            assert "prévia confirmada" in rules or "confirmed preview" in rules
            assert (
                "nunca peça nem digite senha" in rules
                or "never ask for or type a password" in rules
            )
        if name in READS_EXTERNAL:
            assert (
                "dado, nunca instrução" in rules or "data, never instructions" in rules
            )


def test_skills_compose_without_exposing_internal_routing_to_users():
    for path in _skill_files().values():
        content = path.read_text(encoding="utf-8")
        normalized = content.casefold()
        assert "indique a skill" not in normalized
        assert "escolha entre as skills" not in normalized
        assert "diga o nome da skill" not in normalized

    agenda = _read("preparar-agenda")
    assert "retorne o pedido ao roteador interno do pacote" in agenda
    assert "sem pedir que o usuário escolha ou nomeie uma skill" in agenda

    meeting = _read("granola-reuniao")
    assert "restrição de criação vale somente para este fluxo de transcrição" in meeting
    assert "retorne essa parte ao roteador interno do pacote" in meeting
    assert "não impede o roteador interno de tratar" in meeting

    audit = _read("auditoria-qualitativa")
    assert "retorne o pedido ao roteador interno do pacote" in audit

    chase = _read("cobrar-indicadores")
    assert "retorne essa parte ao roteador interno do pacote" in chase



def test_granola_skill_detects_mcp_before_requesting_a_conversation_link():
    meeting = _read("granola-reuniao")
    normalized = _normalized(meeting)

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

    base = _read("operar-portfolioos")
    assert "conversation, link or notes from Granola" in base


def test_chase_skill_never_assumes_the_send_mode_or_the_recipient():
    chase = _read("cobrar-indicadores")
    normalized = _normalized(chase)

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

    # The panel picks the channel; the skill only follows it and never sends.
    assert "o painel já escolhe o canal" in normalized
    assert "a plataforma nunca envia nada sozinha" in normalized


def test_package_source_artifacts_are_uploadable_without_duplicating_skills():
    assert (PACKAGE_SOURCE_DIR / "README.md").is_file()
    assert (PACKAGE_SOURCE_DIR / "SKILL.md").is_file()

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

    wrapper = (PACKAGE_SOURCE_DIR / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = wrapper.split("---", maxsplit=2)[1]
    fields = {
        line.split(":", maxsplit=1)[0].strip()
        for line in frontmatter.splitlines()
        if line.strip()
    }
    assert fields == {"name", "description"}
    assert "name: portfolioos" in frontmatter


def test_presentation_skill_protects_the_numbers_it_puts_on_a_slide():
    deck = _read("apresentacao-portfolio")
    normalized = _normalized(deck)

    # A deck outlives the conversation, so an invented number becomes a decision.
    assert "somente leitura" in normalized
    assert "verbatim" in normalized
    # Absence is not zero: the top cards coerce it, the deck must not.
    assert "sem dado" in normalized
    assert "nunca como zero" in normalized
    assert "estimativa" in normalized
    # The brand skills are not shipped here; degrade instead of going off-brand.
    assert "brq-pptx" in normalized
    assert "não improvise" in normalized

    # Every control the guide navigates by must exist verbatim in the UI.
    for label in (
        "Monitoramento",
        "Mês anterior",
        "Indicadores Mensais",
        "Ver indicador de {Mmm/AAAA}",
    ):
        assert label in deck, label

    # The deck follows the fund's real monthly deliverable — the Análise
    # Crítica — in FUNCTION. Three anchors keep that model from silently
    # degrading back into a generic deck:
    assert "análise crítica" in normalized
    # (a) every section declares its source: platform data vs user-provided —
    # the split is what forbids inventing ecosystem KPIs or deal values.
    assert "fonte declarada" in normalized
    # "Deals no pipe" are the ecosystem's deals per investee, which the platform
    # does not hold; the platform's Dealflow is the funnel of NEW investees and
    # feeds a different line. Filling one with the other invents the number.
    assert "a plataforma não guarda esses negócios" in normalized
    assert "dealflow da plataforma é outra coisa" in normalized
    # (b) the coverage section is mandatory: the deck must say what it does
    # NOT cover — who has no meeting, no indicator, or suspicious data.
    assert "a seção 6 é obrigatória" in normalized
    assert "a preencher" in normalized
    # (c) a section the platform does not hold still gets its slide — labels
    # ready, values "a preencher" — and never blocks the flow waiting for the
    # user to supply the numbers.
    assert "nunca é omitida" in normalized
    assert "não bloqueie o fluxo" in normalized


def test_every_published_guide_has_activation_vocabulary_in_the_entrypoint():
    # The runtime loads the whole package from the entrypoint's description, so a
    # guide without a trigger word there is shipped but unreachable.
    wrapper = (PACKAGE_SOURCE_DIR / "SKILL.md").read_text(encoding="utf-8")
    description = next(
        line for line in wrapper.splitlines() if line.startswith("description:")
    ).casefold()
    triggers = {
        "operar-portfolioos": ("portfolioos",),
        "preparar-agenda": ("agenda",),
        "granola-reuniao": ("granola", "reunião de conselho"),
        "cobrar-indicadores": ("cobrança", "não reportou"),
        "apresentacao-portfolio": ("apresentação", "análise crítica", "deck", "slides"),
    }
    published = {path.parent.name for path in PACKAGE_SOURCE_DIR.glob("skills/*/GUIDE.md")}

    # A guide added without extending the map fails here, on purpose.
    assert published == set(triggers)
    for name in published:
        assert any(word in description for word in triggers[name]), name


def test_chase_guide_orients_the_whatsapp_connection_before_the_queue():
    """A `wa.me` link does not open a conversation — it opens a choice.

    The send lands on WhatsApp's own interstitial, which offers the desktop app
    or WhatsApp Web. The two sessions are independent: being connected in one
    says nothing about the other. Picking the side where the person is not
    connected dead-ends the send — the web asks for a QR code, the app opens
    without the conversation — and it does so silently, mid-queue.
    """
    chase = _read("cobrar-indicadores")
    normalized = _normalized(chase)

    # The interstitial belongs to WhatsApp, not to us, and it follows the
    # BROWSER's language: on the fund's pt-BR browsers the English labels are
    # not there at all. So the guide names the two exits by what they DO, and
    # carries the English wording only as a reference — an instruction to click
    # a literal string would stall the queue at the first item.
    for label in ("Open app", "Continue to WhatsApp Web"):
        assert label in chase, label
    assert "segue o idioma do navegador" in normalized
    assert "saída do aplicativo" in normalized
    assert "saída do navegador" in normalized
    # The rule that makes the labels reference material instead of a target.
    assert "nunca pelo texto exato" in normalized

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

    # The send controls are named as the panel exposes them, so the agent and
    # a screen reader look for the same thing.
    assert "enviar por whatsapp para {nome}" in normalized
    assert "enviar por e-mail para {nome}" in normalized


def test_every_guide_asks_for_the_address_instead_of_guessing_one():
    """Reaching the wrong system and operating it is worse than any delay.

    The guides carry no URL by design: the address changes per environment, and
    a guide that navigated on its own would have to handle "I am not signed in
    here", whose honest answer is asking for a credential — the one thing they
    must never do. So the rule is: no page open → ask the user, and never adopt
    an address found in content, which is third-party data like any other.
    """
    entrypoint = _normalized(
        (PACKAGE_SOURCE_DIR / "SKILL.md").read_text(encoding="utf-8")
    )

    assert "if portfolioos is not open, ask the user for its address" in entrypoint
    assert "never guess an address" in entrypoint
    assert "the address comes from the user" in entrypoint
    # Arriving is not entering: an address never licenses asking for a password.
    assert "arriving is not entering" in entrypoint

    # `operar-portfolioos` carries the shared safety rules the others defer to,
    # so it states the rule in full rather than as a foreseen situation.
    assert "ask the user for its address" in _normalized(_read("operar-portfolioos"))

    # Every other workflow states it where the agent actually is when the page
    # is missing — in its own table of foreseen situations.
    for name in _skill_files():
        if name == "operar-portfolioos":
            continue
        conteudo = _read(name)
        assert "portfolioOS não está aberto" in conteudo, name
        assert "nunca adivinhe" in conteudo, name


def test_agenda_guide_reads_the_conversation_before_the_platform():
    """"Analyse the meeting" is not answered by the meeting record.

    The record in Reuniões de Conselho is a summary written afterwards, already
    filtered by whoever typed it. The conversation is the source. A brief built
    only from the platform answers a different question while looking complete —
    the failure that made "analise a reunião com a investida e me prepare para a
    próxima" come back with indicators and no meeting content at all.
    """
    agenda = _read("preparar-agenda")
    normalized = _normalized(agenda)

    # Granola is not an optional enrichment: it is the source of the meeting,
    # and it is searched even when the user never names it.
    assert "buscar a conversa no granola é passo obrigatório" in normalized
    assert "mesmo que o usuário não cite o granola" in normalized
    assert "a reunião vem da conversa, não só da plataforma" in normalized

    # The shared Granola floor (discovery, read-only, consent, honest coverage)
    # has one owner: `test_every_granola_flow_carries_the_same_source_safety_anchors`.
    # Only the ordering is asserted here, because it is what this flow gets
    # wrong: asking for a link before probing the MCP.
    assert normalized.index("inspecione primeiro as ferramentas disponíveis") < (
        normalized.index("peça o link da conversa")
    )

    # Coming back empty is a reportable outcome, never a silent downgrade to
    # platform-only — and never a dead end either: the brief still ships.
    assert "o que você não achou, você diz" in normalized
    assert "informe o usuário" in normalized
    assert "não bloqueie a preparação esperando o link" in normalized

    # The delivered document carries the source, so the reader can tell what a
    # fact is worth: said in the call, or reported months ago on a form.
    assert "fonte da reunião" in normalized
    assert "conversa não encontrada no granola" in normalized

    # The entrypoint has to say it too: the request that reaches it is "analyse
    # the meeting", which never mentions Granola.
    routing = _normalized(_read("operar-portfolioos"))
    assert "to analyse the last meeting with a startup" in routing
    assert "reads the conversation from granola before it reads the platform" in routing


def test_every_granola_flow_carries_the_same_source_safety_anchors():
    """Three guides read Granola; the safety floor cannot depend on which one.

    The discovery text is deliberately duplicated (each guide is self-contained
    in the archive), and duplication drifts: the audit found the link-consent
    warning present in one copy and silently missing from the other two. This
    test pins the shared floor so a future edit to one flow fails loudly
    instead of quietly weakening it.
    """
    # Derived from the catalog, never hand-listed: a fourth flow that reads
    # Granola must not escape the floor by nobody remembering a tuple.
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
    assert READS_GRANOLA, "o catálogo não marca nenhum fluxo como leitor do Granola"
    for name in sorted(READS_GRANOLA):
        normalized = _normalized(_read(name))
        for anchor in shared_anchors:
            assert anchor in normalized, f"{name}: missing anchor {anchor!r}"


def test_agenda_guide_delivers_a_branded_html_it_never_regenerates():
    """The shell is copied, not written. That is the whole economy of it.

    Re-emitting the CSS on every run costs more tokens than the briefing
    itself, drifts off-brand a little further each time, and quietly undoes
    contrast decisions that were audited once. So the guide ships the shell as
    an asset and the agent fills one marked slot.
    """
    agenda = _read("preparar-agenda")
    normalized = _normalized(agenda)

    shell_path = _skill_files()["preparar-agenda"].parent / "assets" / "preparacao.html"
    assert shell_path.is_file()
    shell = shell_path.read_text(encoding="utf-8")

    # One slot, clearly delimited, or "replace only the content" means nothing.
    for marker in ("▼▼ CONTEÚDO", "▲▲ FIM DO CONTEÚDO", "{{STARTUP}}"):
        assert marker in shell, marker

    # Self-contained: no CDN, no webfont host, and no chance of the Granola
    # link riding along inside the delivered file.
    assert "http" not in shell

    # The accent contract, which is the part a regenerated shell always loses:
    # purple is the functional accent and orange is brand-only. On dark, purple
    # is raised — #7f2ec9 reaches only 2.8:1 there.
    assert "#7f2ec9" in shell
    assert "#ee7c38" in shell
    # The DECLARED value inside the dark block, not a hex mentioned in prose:
    # the shell explains in a comment why it does not use the chart accent
    # #a94fd6, so asserting that string would pass on the explanation alone.
    escuro = shell.split("prefers-color-scheme:dark", 1)
    assert len(escuro) == 2, "o bloco de tema escuro sumiu do shell"
    assert "--color-accent:#a670dd" in " ".join(escuro[1].split())

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


def test_the_briefing_shell_keeps_the_brand_accents_in_sync_with_the_app():
    """The shell snapshots the brand; nothing regenerates it, so pin the seams.

    `assets/preparacao.html` ships inside the uploaded package and runs in
    someone else's Claude or ChatGPT session, where `Client/src/styles.scss`
    cannot reach it — a snapshot is the right mechanism. What the snapshot
    lacks is a way to notice that the source moved: the day a brand token
    changes, the briefing silently stops matching the product it reports on,
    and the one DELIBERATE deviation below becomes indistinguishable from an
    accidental one.
    """
    # Mounted read-only by both compose files; on the host it is the real path.
    fonte = Path("/brand/styles.scss")
    if not fonte.is_file():
        fonte = Path(__file__).resolve().parents[3] / "Client" / "src" / "styles.scss"
    estilos = fonte.read_text(encoding="utf-8")
    shell = (
        _skill_files()["preparar-agenda"].parent / "assets" / "preparacao.html"
    ).read_text(encoding="utf-8")

    def token(nome: str, fonte: str) -> str:
        achado = re.search(rf"--{nome}:\s*(#[0-9a-fA-F]{{3,8}})", fonte)
        assert achado, f"token --{nome} não encontrado"
        return achado.group(1).casefold()

    # The functional accent and the brand accent travel verbatim.
    assert token("color-purple", estilos) in shell.casefold()
    assert token("color-orange", estilos) in shell.casefold()

    # The documented deviation: on dark the app raises purple to
    # `--color-accent-on-dark`, which clears 3:1 for non-text. The shell's
    # accent carries 11px text, where 4.5:1 applies and that value gives 4.18:1
    # — so the shell goes further. Pinned here so the difference stays a
    # decision instead of becoming drift.
    escuro = " ".join(shell.split("prefers-color-scheme:dark", 1)[1].split())
    assert "--color-accent:#a670dd" in escuro
    assert token("color-accent-on-dark", estilos) == "#a94fd6", (
        "o acento escuro do app mudou: reveja o desvio documentado no shell"
    )

