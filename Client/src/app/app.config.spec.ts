import { ApplicationRef, Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DEFAULT_OPTIONS, MatDialog, MatDialogModule } from '@angular/material/dialog';

import { dialogDefaults } from './app.config';

@Component({ template: '<p>conteúdo</p>' })
class DialogoDeTeste {}

describe('dialogDefaults', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MatDialogModule, DialogoDeTeste],
      providers: [
        provideNoopAnimations(),
        { provide: MAT_DIALOG_DEFAULT_OPTIONS, useValue: dialogDefaults },
      ],
    }).compileComponents();
  });

  // Regressão: `MAT_DIALOG_DEFAULT_OPTIONS` SUBSTITUI a configuração padrão do
  // Material. Sem declarar `role` aqui, o container saía com `aria-modal="true"`
  // e nenhum role — e `aria-modal` só tem significado sobre um `role="dialog"`.
  // Assistive tech deixava de anunciar o diálogo como diálogo.
  it('should open dialogs with both role and aria-modal', () => {
    const dialog = TestBed.inject(MatDialog);
    dialog.open(DialogoDeTeste);
    // Os atributos do container só chegam ao DOM depois da detecção de mudanças.
    TestBed.inject(ApplicationRef).tick();
    const container = document.querySelector('.mat-mdc-dialog-container');
    expect(container?.getAttribute('role')).toBe('dialog');
    expect(container?.getAttribute('aria-modal')).toBe('true');

    dialog.closeAll();
  });
});
