# PRD — Adição unificada de indicador mensal

- **Status:** Rascunho
- **Autor(es):** Matheus Donangelo
- **Audiência:** Daniel Braz e Mauricio Bueno
- **Revisores:** Daniel Braz
- **Última atualização:** 2026-08-11
- **Relacionados:** [RFC-001 — Adição unificada de indicador](../rfc/001-adicao-unificada-de-indicador.md) · [PRD-002 — IA na plataforma](002-ia-na-plataforma.md) (níveis 2 e 3 da progressão de automação) · PR do redesign BRQ ([#1](https://github.com/dsbraz/portfolioOS/pull/1))

## 1. Resumo

Hoje existem duas ações separadas para o mesmo fim — registrar o indicador
mensal de uma startup investida: "Adicionar indicador" (o administrador digita)
e "Gerar link" (a investida preenche por um formulário público). Elas moram em
lugares diferentes da tela, com formulários, validações e períodos-padrão
divergentes. Esta entrega unifica a adição em **um único ponto de entrada**: o
administrador escolhe o período e então decide se preenche agora ou gera um
link para a investida responder. Os campos reportáveis passam a ter o mesmo
contrato e a mesma validação nos dois caminhos, e o campo de comentários é
formalizado como **anotação exclusiva do fundo**.

O envio do link também entra no produto: o painel do link gerado oferece
**enviar por WhatsApp** (click-to-chat oficial, `wa.me`), com o destinatário
vindo dos executivos cadastrados da startup. O fluxo inteiro — gerar o link e
enviá-lo — é desenhado para ser **operável por um agente de IA** com acesso ao
navegador ou à sessão do administrador, usando apenas semântica acessível.

## 2. Problema e contexto

A dupla atuação é a mesma ação feita por pessoas diferentes: preenchida pelo
CEO da investida (via link) ou pelo usuário da dashboard (via diálogo). A
implementação atual trata como duas funcionalidades independentes:

- **"Gerar link" mora no cabeçalho da página**, entre ações de startup (Editar,
  Excluir), e aparece até quando a aba ativa é Reuniões ou Executivos.
  "Adicionar indicador" mora na barra da seção. O administrador escolhe o
  caminho antes de ter contexto do período.
- **A validação é assimétrica sobre os mesmos dados.** O formulário público
  valida limites de valores; o diálogo do administrador não valida nada no
  cliente. Foi por esse caminho que um valor de −999 bilhões chegou ao banco
  durante testes internos.
- **Os períodos-padrão divergem**: o diálogo abre no mês corrente, o link no
  mês anterior.
- **`comments` não distingue autoria.** Aparece ao lado de "Conquistas" e
  "Desafios" como se fosse o mesmo tipo de texto, mas por decisão de produto é
  anotação interna do fundo — a investida não a vê nem a preenche.
- **O envio do link acontece fora do produto.** Gerar copia para a área de
  transferência e o resto é colar em algum canal por conta própria — sem
  destinatário sugerido, com um link que é um segredo portador. E a área de
  transferência é invisível para automação: um agente que gere o link hoje não
  tem como lê-lo nem enviá-lo.

## 3. Objetivos, métricas e dependências

- **Resultado pretendido:** o administrador realiza as duas variantes da ação a
  partir de um único ponto, com contexto do período antes da escolha; nenhum
  registro passa a existir com valores que um dos caminhos rejeitaria; o envio
  do link à investida acontece dentro do produto e pode ser executado de ponta
  a ponta por um agente de IA agindo pela sessão do administrador.
- **Como saberemos:**
  - zero indicadores novos com valores fora dos limites compartilhados
    (guardrail: validação simétrica nos dois formulários);
  - zero ocorrências da anotação do fundo em payload ou resposta do fluxo
    público (teste de contrato);
  - sem regressão no volume de links gerados por mês (proxy de que o modo
    "gerar link" continua descobrível dentro do novo fluxo);
  - o fluxo gerar→enviar é completável por um agente de navegador usando
    apenas papéis e nomes acessíveis — verificado por teste automatizado que
    percorre o fluxo dessa forma, sem seletores de implementação.
- **Dependências:** decisões da seção 9.1; nenhuma dependência externa.

## 4. Escopo

- **Nesta entrega:**
  1. contrato único da zona reportada (campos e validação) nos dois formulários;
  2. entrada única "Adicionar indicador" com escolha de modo (preencher agora ·
     gerar link) e contexto do período;
  3. anotação do fundo como seção própria na edição e na leitura;
  4. período-padrão unificado (mês anterior);
  5. painel do link gerado com **envio por WhatsApp** (`wa.me`), destinatário
     vindo dos executivos da startup;
  6. **operabilidade por agente**: o fluxo gerar→enviar executável por
     automação de navegador, sem depender de área de transferência.
- **Fora / depois:** expiração e revogação de link; registro de procedência
  (quem escreveu o quê) e fila de aprovação; tabela orientada a períodos
  pendentes; notificações enviadas pelo servidor; integração com a API do
  WhatsApp Business; envio automático agendado; rastreio de entrega da
  mensagem; qualquer mudança de API.

**Progressão planejada.** Esta entrega é o **nível 1** de três: manual
unificado (este PRD) → assistido por agente (PRD-002, skill de cobrança) →
automação pela plataforma (futuro PRD-003: job que detecta quem não reportou,
gera os links e envia). Não é escopo concorrente — as primitivas daqui são
desenhadas para os três níveis consumirem: link idempotente por período,
mensagem canônica como função pura, telefone normalizado do cadastro e
`last_reported` como fonte de quem falta. O nível 3 exige uma decisão de canal
que não pertence a este PRD (`wa.me` requer confirmação humana; envio autônomo
pede WhatsApp Business API, e-mail, ou o meio-termo "preparado pelo job,
disparado com um clique").

## 5. Personas e permissões

| Papel | Acesso | Pode |
|---|---|---|
| Administrador do fundo | dashboard autenticada | criar/editar/excluir indicador; gerar link; enviar por WhatsApp; escrever a anotação do fundo (criação e edição) |
| Fundador/CEO da investida | link público, sem autenticação | ver os valores já reportados do próprio período; enviar/reenviar a zona reportada |
| Agente de IA | navegador com a sessão do administrador | tudo que o administrador pode; **não é um papel novo no backend** |

O agente age em nome do administrador, com a mesma sessão e as mesmas
permissões. O requisito que ele impõe ao produto não é de autorização, é de
**operabilidade**: cada passo do fluxo precisa ser executável por semântica
acessível — nomes estáveis, resultados visíveis como texto, sem CAPTCHA e sem
depender da área de transferência.

Onde o controle deve **sumir** (não basta bloquear no backend):

- o campo de anotação do fundo **não é renderizado** no formulário público nem
  retornado no contexto público;
- "Gerar link" **deixa de existir** como ação do cabeçalho da página.

## 6. Jornadas

### 6.1 Adicionar indicador (entrada única)

- **Ator / gatilho:** administrador, na aba Indicadores da startup, ação
  "Adicionar indicador".
- **Fluxo:** o diálogo abre com o período (padrão: mês anterior) → exibe o
  contexto do período (já tem indicador? já tem link?) → o administrador
  escolhe o modo: **Preencher agora** (campos reportados + anotação do fundo)
  ou **Gerar link para a investida** → confirma → a tabela recarrega ou o
  painel do link abre (jornada 6.5).
- **Regras / invariantes:** período futuro é bloqueado; existe no máximo um
  link por (startup, período) — repetir devolve o existente; trocar de modo não
  descarta o que já foi digitado; salvar sobre período existente substitui
  campo a campo (campos vazios não apagam valor existente).
- **Critérios de aceite:**
  - [ ] "Gerar link" não existe mais como ação separada no cabeçalho.
  - [ ] O diálogo abre com o período padrão igual ao mês anterior ao corrente.
  - [ ] Alternar entre os modos preserva o período e os campos já digitados.
  - [ ] Se o período já possui indicador, um aviso identifica isso antes do envio.
  - [ ] Se o período já possui link, o modo link informa e devolve o mesmo link.
  - [ ] Período futuro é recusado com mensagem, no cliente e no servidor.
  - [ ] No modo link, confirmar gera o link e abre o painel do link — com o
        link **visível como texto selecionável**, não apenas na área de
        transferência.

### 6.2 Responder pelo link (investida)

- **Ator / gatilho:** fundador/CEO, ao abrir o link recebido.
- **Fluxo:** vê a identificação da startup e do período → preenche a zona
  reportada (valores já enviados aparecem pré-preenchidos) → envia → confirmação.
- **Regras / invariantes:** a validação da zona reportada é idêntica à do
  administrador; a anotação do fundo não aparece nem é aceita; reenvio
  substitui campo a campo e **preserva a anotação do fundo**.
- **Critérios de aceite:**
  - [ ] Todo valor recusado pelo formulário do administrador é recusado pelo
        formulário público, e vice-versa.
  - [ ] O payload público não aceita o campo de anotação; o contexto público
        não o retorna.
  - [ ] Reenvio da investida preserva a anotação do fundo existente.

### 6.3 Editar e anotar (administrador)

- **Ator / gatilho:** administrador, ação Editar em um indicador da tabela.
- **Fluxo:** o formulário de edição apresenta a zona reportada e, separada, a
  seção "Anotações do fundo" → salva.
- **Regras / invariantes:** a validação é a mesma da criação e do formulário
  público; a anotação é editável em qualquer indicador, inclusive nos enviados
  pela investida.
- **Critérios de aceite:**
  - [ ] "Anotações do fundo" é uma seção própria, visualmente separada dos
        campos reportados.
  - [ ] A zona reportada aplica os mesmos limites da criação e do público.

### 6.4 Ler indicador

- **Ator / gatilho:** administrador, clique na linha da tabela.
- **Fluxo:** vista de leitura com Período, Quantitativos, Qualitativos e
  Anotações do fundo.
- **Critérios de aceite:**
  - [ ] A leitura separa a zona reportada da anotação do fundo.
  - [ ] Valor ausente é apresentado como "Não informado" (inclusive para
        leitores de tela).

### 6.5 Enviar o link por WhatsApp (humano ou agente)

- **Ator / gatilho:** administrador — ou um agente de IA operando com a sessão
  dele — a partir do painel do link gerado (jornada 6.1, modo link).
- **Fluxo:** escolhe o destinatário entre os executivos da startup que possuem
  telefone cadastrado → vê a mensagem padrão (saudação com o primeiro nome do
  destinatário, mês de referência e link) e o número normalizado → aciona
  "Enviar por WhatsApp" → o WhatsApp abre pelo click-to-chat oficial (`wa.me`)
  com a mensagem pré-preenchida → quem opera confirma o envio no próprio
  WhatsApp.
- **Regras / invariantes:** o destinatário vem **exclusivamente do telefone
  cadastrado na plataforma** (executivos da startup) — não existe entrada de
  número avulso; telefone novo se cadastra no executivo, e o cadastro é a fonte
  da verdade de contato. O produto exibe destinatário (nome e número) antes de
  abrir o WhatsApp — a mensagem carrega um segredo portador; a mensagem é
  editável no WhatsApp antes do envio; o produto não rastreia entrega; número
  não normalizável é recusado com orientação para corrigir o cadastro.
- **Critérios de aceite:**
  - [ ] O link gerado permanece visível como texto no painel — nenhum passo do
        fluxo depende da área de transferência.
  - [ ] "Enviar por WhatsApp" é um link real (`href` para `wa.me` presente no
        DOM antes do clique), com nome acessível que identifica o destinatário.
  - [ ] A mensagem pré-preenchida segue o modelo padrão do fundo — saudação
        com o **primeiro nome** do destinatário, mês de referência e link do
        formulário:

        > Olá [Primeiro nome]. Tudo bem?
        > Segue o link para atualizações dos dados referentes a
        > [mês de referência]: [link do formulário]
        > Obrigado
  - [ ] Número brasileiro sem código do país é normalizado para +55; número
        inválido é recusado com orientação para corrigir o cadastro do
        executivo.
  - [ ] O painel não oferece entrada de número avulso — o destinatário vem
        sempre do cadastro.
  - [ ] Startup sem executivo com telefone: o painel explica e orienta a
        cadastrar o telefone do responsável na aba Executivos; o envio fica
        indisponível até lá.
  - [ ] Um agente de navegador completa gerar→enviar usando apenas papéis e
        nomes acessíveis, verificado por teste que percorre o fluxo dessa
        forma.

## 7. Regras transversais

- **Confidencialidade da anotação:** a anotação do fundo é dado interno; nunca
  transita pelo fluxo público (formulário, payload ou resposta).
- **O link é um segredo portador:** quem o possui escreve no período. Sem
  expiração no v1 (pendência 1); a mitigação é o escopo estreito — um link só
  escreve na zona reportada de um único período de uma única startup.
- **Envio consciente:** por carregar um segredo portador, o envio sempre exibe
  o destinatário (nome e número normalizado) antes de abrir o WhatsApp.
  Telefones não entram em URLs do próprio produto; `wa.me` é o destino externo
  oficial do click-to-chat.
- **Operabilidade por agente:** o fluxo gerar→enviar é um contrato de máquina,
  na linha da seção *Machine-readable UI* do AGENTS.md — ações com nome
  acessível estável, resultados como texto no DOM, confirmações em
  `role="status"`, sem CAPTCHA, sem diálogo nativo do navegador e sem depender
  da área de transferência.

## 8. Casos de borda e exceções

| Situação | Comportamento esperado |
|---|---|
| Período futuro selecionado | recusado no cliente e no servidor |
| Salvar sobre período que já tem indicador | aviso prévio; substituição campo a campo; vazio não apaga |
| Gerar link para período que já tem link | devolve o mesmo link, com aviso |
| Link inválido | página pública informa indisponibilidade, sem detalhes internos |
| Investida reenvia após edição do administrador | última escrita vence na zona reportada; anotação preservada |
| Envio público totalmente em branco | aceito no v1; o período conta como reportado (pendência 3) |
| Administrador exclui indicador de período com link emitido | o link continua válido e um reenvio cria novo registro |
| Startup sem executivo com telefone | painel explica e orienta o cadastro na aba Executivos; envio indisponível até lá |
| Telefone cadastrado não normalizável | recusado com orientação para corrigir o cadastro; o WhatsApp não abre |
| WhatsApp aberto mas mensagem não enviada | fora do alcance do produto; o link permanece no painel para nova tentativa |

## 9. Decisões funcionais

| Tema | Decisão fechada |
|---|---|
| Anotação do fundo | `comments` é exclusiva do administrador, na criação e na edição; nunca exposta no fluxo público |
| Entrada única | uma só ação "Adicionar indicador"; o modo (preencher agora · gerar link) é escolhido dentro do diálogo, depois do período |
| Zona reportada | mesmo conjunto de campos e mesma validação nos dois formulários |
| Período padrão | mês anterior ao corrente — mesma convenção do monitoramento, que abre no mês fechado |
| Concorrência (v1) | última escrita vence, campo a campo; sem fila de aprovação |
| Link por período | no máximo um por (startup, período); repetir devolve o existente |
| API | nenhum endpoint novo; a unificação é de experiência e contrato de campos |
| Canal de envio | click-to-chat oficial do WhatsApp (`wa.me/<número>?text=…`), aberto no navegador; sem WhatsApp Business API no v1 |
| Destinatário | **exclusivamente o telefone cadastrado na plataforma** (executivos da startup); sem número avulso — telefone novo se cadastra no executivo, mantendo a plataforma como fonte da verdade de contato |
| Mensagem | o modelo padrão do fundo, hoje já em uso: "Olá [Primeiro nome]. Tudo bem? / Segue o link para atualizações dos dados referentes a [mês de referência]: [link do formulário] / Obrigado" — quem envia edita no próprio WhatsApp antes de confirmar |
| Agente de IA | age com a sessão do administrador; não existe papel novo nem credencial própria no backend |
| Rastreio de entrega | fora do produto; o envio se conclui dentro do WhatsApp |

### 9.1 Pendências

| # | Decisão | Opções | Quem decide | Bloqueia entrega? |
|---|---|---|---|---|
| 1 | Expiração do link | nunca (atual) · 30 dias · fim do mês seguinte; com ou sem revogação manual | Produto/CTO | Não — v1 mantém sem expiração. **Atenção:** a automação planejada (PRD-003) cunha links todo mês; sem expiração, o estoque de segredos portadores válidos só cresce — quando a automação vier, expirar deixa de ser opcional |
| 2 | Aviso de sobrescrita e procedência | manter silencioso (atual) · avisar no reenvio · registrar origem (manual/formulário) | Produto/CTO | Não |
| 3 | Envio público em branco | aceitar (atual) · exigir ao menos um campo | Produto/CTO | Não |
| 4 | Responsável pelo report como contato formal | escolher a cada envio entre os executivos com telefone (v1) · marcar um executivo como "responsável" da startup, pré-selecionado no envio | Produto/CTO | Não — v1 lista e o administrador escolhe |

## 10. Referências

- Incidente interno (2026-08-06): valor de −999 bilhões aceito pelo caminho do
  administrador durante testes — evidência da assimetria de validação.
- Comportamento vigente do backend: substituição campo a campo em período
  existente; unicidade de link por período; contexto público sem `comments`.
- Convenção de período do monitoramento (abre no mês anterior).
- WhatsApp — Click to Chat (formato oficial `wa.me/<número>?text=…`):
  https://faq.whatsapp.com/5913398998672934
- AGENTS.md, seção *Machine-readable UI* — contrato de operabilidade que a
  jornada 6.5 estende ao fluxo de envio.
