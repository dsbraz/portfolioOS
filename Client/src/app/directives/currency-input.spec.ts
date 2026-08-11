import { Component, signal } from '@angular/core';
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

  const digitar = (texto: string) => {
    input.value = texto;
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

  it('should format what the user types as pt-BR currency', () => {
    digitar('125000000');
    expect(input.value).toBe('1.250.000,00');
  });

  // O ponto do componente: a máscara é de APRESENTAÇÃO. Se o controle guardasse
  // a string formatada, o formulário enviaria "1.250.000,00" para a API.
  it('should keep the control value numeric', () => {
    digitar('125000000');
    expect(host.control.value).toBe(1250000);
  });

  it('should treat the last two digits as cents', () => {
    digitar('1234');
    expect(input.value).toBe('12,34');
    expect(host.control.value).toBe(12.34);
  });

  it('should support negative values for burn', () => {
    digitar('-13820000');
    expect(host.control.value).toBe(-138200);
  });

  // Regressão: o "-" chega sozinho, antes de qualquer dígito. Limpar o campo
  // nesse instante descartava o sinal, e o burn nunca ficava negativo.
  it('should keep the minus sign typed before any digit', () => {
    digitar('-');
    expect(input.value).toBe('-');

    digitar('-13820000');
    expect(input.value).toBe('-138.200,00');
    expect(host.control.value).toBe(-138200);
  });

  it('should clear to null when emptied', () => {
    digitar('1234');
    digitar('');
    expect(input.value).toBe('');
    expect(host.control.value).toBeNull();
  });

  it('should format a value written by the form', () => {
    host.control.setValue(980000);
    fixture.detectChanges();
    expect(input.value).toBe('980.000,00');
  });
});
