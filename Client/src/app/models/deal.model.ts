export enum DealStage {
  NEW = 'novo',
  TALKING = 'conversando',
  ANALYZING = 'analisando',
  COMMITTEE = 'comite',
  INVESTED = 'investido',
  ARCHIVED = 'arquivado',
}

export const DEAL_STAGE_CONFIG: Record<
  DealStage,
  { label: string; color: string }
> = {
  [DealStage.NEW]: { label: 'Novo', color: 'var(--app-stage-new)' },
  [DealStage.TALKING]: { label: 'Conversando', color: 'var(--app-stage-talking)' },
  [DealStage.ANALYZING]: { label: 'Analisando', color: 'var(--app-stage-analyzing)' },
  [DealStage.COMMITTEE]: { label: 'Comite', color: 'var(--app-stage-committee)' },
  [DealStage.INVESTED]: { label: 'Investido', color: 'var(--app-stage-invested)' },
  [DealStage.ARCHIVED]: { label: 'Arquivado', color: 'var(--app-stage-archived)' },
};

export const FUNDING_ROUND_OPTIONS = [
  'Pre-Seed',
  'Seed',
  'Series A',
  'Series B',
  'Series C+',
];

export interface Deal {
  id: string;
  company: string;
  sector: string | null;
  funding_round: string | null;
  founders: string | null;
  stage: DealStage;
  notes: string | null;
  next_step: string | null;
  internal_owner: string | null;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface DealListResponse {
  items: Deal[];
  total: number;
}

export interface DealCreate {
  company: string;
  sector?: string | null;
  funding_round?: string | null;
  founders?: string | null;
  stage?: DealStage;
  notes?: string | null;
  next_step?: string | null;
  internal_owner?: string | null;
}

export interface DealUpdate {
  company?: string;
  sector?: string | null;
  funding_round?: string | null;
  founders?: string | null;
  stage?: DealStage;
  position?: number;
  notes?: string | null;
  next_step?: string | null;
  internal_owner?: string | null;
}
