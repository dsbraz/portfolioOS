import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

interface PackagedSkill {
  name: string;
  title: string;
  description: string;
  writes: boolean;
}

interface BlockedSkill {
  name: string;
  title: string;
  description: string;
  reason: string;
}

// Mirrors `Server/skills/`: the published guides inside the pack, in the order of
// its index, and the workflows still kept out of it.
const PACKAGED_SKILLS: PackagedSkill[] = [
  {
    name: 'operar-portfolioos',
    title: 'Operar toda a plataforma',
    description:
      'Consulta e administra o portfolioOS pelo navegador, incluindo startups, indicadores, reuniões, executivos, dealflow, usuários, convites e links.',
    writes: true,
  },
  {
    name: 'preparar-agenda',
    title: 'Preparar agenda de uma startup',
    description:
      'Prepara conversas com uma startup usando reuniões e indicadores do portfolioOS.',
    writes: false,
  },
  {
    name: 'granola-reuniao',
    title: 'Registrar reunião de conselho',
    description:
      'Obtém uma conversa do Granola pelo MCP conectado ou por um link compartilhado e a transforma em um registro de reunião no portfolioOS, com prévia.',
    writes: true,
  },
  {
    name: 'cobrar-indicadores',
    title: 'Cobrar indicadores em falta',
    description:
      'Encontra as startups sem indicador no período, gera os links de reporte após confirmação e monta a fila de cobrança por WhatsApp.',
    writes: true,
  },
];

const BLOCKED_SKILLS: BlockedSkill[] = [
  {
    name: 'auditoria-qualitativa',
    title: 'Auditar o portfólio',
    description:
      'Analisa textos qualitativos do portfólio para encontrar riscos, contradições com indicadores e compromissos sem avanço.',
    reason:
      'Aguardando aprovação da política de trânsito de dados. Até lá, use apenas com dados de demonstração.',
  },
];

@Component({
  selector: 'app-ai',
  imports: [MatButtonModule, MatIconModule],
  templateUrl: './ai.html',
  styleUrl: './ai.scss',
})
export class Ai {
  readonly packagedSkills = PACKAGED_SKILLS;
  readonly blockedSkills = BLOCKED_SKILLS;
}
