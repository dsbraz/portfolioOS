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
  /** Why the relay refused it; the job retries it on its next run. */
  error: string | null;
  /** When the job claimed it and tried to send. */
  attempted_at: string;
  /** When the relay accepted it. */
  sent_at: string | null;
}

/**
 * Delivered (`sent_at`), failed (`error`), or unconfirmed: the job tried but
 * could not record the outcome, so the e-mail may or may not have left and the
 * job will not resend it on its own.
 */
export type DispatchStatus = 'delivered' | 'failed' | 'unconfirmed';

export function dispatchStatus(dispatch: MonthlyReportDispatch): DispatchStatus {
  if (dispatch.sent_at != null) return 'delivered';
  if (dispatch.error != null) return 'failed';
  return 'unconfirmed';
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
