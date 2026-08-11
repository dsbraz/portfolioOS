# PRD — IA na plataforma: skills para usuários leigos

- **Status:** Rascunho
- **Autor(es):** Matheus Donangelo
- **Audiência:** Daniel Braz e Mauricio Bueno
- **Revisores:** Daniel Braz
- **Última atualização:** 2026-08-11
- **Relacionados:** [PRD-001 — Adição unificada de indicador](001-adicao-unificada-de-indicador.md) (jornada 6.5, operabilidade por agente) · AGENTS.md, seção *Machine-readable UI* · benchmark Stripe (skills/MCP/directory)

## 1. Resumo

O time do fundo quer usar IA — Claude Cowork, ChatGPT Cowork — para operar os
fluxos recorrentes do portfolioOS: registrar reuniões a partir de transcrições,
preparar agendas, cobrar indicadores, auditar o que se esconde no
qualitativo, montar apresentações. Esta iniciativa
cria o modelo de **skills da plataforma para usuários leigos**: pacotes de
instruções que ensinam o agente de IA a operar a plataforma **pelo navegador,
com a sessão do próprio usuário** — sem terminal, sem chave de API, sem
backend novo no v1. A porta de entrada é uma **página exclusiva dentro da
plataforma que ensina a usar IA com ela**: guias passo a passo por plataforma
de IA, catálogo de skills para baixar e boas práticas de segurança.

O navegador é a **ponte**, não o fim: o conector MCP (incremento 4) é o
destino da camada de capacidade — e as skills sobrevivem à travessia, porque o
que muda é como o agente alcança os dados, não o fluxo que ele executa.

## 2. Problema e contexto

- Os fluxos recorrentes do fundo são manuais e cada pessoa improvisa seus
  próprios prompts, sem método, sem guardrails e sem reuso.
- O benchmark natural (Stripe: skills + MCP + directory) foi desenhado **para
  desenvolvedores** — CLI, `npx`, chaves de API, IDE. A audiência daqui é
  leiga: usa chat, não terminal. O modelo precisa ser adaptado, não copiado.
- A plataforma já é operável por agente via navegador: o contrato de UI
  legível por máquina está no AGENTS.md, o PRD-001 trata o agente como persona
  com critérios de aceite próprios, e o redesign recente foi conduzido — e
  verificado — por um agente operando o browser.
- **A skill de apresentações já existe e está madura**: `brq-pptx` (repositório
  `brq-ppt`) gera `.pptx` **clonando os slides do template oficial de
  marketing** ("PPT Modelo BRQ v1.2") — 45 padrões catalogados, engine de
  build com validação e avisos, e as skills irmãs `brq-brand-identity` e
  `brq-tom-de-voz`. A fidelidade à marca vem do mecanismo: slides nunca são
  montados do zero. O que falta para o caso do fundo é só a **camada de
  conteúdo do portfólio** — os dados que a plataforma guarda entrando no deck.
- O que falta, portanto, não é capacidade técnica: é **ensino e
  distribuição**. Não existe lugar onde um usuário leigo descubra o que a IA
  pode fazer com a plataforma, aprenda a configurar sua ferramenta e obtenha
  as skills.

## 3. Objetivos, métricas e dependências

- **Resultado pretendido:** qualquer pessoa do fundo, sem conhecimento
  técnico, configura sua IA e executa os fluxos recorrentes com ela — com a
  plataforma como fonte da verdade e escrita sempre confirmada por humano.
- **Como saberemos:**
  - todos os usuários ativos do fundo com ao menos uma skill instalada na sua
    ferramenta de IA;
  - as três skills do incremento 1 usadas em fluxo real (uma agenda
    preparada, uma reunião registrada via transcrição, uma auditoria rodada)
    no primeiro mês;
  - zero escritas na plataforma feitas por agente sem confirmação humana
    (guardrail — as skills exigem prévia);
  - tempo entre abrir a página educativa e concluir a primeira skill
    instalada: uma sessão, sem ajuda de terceiros.

  Medição por auto-relato do time — são três pessoas; telemetria de uso de
  skill não existe no v1 e não vale seu custo aqui.
- **Dependências:** plano das ferramentas de IA do fundo (individual vs.
  time) define se a implantação por organização entra no guia — ver pendência
  1; a skill de cobrança depende do PRD-001 implementado.

## 4. Escopo

