import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { By } from '@angular/platform-browser';

import { CurrencyInput } from './currency-input';

@Component({
  imports: [ReactiveFormsModule, CurrencyInput],
  template: `<input appCurrencyInput type="text" inputmode="decimal" [formControl]="control" />`,
})
class TestHost {
  readonly control = new FormControl<number | null>(null);
}

describe('CurrencyInput', () => {
  let fixture: ComponentFixture<TestHost>;
  let host: TestHost;
  let input: HTMLInputElement;

  const typeText = (text: string) => {
    input.value = text;
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [TestHost] }).compileComponents();
    fixture = TestBed.createComponent(TestHost);
    host = fixture.componentInstance;
    fixture.detectChanges();
    input = fixture.debugElement.query(By.directive(CurrencyInput)).nativeElement;
  });

  it.each(['64000', '64.000', '64.000,00'])('should interpret %s as reais', (text) => {
    typeText(text);
    expect(host.control.value).toBe(64000);
    expect(input.value).toBe(text);
    input.dispatchEvent(new Event('blur'));
    expect(input.value).toBe('64.000,00');
    expect(host.control.touched).toBe(true);
  });

  it.each([
    ['64.000,50', 64000.5], ['64', 64], ['6,4', 6.4], ['64,', 64],
    ['-64000', -64000], ['0', 0], ['0,01', 0.01],
    [' R$\u00a064.000,50 ', 64000.5], ['R$ -64.000,50', -64000.5],
  ])('should parse %s without changing its magnitude', (text, value) => {
    typeText(text as string);
    expect(host.control.value).toBe(value);
    expect(host.control.valid).toBe(true);
  });

  it.each(['64,000.50', '64000.50', '64,000', '6.40', '1.23.456', '64mil',
    '64-', '--64', '-', 'R$', '64,001', '1e3', 'Infinity', '64 000'])
  ('should preserve and reject invalid text %s', (text) => {
    typeText('100');
    typeText(text);
    input.dispatchEvent(new Event('blur'));
    expect(input.value).toBe(text);
    expect(host.control.value).toBeNull();
    expect(host.control.hasError('currencyFormat')).toBe(true);
  });

  it('should support incremental typing and recovery from incomplete grouping', () => {
    for (const text of ['6', '64', '640', '6400', '64000']) {
      typeText(text);
      expect(host.control.value).toBe(Number(text));
    }
    typeText('64.');
    expect(host.control.invalid).toBe(true);
    typeText('64.000');
    expect(host.control.value).toBe(64000);
    expect(host.control.valid).toBe(true);
    typeText('-');
    expect(input.value).toBe('-');
    typeText('-64');
    expect(host.control.value).toBe(-64);
  });

  it('should preserve the caret when editing inside a value', () => {
    host.control.setValue(64000);
    input.value = '65.000,00';
    input.setSelectionRange(2, 2);
    input.dispatchEvent(new Event('input'));
    expect(input.selectionStart).toBe(2);
    expect(host.control.value).toBe(65000);
  });

  it('should allow selection replacement and deletion', () => {
    host.control.setValue(64000);
    input.select();
    typeText('25,5');
    expect(host.control.value).toBe(25.5);
    typeText('25,');
    expect(host.control.value).toBe(25);
    typeText('');
    expect(host.control.value).toBeNull();
    expect(host.control.valid).toBe(true);
  });

  it('should clear invalid state on reset or programmatic update', () => {
    typeText('bad');
    host.control.setValue(980000);
    expect(input.value).toBe('980.000,00');
    expect(host.control.valid).toBe(true);
    typeText('bad');
    host.control.reset();
    expect(input.value).toBe('');
    expect(host.control.valid).toBe(true);
  });

  it('should propagate disabled state', () => {
    host.control.disable();
    expect(input.disabled).toBe(true);
    host.control.enable();
    expect(input.disabled).toBe(false);
  });
});
