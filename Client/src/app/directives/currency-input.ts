import { Directive, ElementRef, HostListener, forwardRef, inject } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

const FORMATTER = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/**
 * pt-BR currency mask.
 *
 * The field DISPLAYS `1.250.000,00` and the control stores `1250000` — formatting
 * is presentational, the form still submits a number.
 *
 * Treats typing as CENTS: each digit enters from the right and the last two are
 * the fraction. That spares the user from placing the cursor between separators,
 * which is where naive masks break.
 *
 * Requires `type="text"` with `inputmode="decimal"`: a `type="number"` does not
 * accept a thousands separator in the displayed value — and, as a bonus, avoids
 * the mouse wheel changing the number.
 */
@Directive({
  selector: 'input[appCurrencyInput]',
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => CurrencyInput),
      multi: true,
    },
  ],
})
export class CurrencyInput implements ControlValueAccessor {
  private readonly el = inject<ElementRef<HTMLInputElement>>(ElementRef);

  private onChange: (value: number | null) => void = () => undefined;
  private onTouched: () => void = () => undefined;

  writeValue(value: number | null): void {
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

  @HostListener('input')
  onInput(): void {
    const input = this.el.nativeElement;
    const negativo = input.value.trim().startsWith('-');
    const digitos = input.value.replace(/\D/g, '');

    if (!digitos) {
      // Keep the sign while there is no digit yet. Clearing everything here dropped
      // the "-" the moment it was typed, and the burn field — the only one that is
      // usually negative — could never become negative.
      input.value = negativo ? '-' : '';
      this.onChange(null);
      return;
    }

    const valor = (negativo ? -1 : 1) * (Number(digitos) / 100);
    input.value = FORMATTER.format(valor);
    // Move the cursor to the end: with cents-based input the new digit always
    // lands on the right, so that is where the cursor should go.
    input.setSelectionRange(input.value.length, input.value.length);
    this.onChange(valor);
  }

  @HostListener('blur')
  onBlur(): void {
    this.onTouched();
  }
}