- **Nesta iniciativa, por incremento:**
  1. **Página "IA na plataforma"** — educação (guias por ferramenta, prompts
     prontos, boas práticas) + catálogo de skills com download — **e as três
     primeiras skills**: `preparar-agenda` (só leitura), `granola-reuniao`
     (escrita com prévia obrigatória) e `auditoria-qualitativa` (só leitura —
     jornada 6.5);
  2. **Skill de cobrança de indicadores** — quem falta vem da plataforma
     (`last_reported`), link e envio pelo fluxo do PRD-001 (`wa.me` com
     telefone do cadastro). É o **nível 2 da progressão de automação** do
     PRD-001: o agente detecta, gera e enfileira; o humano confirma cada envio
     no WhatsApp. O nível 3 (a plataforma enviando sozinha, sem confirmação) é
     o futuro PRD-003 e depende de decisão de canal;
  3. **Apresentação do portfólio na identidade BRQ** — a geração **já
     existe** (`brq-pptx` + `brq-brand-identity` + `brq-tom-de-voz`); este
     incremento empacota o trio no catálogo da página e adiciona a camada de
     conteúdo do fundo: visão executiva (receita e crescimento mês a mês das
     startups), síntese do portfólio (receita, crescimento, EBITDA),
     prioridades do mês e onepage qualitativo por investida — jornada 6.6;
  4. **Conector MCP com OAuth** — o **destino** da camada de capacidade, não
     um opcional. Três forças já apontam para ele: (a) a
     `auditoria-qualitativa` custa dezenas de aberturas de registro pelo
     navegador e viraria poucas chamadas; (b) o conector MCP é o único padrão
     que Claude e ChatGPT consomem **nativamente** para leigos (conectar com
     um clique, OAuth), dissolvendo a assimetria de harness do canal
     navegador; (c) só o MCP converte as regras de contenção em **capacidade
     imposta** — ferramentas somente-leitura para skills de leitura, sessões
     revogáveis por usuário. O navegador fica como ponte até aqui; as skills
     não são retrabalho, porque o fluxo delas sobrevive — muda apenas a seção
     "como alcançar os dados".
- **Fora / depois:** leitura automatizada do WhatsApp Web (a plataforma já
  sabe quem respondeu — indicador enviado é a resposta); marketplace, CLI ou
  plugin próprio; auto-update de skills; distribuição para desenvolvedores
  (`.well-known`, `npx`) como objetivo; skills que escrevem sem confirmação
  humana; chaves de API pessoais no v1.

## 5. Personas e permissões

| Papel | Acesso | Pode |
|---|---|---|
| Administrador do fundo (leigo) | dashboard autenticada + sua ferramenta de IA | aprender na página, baixar e instalar skills, executar os fluxos com seu agente |
| Agente de IA | navegador com a sessão do usuário | tudo que o usuário pode — **não é papel novo no backend**; escrita sempre passa por confirmação do humano |
| Admin da organização de IA (se plano de time) | console da ferramenta de IA | implantar skills para o time inteiro, dispensando instalação individual |

O agente age em nome do usuário, com a sessão dele — auditoria e permissão são
as do usuário. A página é autenticada: faz parte da plataforma, não é site
público.

**As ferramentas de IA não são equivalentes no canal navegador** — e o v1
precisa tratar isso com honestidade:

| Ferramenta | Como opera o navegador | Implicação para o browser-first |
|---|---|---|
| Claude (Cowork + extensão Chrome) | o navegador **real** do usuário, na sessão já autenticada | é o modelo como descrito neste PRD — comprovado nesta própria plataforma |
| ChatGPT (modo agente) | navegador **virtual na nuvem**, que não é o do usuário | o usuário precisa autenticar dentro do navegador do agente — sessão e postura de segurança diferentes; o guia da página deve dizer isso sem eufemismo |

O conector MCP do incremento 4 dissolve a assimetria: é padrão nativo de
conexão nas duas ferramentas. Até lá, a pendência 3 define qual harness é o
primário do v1.

## 6. Jornadas

### 6.1 Aprender a usar IA com a plataforma (a página)

- **Ator / gatilho:** administrador leigo, pelo item "IA na plataforma" na
  navegação.
- **Fluxo:** abre a página → entende em linguagem simples o que a IA pode
  fazer com a plataforma → escolhe sua ferramenta (Claude ou ChatGPT) → segue
  o guia passo a passo de configuração → copia um prompt pronto para começar.
- **Regras / invariantes:** linguagem leiga, sem jargão técnico; conteúdo em
  PT-BR; as boas práticas de segurança são parte do conteúdo, não rodapé.
