import { Startup } from './startup.model';

export interface StartupMonitoringItem {
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

export interface MonitoringSummary {
  total_startups: number;
  portfolio_revenue: number;
  portfolio_health: HealthDistribution;
  monthly_report_pct: number;
  routines_up_to_date_pct: number;
  startups: StartupMonitoringItem[];
}
