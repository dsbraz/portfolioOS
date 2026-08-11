import { Directive, ElementRef, HostListener, forwardRef, inject } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

const FORMATTER = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/**
 * Máscara de moeda em pt-BR.
 *
 * O campo EXIBE `1.250.000,00` e o controle guarda `1250000` — a formatação é
 * de apresentação, o formulário continua enviando número.
 *
 * Trata a digitação como CENTAVOS: cada dígito entra pela direita e os dois
 * últimos são a fração. É o que dispensa o usuário de posicionar o cursor entre
 * separadores, que é onde máscaras ingênuas quebram.
 *
 * Exige `type="text"` com `inputmode="decimal"`: um `type="number"` não aceita
 * separador de milhar no valor exibido — e, de quebra, deixa de ter o problema
 * da roda do mouse alterando o número.
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
      // Preserva o sinal quando ainda não há dígito. Limpar tudo aqui descartava
      // o "-" no instante em que ele era digitado, e o campo de burn — o único
      // que costuma ser negativo — nunca conseguia ficar negativo.
      input.value = negativo ? '-' : '';
      this.onChange(null);
      return;
    }

    const valor = (negativo ? -1 : 1) * (Number(digitos) / 100);
    input.value = FORMATTER.format(valor);
    // O cursor vai para o fim: com entrada por centavos o dígito novo sempre
    // aterrissa à direita, então é para lá que o cursor deve seguir.
    input.setSelectionRange(input.value.length, input.value.length);
    this.onChange(valor);
  }

  @HostListener('blur')
  onBlur(): void {
    this.onTouched();
  }
}
