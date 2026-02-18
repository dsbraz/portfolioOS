export enum DealColumn {
  NEW = 'novo',
  TALKING = 'conversando',
  ANALYZING = 'analisando',
  COMMITTEE = 'comite',
  INVESTED = 'investido',
  ARCHIVED = 'arquivado',
}

export const DEAL_COLUMN_CONFIG: Record<
  DealColumn,
  { label: string; color: string }
> = {
  [DealColumn.NEW]: { label: 'Novo', color: 'var(--app-column-new)' },
  [DealColumn.TALKING]: { label: 'Conversando', color: 'var(--app-column-talking)' },
  [DealColumn.ANALYZING]: { label: 'Analisando', color: 'var(--app-column-analyzing)' },
  [DealColumn.COMMITTEE]: { label: 'Comite', color: 'var(--app-column-committee)' },
  [DealColumn.INVESTED]: { label: 'Investido', color: 'var(--app-column-invested)' },
  [DealColumn.ARCHIVED]: { label: 'Arquivado', color: 'var(--app-column-archived)' },
};

export const DEAL_STAGE_OPTIONS = [
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
  stage: string | null;
  founders: string | null;
  column: DealColumn;
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
  stage?: string | null;
  founders?: string | null;
  column?: DealColumn;
  notes?: string | null;
  next_step?: string | null;
  internal_owner?: string | null;
}

export interface DealUpdate {
  company?: string;
  sector?: string | null;
  stage?: string | null;
  founders?: string | null;
  column?: DealColumn;
  notes?: string | null;
  next_step?: string | null;
  internal_owner?: string | null;
}

export interface DealMoveRequest {
  column: DealColumn;
  position: number;
}
