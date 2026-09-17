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

  // The point of the component. Read mode used to be a disabled form, and the
  // value inherited the inactive-control color (2.46:1). Here the value is
  // plain text, so it inherits `--color-text` like any other content on screen.
  it('should render values as plain text, not as form controls', async () => {
    const el = await render([{ label: 'Receita do mês', value: 'R$ 767.776,43', kind: 'num' }]);
    expect(el.querySelector('input')).toBeNull();
    expect(el.querySelector('textarea')).toBeNull();
    expect(el.querySelector('.mat-mdc-form-field')).toBeNull();
  });

  // A bare dash says nothing to someone listening to the screen.
  it('should announce an absent value instead of showing a bare dash', async () => {
    const el = await render([{ label: 'Comentários', value: null }]);
    const dd = el.querySelector('dd');
    expect(dd?.querySelector('[aria-hidden="true"]')?.textContent).toBe('—');
    expect(dd?.querySelector('.visually-hidden')?.textContent?.trim()).toBe('Não informado');
  });

  // Regression: an empty string is a provided value; only `null` means absence.
  // A truthiness check here would hide a note that was cleared on purpose.
  it('should treat an empty string as a value, not as absence', async () => {
    const el = await render([{ label: 'Resumo', value: '' }]);
    expect(el.querySelector('.read-value--empty')).toBeNull();
  });

  it('should give long text the full row', async () => {
    const el = await render([{ label: 'Resumo', value: 'texto', kind: 'long' }]);
    expect(el.querySelector('.read-item--long')).toBeTruthy();
  });

  // Each section is its own list, not a single list with titles in between: a
  // `dt` belonging to another group inside the same `dl` breaks the grouping
  // for anyone navigating by structure.
  it('should give each titled section its own heading and list', async () => {
    const el = await renderSections([
      { title: 'Quantitativos', items: [{ label: 'Headcount', value: '19' }] },
      { title: 'Qualitativos', items: [{ label: 'Comentários', value: 'ok' }] },
    ]);

    const titles = [...el.querySelectorAll('h3')].map(h => h.textContent?.trim());
    expect(titles).toEqual(['Quantitativos', 'Qualitativos']);
    expect(el.querySelectorAll('dl').length).toBe(2);
  });

  it('should render a section without a title as just its pairs', async () => {
    const el = await renderSections([{ items: [{ label: 'Data', value: '01/07/2026' }] }]);
    expect(el.querySelector('h3')).toBeNull();
    expect(el.querySelectorAll('dl').length).toBe(1);
  });
});
