import { MONTHS_IN_YEAR, REVENUE_MULTIPLE, participationValue } from './participation';

describe('participationValue', () => {
  it('annualizes accumulated revenue and applies multiple and equity stake', () => {
    // 600000 over 6 months => 100000/month => 1200000/year => x5 => 6000000 => 5% => 300000
    const result = participationValue(600000, 6, 5);
    expect(result).toBe((600000 / 6) * MONTHS_IN_YEAR * REVENUE_MULTIPLE * (5 / 100));
    expect(result).toBe(300000);
  });

  it('divides by the reference month number even with missing months', () => {
    // Only 400000 accumulated but reference month is 6 => divide by 6 (not by count of months)
    const result = participationValue(400000, 6, 10);
    expect(result).toBe((400000 / 6) * MONTHS_IN_YEAR * REVENUE_MULTIPLE * (10 / 100));
  });

  it('returns null when equity stake is null', () => {
    expect(participationValue(600000, 6, null)).toBeNull();
  });

  it('returns null when accumulated revenue is null', () => {
    expect(participationValue(null, 6, 5)).toBeNull();
  });

  it('returns null when monthsElapsed is zero or negative', () => {
    expect(participationValue(600000, 0, 5)).toBeNull();
    expect(participationValue(600000, -1, 5)).toBeNull();
  });

  it('returns zero when accumulated revenue is zero', () => {
    expect(participationValue(0, 6, 5)).toBe(0);
  });

  it('returns zero when equity stake is zero (not null)', () => {
    expect(participationValue(600000, 6, 0)).toBe(0);
  });

  it('coerces Decimal-as-string inputs from the API', () => {
    // The backend serializes Decimal fields as JSON strings.
    expect(participationValue('600000.00' as any, 6, '5.00' as any)).toBe(300000);
  });

  it('returns null when a string input is not numeric', () => {
    expect(participationValue('abc' as any, 6, 5)).toBeNull();
  });
});
