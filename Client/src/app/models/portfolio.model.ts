import { Startup } from './startup.model';

export interface StartupSummary {
  startup: Startup;
  total_revenue: number | null;
  cash_balance: number | null;
  ebitda_burn: number | null;
  headcount: number | null;
}

export interface HealthDistribution {
  healthy: number;
  warning: number;
  critical: number;
}

export type RevenueVariationDirection = 'up' | 'down' | 'neutral';

export interface PortfolioSummary {
  total_startups: number;
  revenue: number;
  revenue_variation_pct: number | null;
  revenue_variation_direction: RevenueVariationDirection;
  health: HealthDistribution;
  monthly_report_pct: number;
  routines_up_to_date_pct: number;
  startups: StartupSummary[];
}