- **Critérios de aceite:**
  - [ ] A página é acessível pela navegação principal da plataforma.
  - [ ] Há um guia passo a passo por ferramenta (Claude e ChatGPT), do zero
        até a primeira skill funcionando.
  - [ ] Há prompts prontos copiáveis por skill ("Prepare minha agenda com a
        [startup]…").
  - [ ] As boas práticas aparecem com destaque: revisar antes de o agente
        salvar; o link de indicador é um segredo; nunca digitar senha no chat.
  - [ ] Uma pessoa sem conhecimento técnico completa o guia sem ajuda
        (validado com um usuário real antes do lançamento).

### 6.2 Instalar uma skill

- **Ator / gatilho:** administrador leigo, no catálogo da página.
- **Fluxo:** lê o que a skill faz e quando usar → baixa o pacote → adiciona na
  sua ferramenta seguindo a instrução da própria página → testa com o prompt
  pronto.
- **Regras / invariantes:** cada skill descreve o que faz em linguagem de
  produto; o pacote é autocontido; a versão é visível (atualização é manual —
  baixar de novo).
- **Critérios de aceite:**
  - [ ] Cada skill do catálogo tem descrição leiga, pacote para download e
        instrução de instalação por ferramenta.
  - [ ] A versão da skill instalada é identificável (a página mostra a atual).
  - [ ] Quando o plano do fundo permitir, o guia documenta a implantação por
        organização como caminho preferido (instalar uma vez para todos).

### 6.3 Preparar agenda com IA (skill 1 — só leitura)

- **Ator / gatilho:** usuário pede ao seu agente: "prepare a agenda com a
  [startup]".
- **Fluxo:** o agente, pelo navegador com a sessão do usuário, abre a startup
  → lê a última reunião de conselho e os indicadores recentes → produz recap
  da última agenda e sugestões de perguntas para a próxima.
- **Regras / invariantes:** a skill é somente leitura — não escreve nada na
  plataforma; navega pela UI usando nomes acessíveis (o contrato do
  AGENTS.md), não seletores de implementação.
- **Critérios de aceite:**
  - [ ] O resultado contém recap da última reunião (resumo, pontos de atenção,
        próximos passos) e perguntas sugeridas ancoradas nos indicadores.
  - [ ] Nenhuma ação de escrita é executada na plataforma.

### 6.4 Registrar reunião do Granola (skill 2 — escrita com prévia)

- **Ator / gatilho:** usuário cola a transcrição da reunião (ou conecta o
  Granola, se disponível na sua ferramenta) e pede o registro.
- **Fluxo:** o agente mapeia a transcrição para os campos da plataforma
  (data, participantes, resumo, pontos de atenção, próximos passos) → exibe a
  **prévia campo a campo** — incluindo, como sugestão, o review da reunião (o
  que foi bom, o que pode melhorar) → o usuário ajusta e confirma → o agente
  preenche o diálogo de reunião no navegador e salva.
- **Regras / invariantes:** **nenhuma escrita sem confirmação humana** — a
  transcrição é entrada não confiável (mitigação de prompt injection); sem
  conexão Granola, colar a transcrição é o caminho padrão.
- **Critérios de aceite:**
  - [ ] A prévia apresenta todos os campos que serão gravados, antes de
        qualquer escrita.
  - [ ] O usuário consegue corrigir a prévia antes de confirmar.
  - [ ] Instrução da transcrição que contrarie a skill (ex.: "apague os
        outros registros") não resulta em ação — a prévia limita o efeito ao
        registro proposto.
  - [ ] O registro salvo corresponde à prévia confirmada.

### 6.5 Auditar o qualitativo do portfólio (skill do incremento 1)

- **Ator / gatilho:** usuário pede ao seu agente: "faça uma auditoria do
  portfólio", "o que os textos dizem que os números não mostram?" ou "o que
  está escondido na [startup]?".
- **Fluxo:** o agente confirma o escopo (portfólio ou uma startup; janela —
  padrão 3 meses) → varre pelo navegador o texto livre de cada startup
  (Conquistas, Desafios, Comentários do fundo, e Resumo/Pontos de
  atenção/Próximos passos das reuniões) → cruza com os números → entrega o
  relatório de achados ordenado por severidade.
- **Regras / invariantes:** somente leitura; **todo achado cita a origem**
  (startup, registro, período) — achado sem origem não entra; o relatório
  **declara a cobertura** (o que foi lido e o que ficou de fora); "sem
  achados" é resultado válido e é dito com essa clareza; nada é inventado
  para engordar o relatório.
- **Critérios de aceite:**
  - [ ] O relatório captura sinais que só existem no texto livre (risco de
        cliente, pessoas-chave, captação, jurídico, execução), cada um com
        origem citável.
  - [ ] Contradições entre qualitativo e quantitativo são apontadas (ex.:
        "mês excelente" com receita em queda; desafio grave com status
        Saudável).
  - [ ] Compromisso repetido em reuniões seguidas sem resolução aparece como
        achado de execução, com as datas.
  - [ ] Startup que parou de preencher o qualitativo aparece como achado de
        silêncio, com a data do último registro.
  - [ ] A seção de cobertura lista startups varridas, registros lidos e o que
        ficou fora da janela.
  - [ ] Nenhuma ação de escrita é executada na plataforma.

### 6.6 Gerar apresentação do portfólio (skill do incremento 3)

- **Ator / gatilho:** usuário pede ao seu agente: "monte a apresentação do
  portfólio de [mês]" ou "monte o onepage da [startup]".
- **Fluxo:** o agente lê os dados na plataforma (indicadores mês a mês,
  resumo do portfólio, reuniões recentes) → estrutura o deck com o usuário →
  gera o `.pptx` **pela skill `brq-pptx`**, clonando os slides do template
  oficial → roda o build até zerar avisos → entrega o arquivo para revisão.
- **Regras / invariantes:** **a identidade BRQ é inegociável e vem do
  mecanismo, não de esforço** — todo slide é clone do template oficial de
  marketing ("PPT Modelo BRQ v1.2"); slides nunca são montados do zero; o
  texto segue o tom de voz BRQ (`brq-tom-de-voz`). Dados quantitativos vêm
  **sempre da plataforma**; o que a plataforma não guarda (ex.: prioridades do
  mês) é **perguntado ao usuário, nunca inventado**.
- **Critérios de aceite:**
  - [ ] O deck é gerado exclusivamente pela skill `brq-pptx` — nenhum slide
        montado fora do template oficial.
  - [ ] A visão executiva traz receita e crescimento mês a mês das startups e
        a síntese de receita, crescimento e EBITDA, com números idênticos aos
        da plataforma no período.
  - [ ] O onepage por investida tem 3–4 pontos qualitativos ancorados em
        reuniões e indicadores registrados — com origem citável.
  - [ ] Conteúdo que a plataforma não guarda é solicitado ao usuário antes da
        geração; nada é inventado para preencher slide.
  - [ ] O build termina sem avisos pendentes (ou com cada um justificado), e
        o arquivo abre corretamente no PowerPoint.

## 7. Regras transversais

- **Escrita sempre confirmada:** nenhuma skill grava na plataforma sem prévia
  aprovada pelo humano. É a regra de segurança e a defesa contra instruções
  maliciosas embutidas em conteúdo externo (transcrições, mensagens).
- **Sem credenciais no chat:** as skills nunca pedem senha ou token; o agente
  usa a sessão já autenticada do navegador. A página ensina isso como boa
  prática explícita.
- **A plataforma é a fonte da verdade:** estado (quem reportou, o que foi
  registrado) sempre vem dela — nunca de leitura de canais externos.
- **Operabilidade é requisito de UI:** as skills navegam por nomes acessíveis
  e estados textuais; a seção *Machine-readable UI* do AGENTS.md é o contrato
  que as sustenta. Regressão de acessibilidade é regressão de skill.
- **Limite aceito do v1 — a contenção é por instrução, não por capacidade:**
  o agente navega com a sessão completa do usuário; "somente leitura" e
  "prévia obrigatória" são regras escritas na skill, que a plataforma não tem
  como impor. A contenção real do v1 é o humano na confirmação. Contenção
  imposta por capacidade (ferramentas somente-leitura, escopo por skill,
  revogação por sessão) chega com o MCP — é uma das três forças do
  incremento 4, não um detalhe.

## 8. Casos de borda e exceções

| Situação | Comportamento esperado |
|---|---|
| Usuário sem plano de time na ferramenta de IA | o guia cobre a instalação individual (upload do pacote) |
| A ferramenta de IA muda seus menus | instruções escritas por objetivo ("adicione o arquivo em Skills"), com capturas atualizáveis; a página indica a versão do guia |
| Agente sem acesso a navegador | a skill declara o pré-requisito e orienta usar uma ferramenta com navegador; não tenta caminho alternativo |
| Transcrição contém instruções para o agente | a prévia obrigatória limita qualquer efeito ao registro proposto; nada além dele é executado |
| UI da plataforma muda e quebra uma skill | o teste de operabilidade por nomes acessíveis (PRD-001/AGENTS.md) acusa antes; skills versionadas na página |
| Usuário pede ação que a skill não cobre | o agente faz apenas o que a skill descreve e diz o que ficou de fora |
| Sessão da plataforma expira no meio de um fluxo longo (ex.: auditoria) | o agente para, pede que o usuário entre de novo e retoma de onde parou — nunca lida com a senha |

## 9. Decisões funcionais

| Tema | Decisão fechada |
|---|---|
| Audiência | usuários leigos em ferramentas de chat (Claude Cowork, ChatGPT Cowork); terminal e CLI fora do modelo |
| Capacidade no v1 | **browser-first**: o agente opera a UI com a sessão do usuário; zero backend novo |
| Educação | página exclusiva **dentro da plataforma**, parte do produto — não documentação externa |
| Distribuição | download na página + implantação por organização quando o plano permitir |
| Escrita | sempre com prévia e confirmação humana, em toda skill, sem exceção |
| Cobrança | estado vem da plataforma (`last_reported`); envio pelo fluxo do PRD-001; **sem leitura de WhatsApp Web** |
| MCP | fora do v1, mas é o **destino declarado** da camada de capacidade (velocidade da auditoria, paridade de harness, contenção por capacidade); o navegador é a ponte, e as skills sobrevivem à transição |
| Apresentações | geradas **exclusivamente pela skill `brq-pptx` existente**, que clona o template oficial de marketing — identidade BRQ garantida pelo mecanismo; slides do zero são proibidos |
| Conteúdo de deck | quantitativo sempre da plataforma; o que ela não guarda é perguntado ao usuário, nunca inventado |
| Idioma | skills e página em PT-BR |

### 9.1 Pendências

| # | Decisão | Opções | Quem decide | Bloqueia entrega? |
|---|---|---|---|---|
| 1 | Plano das ferramentas de IA do fundo | individual · time (habilita implantação por organização) | Daniel Braz | Não — a página cobre os dois caminhos |
| 2 | Conexão nativa com Granola | v1 com transcrição colada · integrar conector Granola quando disponível na ferramenta | Produto | Não — colar transcrição é o caminho padrão do v1 |
| 3 | Harness primário do v1 | Claude (recomendado: opera o navegador real do usuário e consome o formato de skill nativamente; comprovado nesta plataforma) · ChatGPT · os dois com a mesma profundidade | Daniel Braz | Não — o guia nasce para o primário e o outro entra como secundário até o MCP igualar |
| 4 | Política de trânsito de dados | executar skills envia dados do portfólio — **inclusive as anotações do fundo** — para a ferramenta de IA do usuário; aprovar formalmente esse trânsito e em qual plano/conta ele ocorre | Daniel Braz | **Sim para a `auditoria-qualitativa`** (a skill que mais expõe conteúdo sensível); não para as demais |

## 10. Referências

- Discussão interna sobre skills (2026-08 — Matheus e gestor da plataforma):
  origem das quatro skills e da página de configuração.
- Benchmark Stripe — [Agent skills](https://docs.stripe.com/skills),
  [MCP](https://docs.stripe.com/mcp) e o índice
  `/.well-known/skills/index.json`: modelo de três camadas
  (conhecimento/capacidade/descoberta), desenhado para desenvolvedores e aqui
  adaptado para audiência leiga.
- [Agent Skills](https://agentskills.io/home) — formato aberto dos pacotes.
- PRD-001, jornada 6.5 — o agente como persona e o fluxo `wa.me` que a skill
  de cobrança reutiliza.
- Skill `brq-pptx` (repositório `brq-ppt`, com `brq-brand-identity` e
  `brq-tom-de-voz`): engine de geração de `.pptx` por clonagem do template
  oficial "PPT Modelo BRQ v1.2", 45 padrões catalogados com previews, build
  com validação — a base pronta do incremento 3.
- Skills do incremento 1 **já construídas** no repositório:
  `skills/preparar-agenda`, `skills/granola-reuniao`,
  `skills/auditoria-qualitativa` e `skills/README.md` — escritas contra a UI
  real e com as regras transversais embutidas.
- AGENTS.md, seção *Machine-readable UI* — o contrato de operabilidade.
- Evidência prática: o redesign BRQ desta plataforma foi conduzido e
  verificado por um agente operando o navegador — o canal browser-first não é
  hipótese.
