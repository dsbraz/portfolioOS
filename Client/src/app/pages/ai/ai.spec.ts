import { TestBed } from '@angular/core/testing';

import { routes } from '../../app.routes';
import { authGuard } from '../../guards/auth.guard';
import { Ai } from './ai';

describe('Ai', () => {
  async function render(): Promise<HTMLElement> {
    await TestBed.configureTestingModule({ imports: [Ai] }).compileComponents();
    const fixture = TestBed.createComponent(Ai);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  it('should present one portfolioOS package and one download link to the static zip', async () => {
    const element = await render();
    const packageCard = element.querySelector<HTMLElement>('.package-card');
    const downloads = element.querySelectorAll<HTMLAnchorElement>('.package-download');

    expect(element.querySelector('h1')?.textContent?.trim()).toBe('IA no portfolioOS');
    expect(packageCard?.querySelector('h2')?.textContent).toContain('Pacote de skills portfolioOS');
    expect(packageCard?.textContent).toContain('Instale uma vez');
    expect(packageCard?.textContent).toContain('descobre automaticamente');
    expect(downloads).toHaveLength(1);
    expect(downloads[0].getAttribute('href')).toBe('/api/static/portfolioos.zip');
    expect(downloads[0].getAttribute('download')).toBe('portfolioos.zip');
    expect(downloads[0].getAttribute('aria-label')).toBe('Baixar pacote de skills portfolioOS');
  });

  it('should keep equivalent Claude and ChatGPT installation instructions visible', async () => {
    const element = await render();
    const instructions = Array.from(element.querySelectorAll<HTMLElement>('.tool-instruction'));

    expect(instructions).toHaveLength(2);
    expect(instructions[0].querySelector('h3')?.textContent).toContain('Claude');
    expect(instructions[1].querySelector('h3')?.textContent).toContain('ChatGPT');
    for (const instruction of instructions) {
      expect(instruction.hasAttribute('hidden')).toBe(false);
      expect(instruction.closest('details')).toBeNull();
      expect(instruction.textContent).toContain('portfolioos.zip');
      expect(instruction.textContent).toContain('upload');
      expect(instruction.textContent).toContain('plano');
    }
  });

  it('should offer no per-skill action: the download is the only control', async () => {
    const element = await render();

    expect(element.querySelector('[role="tab"], input[type="radio"]')).toBeNull();
    expect(element.querySelector('.copy-button, [data-prompt-skill]')).toBeNull();
    expect(element.querySelectorAll('a, button')).toHaveLength(1);
  });

  it('should list what the package contains and what stays out of it', async () => {
    const element = await render();
    const included = Array.from(element.querySelectorAll<HTMLElement>('[data-included-skill]'));
    const agenda = element.querySelector<HTMLElement>('[data-included-skill="preparar-agenda"]');
    const meeting = element.querySelector<HTMLElement>('[data-included-skill="granola-reuniao"]');
    const blocked = element.querySelector<HTMLElement>(
      '[data-blocked-skill="auditoria-qualitativa"]',
    );

    expect(included.map((item) => item.dataset['includedSkill'])).toEqual([
      'operar-portfolioos',
      'preparar-agenda',
      'granola-reuniao',
      'cobrar-indicadores',
      'apresentacao-portfolio',
    ]);
    expect(agenda?.textContent).toContain('Somente leitura');
    expect(meeting?.textContent).toContain('Escrita com confirmação');
    expect(
      element.querySelector('[data-included-skill="apresentacao-portfolio"]')?.textContent,
    ).toContain('Somente leitura');
    expect(element.querySelector('[data-included-skill="auditoria-qualitativa"]')).toBeNull();
    expect(blocked?.textContent).toContain('Auditar o portfólio');
    expect(blocked?.textContent).toContain('Motivo:');
  });

  it('should show natural request examples without presenting them as skill prompts', async () => {
    const element = await render();
    const examples = element.querySelector<HTMLElement>('.request-examples');

    expect(examples?.querySelectorAll('q')).toHaveLength(4);
    expect(examples?.textContent).toContain('Prepare a agenda para minha reunião');
    expect(examples?.textContent).toContain('Registre minha conversa do Granola');
    expect(examples?.textContent).toContain('ainda não reportaram');
    expect(examples?.textContent).toContain('Mova o deal');
  });

  it('should keep concise safety, help and the guidance review date near setup', async () => {
    const element = await render();
    const packageCard = element.querySelector<HTMLElement>('.package-card');
    const help = element.querySelector<HTMLDetailsElement>('.support-details');

    expect(packageCard?.textContent).toContain('Nunca digite sua senha no chat');
    expect(packageCard?.textContent).toContain('link de indicador permite escrever no período');
    expect(packageCard?.textContent).toContain('Revise a prévia antes de permitir uma gravação');
    expect(element.querySelector('time[datetime="2026-09-17"]')).toBeTruthy();
    expect(help?.textContent).toContain('instalação para toda a organização');
    expect(help?.textContent).toContain('Cowork');
  });
});

describe('AI route', () => {
  it('should protect /ia with the authentication guard', () => {
    const route = routes.find((candidate) => candidate.path === 'ia');

    expect(route).toBeTruthy();
    expect(route?.canActivate).toContain(authGuard);
    expect(route?.data?.['public']).not.toBe(true);
  });
});
