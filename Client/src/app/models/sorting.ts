/**
 * Ordenação de tabelas.
 *
 * Vive aqui, e não em cada página, porque as regras difíceis são as mesmas em
 * todas as tabelas: número que chega como string, ausência que não pode ser
 * tratada como zero, e texto em pt-BR com acento.
 *
 * Não depende do Angular Material de propósito — o `Sort` do Material é
 * estruturalmente compatível com `SortState`, então dá para passar o evento
 * direto, mas a comparação continua testável sem framework.
 */

export type SortDirection = 'asc' | 'desc' | '';

export interface SortState {
  active: string;
  direction: SortDirection;
}

/** Valor comparável de uma linha para uma coluna. */
export type SortAccessor<T> = (row: T) => string | number | null | undefined;

const COLLATOR = new Intl.Collator('pt-BR', {
  // `numeric` faz "Startup 10" vir depois de "Startup 9"; `sensitivity: base`
  // ignora acento e caixa, senão "Ávila" cairia depois de "Zago".
  numeric: true,
  sensitivity: 'base',
});

/**
 * A API serializa `Decimal` como string JSON — `"767776.43"`, não `767776.43`.
 * Comparar isso como texto ordenaria "9" depois de "10".
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

  // Cópia antes de ordenar: `sort` muda o array no lugar, e estes vêm de
  // signals — ordenar o original reescreveria o estado sem avisar ninguém.
  return [...rows].sort((rowA, rowB) => {
    const a = accessor(rowA);
    const b = accessor(rowB);

    // Ausência vai para o fim NOS DOIS SENTIDOS. Deixar o nulo participar da
    // inversão o traria para o topo no descendente, e uma tela cheia de "—"
    // antes do primeiro dado não é o que ninguém quer ver ao ordenar.
    const vazioA = a === null || a === undefined || a === '';
    const vazioB = b === null || b === undefined || b === '';
    if (vazioA && vazioB) return 0;
    if (vazioA) return 1;
    if (vazioB) return -1;

    const numA = typeof a === 'boolean' ? null : asNumber(a);
    const numB = typeof b === 'boolean' ? null : asNumber(b);
    if (numA !== null && numB !== null) return (numA - numB) * factor;

    return COLLATOR.compare(String(a), String(b)) * factor;
  });
}

/**
 * Aplica o estado de ordenação usando o acessor registrado para a coluna ativa.
 * Coluna sem acessor mantém a ordem original — é o caso da coluna de ações.
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
