export interface MonthlyIndicator {
  id: string;
  startup_id: string;
  month: number;
  year: number;
  total_revenue: number | null;
  recurring_revenue_pct: number | null;
  gross_margin_pct: number | null;
  cash_balance: number | null;
  headcount: number | null;
  ebitda_burn: number | null;
  achievements: string | null;
  challenges: string | null;
  comments: string | null;
  created_at: string;
  updated_at: string;
}

export interface MonthlyIndicatorListResponse {
  items: MonthlyIndicator[];
  total: number;
}

export interface MonthlyIndicatorCreate {
  month: number;
  year: number;
  total_revenue?: number | null;
  recurring_revenue_pct?: number | null;
  gross_margin_pct?: number | null;
  cash_balance?: number | null;
  headcount?: number | null;
  ebitda_burn?: number | null;
  achievements?: string | null;
  challenges?: string | null;
  comments?: string | null;
}

export interface MonthlyIndicatorUpdate {
  month?: number;
  year?: number;
  total_revenue?: number | null;
  recurring_revenue_pct?: number | null;
  gross_margin_pct?: number | null;
  cash_balance?: number | null;
  headcount?: number | null;
  ebitda_burn?: number | null;
  achievements?: string | null;
  challenges?: string | null;
  comments?: string | null;
}

export const MONTH_LABELS: Record<number, string> = {
  1: 'Jan',
  2: 'Fev',
  3: 'Mar',
  4: 'Abr',
  5: 'Mai',
  6: 'Jun',
  7: 'Jul',
  8: 'Ago',
  9: 'Set',
  10: 'Out',
  11: 'Nov',
  12: 'Dez',
};
