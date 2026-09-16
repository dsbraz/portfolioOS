import { SortState, applySort, sortRows } from './sorting';

interface Row {
  name: string;
  revenue: number | string | null;
}

const row = (name: string, revenue: number | string | null): Row => ({ name, revenue });

describe('sorting', () => {
  it('should sort numbers numerically, not as text', () => {
    const rows = [row('a', 9), row('b', 100), row('c', 20)];
    expect(sortRows(rows, r => r.revenue, 'asc').map(r => r.name)).toEqual(['a', 'c', 'b']);
  });

  it('should invert on desc', () => {
    const rows = [row('a', 9), row('b', 100), row('c', 20)];
    expect(sortRows(rows, r => r.revenue, 'desc').map(r => r.name)).toEqual(['b', 'c', 'a']);
  });

  // The API serializes Decimal as a JSON string. Comparing as text would put
  // "9" after "100".
  it('should coerce numeric strings coming from the API', () => {
    const rows = [row('a', '9.00'), row('b', '100.00'), row('c', '20.00')];
    expect(sortRows(rows, r => r.revenue, 'asc').map(r => r.name)).toEqual(['a', 'c', 'b']);
  });

  // If empty values took part in the inversion, sorting descending would fill
  // the top of the screen with "—" before the first data point.
  it('should keep absent values last in both directions', () => {
    const rows = [row('a', null), row('b', 100), row('c', 20)];
    expect(sortRows(rows, r => r.revenue, 'asc').map(r => r.name)).toEqual(['c', 'b', 'a']);
    expect(sortRows(rows, r => r.revenue, 'desc').map(r => r.name)).toEqual(['b', 'c', 'a']);
  });

  it('should treat an empty string as absent', () => {
    const rows = [row('a', ''), row('b', 'zulu'), row('c', 'alfa')];
    expect(sortRows(rows, r => r.revenue, 'asc').map(r => r.name)).toEqual(['c', 'b', 'a']);
  });

  // Zero is data: it must sort before 1, not go to the end with absent values.
  it('should sort zero as a value, not as absence', () => {
    const rows = [row('a', null), row('b', 1), row('c', 0)];
    expect(sortRows(rows, r => r.revenue, 'asc').map(r => r.name)).toEqual(['c', 'b', 'a']);
  });

  it('should sort negative numbers below zero', () => {
    const rows = [row('a', 0), row('b', -138200), row('c', 5)];
    expect(sortRows(rows, r => r.revenue, 'asc').map(r => r.name)).toEqual(['b', 'a', 'c']);
  });

  // Without a pt-BR collator, "Ávila" would land after "Zago" because "Á" has a
  // higher code point than "Z".
  it('should sort pt-BR text ignoring accents', () => {
    const rows = [row('z', 'Zago'), row('a', 'Ávila'), row('g', 'Grão Verde')];
    expect(sortRows(rows, r => r.name === 'z' ? 'Zago' : r.name === 'a' ? 'Ávila' : 'Grão Verde', 'asc')
      .map(r => r.name)).toEqual(['a', 'g', 'z']);
  });

  it('should order embedded numbers naturally', () => {
    const rows = [row('a', 'Startup 10'), row('b', 'Startup 9')];
    expect(sortRows(rows, r => r.revenue, 'asc').map(r => r.name)).toEqual(['b', 'a']);
  });

  it('should keep the original order when there is no direction', () => {
    const rows = [row('a', 9), row('b', 100)];
    expect(sortRows(rows, r => r.revenue, '').map(r => r.name)).toEqual(['a', 'b']);
  });

  // `Array.prototype.sort` sorts in place, and these rows come from signals:
  // sorting the original would rewrite state without anything emitting.
  it('should never mutate the input array', () => {
    const rows = [row('a', 9), row('b', 100), row('c', 20)];
    const before = rows.map(r => r.name);

    sortRows(rows, r => r.revenue, 'asc');
    sortRows(rows, r => r.revenue, '');

    expect(rows.map(r => r.name)).toEqual(before);
  });

  describe('applySort', () => {
    const accessors = {
      name: (r: Row) => r.name,
      revenue: (r: Row) => r.revenue,
    };

    it('should use the accessor registered for the active column', () => {
      const rows = [row('zulu', 1), row('alfa', 2)];
      const sort: SortState = { active: 'name', direction: 'asc' };
      expect(applySort(rows, sort, accessors).map(r => r.name)).toEqual(['alfa', 'zulu']);
    });

    // The actions column has no accessor, and clicking it must not shuffle the
    // table.
    it('should keep the original order for a column with no accessor', () => {
      const rows = [row('zulu', 1), row('alfa', 2)];
      const sort: SortState = { active: 'actions', direction: 'asc' };
      expect(applySort(rows, sort, accessors).map(r => r.name)).toEqual(['zulu', 'alfa']);
    });
  });
});
