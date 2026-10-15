import { Directive, ElementRef, HostListener, forwardRef, inject } from '@angular/core';
import { ControlValueAccessor, NG_VALIDATORS, NG_VALUE_ACCESSOR, ValidationErrors, Validator } from '@angular/forms';

const FORMATTER = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/**
 * Brazilian currency input: ungrouped digits represent reais, commas separate
 * cents, and periods group thousands. Keep the text and caret while editing;
 * format only on blur. The form always receives a number or null.
 * Requires type="text" and inputmode="decimal".
 */
@Directive({
  selector: 'input[appCurrencyInput]',
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => CurrencyInput),
      multi: true,
    },
    {
      provide: NG_VALIDATORS,
      useExisting: forwardRef(() => CurrencyInput),
      multi: true,
    },
  ],
})
export class CurrencyInput implements ControlValueAccessor, Validator {
  private readonly el = inject<ElementRef<HTMLInputElement>>(ElementRef);

  private invalidFormat = false;
  private value: number | null = null;

  private onChange: (value: number | null) => void = () => undefined;
  private onTouched: () => void = () => undefined;

  writeValue(value: number | null): void {
    this.invalidFormat = false;
    this.value = value;
    this.el.nativeElement.value = value == null ? '' : FORMATTER.format(value);
  }

  registerOnChange(fn: (value: number | null) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.el.nativeElement.disabled = isDisabled;
  }

  validate(): ValidationErrors | null {
    return this.invalidFormat ? { currencyFormat: true } : null;
  }

  @HostListener('input')
  onInput(): void {
    const raw = this.el.nativeElement.value.trim();
    const text = raw.replace(/^R\$\s*/, '');
    const valid = /^-?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{0,2})?$/.test(text);
    const value = valid ? Number(text.replace(/\./g, '').replace(',', '.')) : null;
    this.invalidFormat = raw !== '' && (!valid || !Number.isFinite(value));
    this.value = this.invalidFormat ? null : value;
    // Set validation state before notifying Angular: optional fields must not
    // turn malformed text into a valid null or retain a previous valid number.
    this.onChange(this.value);
  }

  @HostListener('blur')
  onBlur(): void {
    if (!this.invalidFormat) {
      this.el.nativeElement.value = this.value == null ? '' : FORMATTER.format(this.value);
    }
    this.onTouched();
  }
}
