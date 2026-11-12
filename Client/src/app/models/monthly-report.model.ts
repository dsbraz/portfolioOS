export type DispatchKind = 'initial' | 'reminder';

/** One automatic e-mail of the reporting link, sent by the monthly job. */
export interface MonthlyReportDispatch {
  id: string;
  startup_id: string;
  executive_id: string | null;
  recipient_email: string;
  month: number;
  year: number;
  kind: DispatchKind;
  /** Why the relay refused it; `null` when it went out. */
  error: string | null;
  sent_at: string;
}

export interface MonthlyReportDispatchListResponse {
  items: MonthlyReportDispatch[];
  total: number;
}

/**
 * Days of the month the scheduled job runs (Cloud Scheduler, DEPLOY.md §8).
 * The schedule lives in the infrastructure; this mirrors it for the copy that
 * tells the operator when the e-mail goes out. Change both together.
 */
export const MONTHLY_REPORT_DAYS: Record<DispatchKind, number> = {
  initial: 10,
  reminder: 20,
};

export const DISPATCH_KIND_LABELS: Record<DispatchKind, string> = {
  initial: 'Envio',
  reminder: 'Lembrete',
};
