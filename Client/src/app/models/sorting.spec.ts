import { SortState, applySort, sortRows } from './sorting';

interface Linha {
  nome: string;
  receita: number | string | null;
}

const linha = (nome: string, receita: number | string | null): Linha => ({ nome, receita });

describe('sorting', () => {
  it('should sort numbers numerically, not as text', () => {
    const rows = [linha('a', 9), linha('b', 100), linha('c', 20)];
    expect(sortRows(rows, r => r.receita, 'asc').map(r => r.nome)).toEqual(['a', 'c', 'b']);
  });

  it('should invert on desc', () => {
    const rows = [linha('a', 9), linha('b', 100), linha('c', 20)];
    expect(sortRows(rows, r => r.receita, 'desc').map(r => r.nome)).toEqual(['b', 'c', 'a']);
  });

  // A API serializa Decimal como string JSON. Comparar como texto colocaria
  // "9" depois de "100".
  it('should coerce numeric strings coming from the API', () => {
    const rows = [linha('a', '9.00'), linha('b', '100.00'), linha('c', '20.00')];
    expect(sortRows(rows, r => r.receita, 'asc').map(r => r.nome)).toEqual(['a', 'c', 'b']);
  });

  // Se o vazio participasse da inversão, ordenar decrescente encheria o topo da
  // tela de "—" antes do primeiro dado.
  it('should keep absent values last in both directions', () => {
    const rows = [linha('a', null), linha('b', 100), linha('c', 20)];
    expect(sortRows(rows, r => r.receita, 'asc').map(r => r.nome)).toEqual(['c', 'b', 'a']);
    expect(sortRows(rows, r => r.receita, 'desc').map(r => r.nome)).toEqual(['b', 'c', 'a']);
  });

  it('should treat an empty string as absent', () => {
    const rows = [linha('a', ''), linha('b', 'zulu'), linha('c', 'alfa')];
    expect(sortRows(rows, r => r.receita, 'asc').map(r => r.nome)).toEqual(['c', 'b', 'a']);
  });

  // Zero é dado: tem que ordenar antes de 1, não ir para o fim com os ausentes.
  it('should sort zero as a value, not as absence', () => {
    const rows = [linha('a', null), linha('b', 1), linha('c', 0)];
    expect(sortRows(rows, r => r.receita, 'asc').map(r => r.nome)).toEqual(['c', 'b', 'a']);
  });

  it('should sort negative numbers below zero', () => {
    const rows = [linha('a', 0), linha('b', -138200), linha('c', 5)];
    expect(sortRows(rows, r => r.receita, 'asc').map(r => r.nome)).toEqual(['b', 'a', 'c']);
  });

  // Sem collator pt-BR, "Ávila" cairia depois de "Zago" porque "Á" tem code
  // point maior que "Z".
  it('should sort pt-BR text ignoring accents', () => {
    const rows = [linha('z', 'Zago'), linha('a', 'Ávila'), linha('g', 'Grão Verde')];
    expect(sortRows(rows, r => r.nome === 'z' ? 'Zago' : r.nome === 'a' ? 'Ávila' : 'Grão Verde', 'asc')
      .map(r => r.nome)).toEqual(['a', 'g', 'z']);
  });

  it('should order embedded numbers naturally', () => {
    const rows = [linha('a', 'Startup 10'), linha('b', 'Startup 9')];
    expect(sortRows(rows, r => r.receita, 'asc').map(r => r.nome)).toEqual(['b', 'a']);
  });

  it('should keep the original order when there is no direction', () => {
    const rows = [linha('a', 9), linha('b', 100)];
    expect(sortRows(rows, r => r.receita, '').map(r => r.nome)).toEqual(['a', 'b']);
  });

  // `Array.prototype.sort` ordena no lugar, e estas linhas vêm de signals:
  // ordenar o original reescreveria o estado sem que nada emitisse.
  it('should never mutate the input array', () => {
    const rows = [linha('a', 9), linha('b', 100), linha('c', 20)];
    const antes = rows.map(r => r.nome);

    sortRows(rows, r => r.receita, 'asc');
    sortRows(rows, r => r.receita, '');

    expect(rows.map(r => r.nome)).toEqual(antes);
  });

  describe('applySort', () => {
    const acessores = {
      nome: (r: Linha) => r.nome,
      receita: (r: Linha) => r.receita,
    };

    it('should use the accessor registered for the active column', () => {
      const rows = [linha('zulu', 1), linha('alfa', 2)];
      const sort: SortState = { active: 'nome', direction: 'asc' };
      expect(applySort(rows, sort, acessores).map(r => r.nome)).toEqual(['alfa', 'zulu']);
    });

    // A coluna de ações não tem acessor, e um clique nela não deve embaralhar
    // a tabela.
    it('should keep the original order for a column with no accessor', () => {
      const rows = [linha('zulu', 1), linha('alfa', 2)];
      const sort: SortState = { active: 'actions', direction: 'asc' };
      expect(applySort(rows, sort, acessores).map(r => r.nome)).toEqual(['zulu', 'alfa']);
    });
  });
});
