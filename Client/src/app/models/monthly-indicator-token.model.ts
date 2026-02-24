export interface MonthlyIndicatorToken {
  id: string;
  token: string;
  startup_id: string;
  month: number;
  year: number;
  created_at: string;
}

export interface MonthlyIndicatorTokenListResponse {
  items: MonthlyIndicatorToken[];
  total: number;
}

export interface PublicIndicatorForm {
  startup_name: string;
  startup_logo_url: string | null;
  month: number;
  year: number;
  existing_indicator: PublicIndicatorData | null;
}

export interface PublicIndicatorData {
  total_revenue: number | null;
  cash_balance: number | null;
  ebitda_burn: number | null;
  recurring_revenue_pct: number | null;
  gross_margin_pct: number | null;
  headcount: number | null;
  achievements: string | null;
  challenges: string | null;
}

export interface PublicIndicatorSubmit {
  total_revenue: number | null;
  cash_balance: number | null;
  ebitda_burn: number | null;
  recurring_revenue_pct: number | null;
  gross_margin_pct: number | null;
  headcount: number | null;
  achievements: string | null;
  challenges: string | null;
}
