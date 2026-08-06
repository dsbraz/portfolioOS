export enum StartupStatus {
  HEALTHY = 'saudavel',
  WARNING = 'atencao',
  CRITICAL = 'critico',
}

/**
 * Gravidade do status, para ordenação. O status é ORDINAL, não alfabético:
 * ordenar por rótulo daria "Atenção, Crítico, Saudável", que não é ordem
 * nenhuma. Crescente traz o mais saudável primeiro.
 */
export const STARTUP_STATUS_SEVERITY: Record<StartupStatus, number> = {
  [StartupStatus.HEALTHY]: 0,
  [StartupStatus.WARNING]: 1,
  [StartupStatus.CRITICAL]: 2,
};

export interface Startup {
  id: string;
  name: string;
  site: string | null;
  logo_url: string | null;
  status: StartupStatus;
  sector: string;
  investment_date: string;
  equity_stake: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface StartupListResponse {
  items: Startup[];
  total: number;
}

export interface StartupCreate {
  name: string;
  site?: string | null;
  logo_url?: string | null;
  status?: StartupStatus;
  sector: string;
  investment_date: string;
  equity_stake?: number | null;
  notes?: string | null;
}

export interface StartupUpdate {
  name?: string;
  site?: string | null;
  logo_url?: string | null;
  status?: StartupStatus;
  sector?: string;
  investment_date?: string;
  equity_stake?: number | null;
  notes?: string | null;
}

/** Status tone. Drives the `.pill--*` class, which pairs the text color with
 *  its matching tint so the contrast ratio holds in both themes. */
export type StatusTone = 'good' | 'warn' | 'danger';

export const STARTUP_STATUS_CONFIG: Record<
  StartupStatus,
  { label: string; color: string; icon: string; tone: StatusTone }
> = {
  [StartupStatus.HEALTHY]: {
    label: 'Saudável',
    color: 'var(--app-status-healthy)',
    icon: 'check_circle',
    tone: 'good',
  },
  [StartupStatus.WARNING]: {
    label: 'Atenção',
    color: 'var(--app-status-warning)',
    icon: 'warning',
    tone: 'warn',
  },
  [StartupStatus.CRITICAL]: {
    label: 'Crítico',
    color: 'var(--app-status-critical)',
    icon: 'error',
    tone: 'danger',
  },
};
