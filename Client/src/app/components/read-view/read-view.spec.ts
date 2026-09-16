import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ReadItem, ReadSection, ReadView } from './read-view';

describe('ReadView', () => {
  let fixture: ComponentFixture<ReadView>;

  const renderSections = async (sections: ReadSection[]) => {
    fixture.componentRef.setInput('sections', sections);
    fixture.detectChanges();
    await fixture.whenStable();
    return fixture.nativeElement as HTMLElement;
  };

  const render = (items: ReadItem[]) => renderSections([{ items }]);

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [ReadView] }).compileComponents();
    fixture = TestBed.createComponent(ReadView);
  });

  it('should pair each label with its value in a definition list', async () => {
    const el = await render([{ label: 'Headcount', value: '19' }]);
    expect(el.querySelector('dl')).toBeTruthy();
    expect(el.querySelector('dt')?.textContent?.trim()).toBe('Headcount');
    expect(el.querySelector('dd')?.textContent?.trim()).toBe('19');
  });

  // O ponto do componente. O modo leitura era um formulário desabilitado, e o
  // valor herdava a cor de controle inativo (2,46:1). Aqui o valor é texto
  // comum, então herda `--color-text` como qualquer conteúdo da tela.
  it('should render values as plain text, not as form controls', async () => {
    const el = await render([{ label: 'Receita do mês', value: 'R$ 767.776,43', kind: 'num' }]);
    expect(el.querySelector('input')).toBeNull();
    expect(el.querySelector('textarea')).toBeNull();
    expect(el.querySelector('.mat-mdc-form-field')).toBeNull();
  });

  // O traço sozinho não diz nada para quem ouve a tela.
  it('should announce an absent value instead of showing a bare dash', async () => {
    const el = await render([{ label: 'Comentários', value: null }]);
    const dd = el.querySelector('dd');
    expect(dd?.querySelector('[aria-hidden="true"]')?.textContent).toBe('—');
    expect(dd?.querySelector('.visually-hidden')?.textContent?.trim()).toBe('Não informado');
  });

  // Regressão: string vazia é um valor informado; só `null` é ausência. Um teste
  // de veracidade aqui esconderia uma anotação apagada de propósito.
  it('should treat an empty string as a value, not as absence', async () => {
    const el = await render([{ label: 'Resumo', value: '' }]);
    expect(el.querySelector('.read-value--empty')).toBeNull();
  });

  it('should give long text the full row', async () => {
    const el = await render([{ label: 'Resumo', value: 'texto', kind: 'long' }]);
    expect(el.querySelector('.read-item--long')).toBeTruthy();
  });

  // Cada seção é uma lista própria, não uma lista só com títulos no meio: um
  // `dt` que pertence a outro grupo dentro do mesmo `dl` desfaz o agrupamento
  // para quem navega por estrutura.
  it('should give each titled section its own heading and list', async () => {
    const el = await renderSections([
      { title: 'Quantitativos', items: [{ label: 'Headcount', value: '19' }] },
      { title: 'Qualitativos', items: [{ label: 'Comentários', value: 'ok' }] },
    ]);

    const titulos = [...el.querySelectorAll('h3')].map(h => h.textContent?.trim());
    expect(titulos).toEqual(['Quantitativos', 'Qualitativos']);
    expect(el.querySelectorAll('dl').length).toBe(2);
  });

  it('should render a section without a title as just its pairs', async () => {
    const el = await renderSections([{ items: [{ label: 'Data', value: '01/07/2026' }] }]);
    expect(el.querySelector('h3')).toBeNull();
    expect(el.querySelectorAll('dl').length).toBe(1);
  });
});
