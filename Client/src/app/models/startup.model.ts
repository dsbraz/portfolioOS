export enum StartupStatus {
  HEALTHY = 'saudavel',
  WARNING = 'atencao',
  CRITICAL = 'critico',
}

export interface Startup {
  id: string;
  name: string;
  site: string | null;
  logo_url: string | null;
  status: StartupStatus;
  sector: string;
  investment_date: string;
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
  notes?: string | null;
}

export interface StartupUpdate {
  name?: string;
  site?: string | null;
  logo_url?: string | null;
  status?: StartupStatus;
  sector?: string;
  investment_date?: string;
  notes?: string | null;
}

export const STARTUP_STATUS_CONFIG: Record<
  StartupStatus,
  { label: string; color: string; icon: string }
> = {
  [StartupStatus.HEALTHY]: {
    label: 'Saudavel',
    color: 'var(--app-status-healthy)',
    icon: 'check_circle',
  },
  [StartupStatus.WARNING]: {
    label: 'Atencao',
    color: 'var(--app-status-warning)',
    icon: 'warning',
  },
  [StartupStatus.CRITICAL]: {
    label: 'Critico',
    color: 'var(--app-status-critical)',
    icon: 'error',
  },
};
