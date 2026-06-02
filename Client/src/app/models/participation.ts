export const REVENUE_MULTIPLE = 5;
export const MONTHS_IN_YEAR = 12;

/**
 * Participation valuation: annualized revenue x revenue multiple x equity stake.
 *
 * The accumulated year-to-date revenue is averaged over the elapsed months,
 * annualized (x12), multiplied by the revenue multiple (x5), and finally scaled
 * by the equity stake percentage.
 *
 * Returns null when there is no accumulated revenue or no equity stake.
 */
export function participationValue(
  accumulatedRevenue: number | null,
  monthsElapsed: number,
  equityStakePct: number | null,
): number | null {
  if (accumulatedRevenue == null || equityStakePct == null || monthsElapsed <= 0) {
    return null;
  }
  // The API serializes Decimal fields as JSON strings; coerce defensively.
  const revenue = Number(accumulatedRevenue);
  const equity = Number(equityStakePct);
  if (Number.isNaN(revenue) || Number.isNaN(equity)) {
    return null;
  }
  const annualizedRevenue = (revenue / monthsElapsed) * MONTHS_IN_YEAR;
  return annualizedRevenue * REVENUE_MULTIPLE * (equity / 100);
}
