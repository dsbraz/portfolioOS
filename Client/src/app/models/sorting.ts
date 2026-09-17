/**
 * Table sorting.
 *
 * Lives here, not in each page, because the hard rules are the same for every
 * table: numbers that arrive as strings, missing values that must not be
 * treated as zero, and accented pt-BR text.
 *
 * Deliberately independent of Angular Material — Material's `Sort` is
 * structurally compatible with `SortState`, so the event can be passed
 * directly, while the comparison stays testable without a framework.
 */

export type SortDirection = 'asc' | 'desc' | '';

export interface SortState {
  active: string;
  direction: SortDirection;
}

/** Comparable value of a row for a column. */
export type SortAccessor<T> = (row: T) => string | number | null | undefined;

const COLLATOR = new Intl.Collator('pt-BR', {
  // `numeric` puts "Startup 10" after "Startup 9"; `sensitivity: base`
  // ignores accents and case, otherwise "Ávila" would land after "Zago".
  numeric: true,
  sensitivity: 'base',
});

/**
 * The API serializes `Decimal` as a JSON string — `"767776.43"`, not `767776.43`.
 * Comparing that as text would sort "9" after "10".
 */
function asNumber(value: string | number): number | null {
  const parsed = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function sortRows<T>(
  rows: readonly T[],
  accessor: SortAccessor<T>,
  direction: SortDirection,
): T[] {
  if (!direction) return [...rows];

  const factor = direction === 'asc' ? 1 : -1;

  // Copy before sorting: `sort` mutates the array in place, and these come from
  // signals — sorting the original would rewrite state without notifying anyone.
  return [...rows].sort((rowA, rowB) => {
    const a = accessor(rowA);
    const b = accessor(rowB);

    // Missing values go last IN BOTH DIRECTIONS. Letting null take part in the
    // inversion would bring it to the top when descending, and a screen full of "—"
    // before the first data point is not what anyone wants to see when sorting.
    const emptyA = a === null || a === undefined || a === '';
    const emptyB = b === null || b === undefined || b === '';
    if (emptyA && emptyB) return 0;
    if (emptyA) return 1;
    if (emptyB) return -1;

    const numA = asNumber(a);
    const numB = asNumber(b);
    if (numA !== null && numB !== null) return (numA - numB) * factor;

    return COLLATOR.compare(String(a), String(b)) * factor;
  });
}

/**
 * Applies the sort state using the accessor registered for the active column.
 * A column without an accessor keeps the original order — e.g. the actions column.
 */
export function applySort<T>(
  rows: readonly T[],
  sort: SortState,
  accessors: Record<string, SortAccessor<T>>,
): T[] {
  const accessor = sort.active ? accessors[sort.active] : undefined;
  if (!accessor) return [...rows];
  return sortRows(rows, accessor, sort.direction);
}
