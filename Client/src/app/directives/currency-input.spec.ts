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

  it('should format what the user types as pt-BR currency', () => {
    typeText('125000000');
    expect(input.value).toBe('1.250.000,00');
  });

  // The point of the component: the mask is for PRESENTATION only. If the control
  // held the formatted string, the form would send "1.250.000,00" to the API.
  it('should keep the control value numeric', () => {
    typeText('125000000');
    expect(host.control.value).toBe(1250000);
  });

  it('should treat the last two digits as cents', () => {
    typeText('1234');
    expect(input.value).toBe('12,34');
    expect(host.control.value).toBe(12.34);
  });

  it('should support negative values for burn', () => {
    typeText('-13820000');
    expect(host.control.value).toBe(-138200);
  });

  // Regression: the "-" arrives on its own, before any digit. Clearing the field
  // at that moment dropped the sign, and burn never became negative.
  it('should keep the minus sign typed before any digit', () => {
    typeText('-');
    expect(input.value).toBe('-');

    typeText('-13820000');
    expect(input.value).toBe('-138.200,00');
    expect(host.control.value).toBe(-138200);
  });

  // Regression: the sign only counted when the text STARTED with "-". The cursor
  // is moved to the end after every keystroke, so a "-" typed after the number
  // landed at the end and was silently dropped — the burn was saved positive.
  it('should make a typed number negative when "-" is typed after it', () => {
    typeText('1234');
    typeText('12,34-');
    expect(input.value).toBe('-12,34');
    expect(host.control.value).toBe(-12.34);
  });

  it('should toggle back to positive when "-" is typed again', () => {
    typeText('-1234');
    typeText('-12,34-');
    expect(input.value).toBe('12,34');
    expect(host.control.value).toBe(12.34);
  });

  it('should clear to null when emptied', () => {
    typeText('1234');
    typeText('');
    expect(input.value).toBe('');
    expect(host.control.value).toBeNull();
  });

  it('should format a value written by the form', () => {
    host.control.setValue(980000);
    fixture.detectChanges();
    expect(input.value).toBe('980.000,00');
  });
});
