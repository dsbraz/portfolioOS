import { Component, input } from '@angular/core';

export type ReadItemKind = 'text' | 'num' | 'long';

export interface ReadItem {
  label: string;
  value: string | null;
  /** `num` alinha em mono tabular; `long` ocupa a linha inteira. */
  kind?: ReadItemKind;
}

export interface ReadSection {
  /** Sem título, a seção rende só os pares — é o caso de registros sem grupos. */
  title?: string;
  items: ReadItem[];
}

/**
 * Vista de LEITURA de um registro.
 *
 * Substitui o formulário desabilitado que servia de modo somente-leitura. Ali o
 * dado herdava a cor de controle inativo — `#121212` a 38%, medido em 2,46:1 no
 * tema claro — enquanto o rótulo ao lado ficava em 18,7:1. A WCAG 1.4.3 isenta
 * componentes inativos de contraste, então nenhum verificador automático
 * reclamava; só que aqui o texto do controle ERA a informação, e a isenção
 * acabava desculpando um dado ilegível.
 *
 * Uma lista de definição descreve o que a coisa é: pares rótulo/valor em tinta
 * cheia, sem caixas que fingem ser editáveis. As seções acompanham as do modo de
 * edição, para que ler e editar apresentem o registro na mesma ordem e com os
 * mesmos agrupamentos.
 */
@Component({
  selector: 'app-read-view',
  templateUrl: './read-view.html',
  styleUrl: './read-view.scss',
})
export class ReadView {
  readonly sections = input.required<ReadSection[]>();
}
