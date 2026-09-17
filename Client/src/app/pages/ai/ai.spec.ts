import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { routes } from '../../app.routes';
import { authGuard } from '../../guards/auth.guard';
import { SkillPackManifest } from '../../models/skill-pack.model';
import { Ai } from './ai';

const MANIFEST_URL = '/api/static/portfolioos-manifest.json';

const skill = (name: string, writes: boolean) => ({
  name,
  title: `Título de ${name}`,
  description: `Descrição de ${name}`,
  writes,
});

const manifest: SkillPackManifest = {
  revised_at: '2026-09-17',
  content_sha256: 'abc',
  published: [
    skill('operar-portfolioos', true),
    skill('preparar-agenda', false),
    skill('granola-reuniao', true),
    skill('cobrar-indicadores', true),
    skill('apresentacao-portfolio', false),
  ],
  unpublished: [
    {
      name: 'auditoria-qualitativa',
      title: 'Auditar o portfólio',
      description: 'Analisa textos qualitativos.',
      reason: 'Aguardando aprovação.',
    },
  ],
};

describe('Ai', () => {
  let httpMock: HttpTestingController;

  async function mount(): Promise<{ element: HTMLElement; detect: () => void }> {
    await TestBed.configureTestingModule({
      imports: [Ai],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
    const fixture = TestBed.createComponent(Ai);
    fixture.detectChanges();
    return { element: fixture.nativeElement as HTMLElement, detect: () => fixture.detectChanges() };
  }

  async function render(): Promise<HTMLElement> {
    const { element, detect } = await mount();
    httpMock.expectOne(MANIFEST_URL).flush(manifest);
    detect();
    return element;
  }

  afterEach(() => {
    try {
      httpMock.verify();
    } finally {
      TestBed.resetTestingModule();
    }
  });

  it('should announce loading while the package manifest is on its way', async () => {
    const { element } = await mount();

    expect(element.querySelector('.ai-page')?.getAttribute('aria-busy')).toBe('true');
    expect(element.querySelector('[role="status"]')?.textContent).toContain('Carregando');
    expect(element.querySelector('[data-included-skill]')).toBeNull();

    httpMock.expectOne(MANIFEST_URL).flush(manifest);
  });

  it('should say the contents failed to load instead of showing an empty package', async () => {
    const { element, detect } = await mount();
    httpMock.expectOne(MANIFEST_URL).flush(null, { status: 404, statusText: 'Not Found' });
    detect();

    expect(element.textContent).toContain('Não foi possível carregar o conteúdo do pacote');
    expect(element.querySelector('.ai-page')?.hasAttribute('aria-busy')).toBe(false);
    // Downloading does not depend on the manifest.
    expect(element.querySelector('.package-download')).toBeTruthy();
    expect(element.querySelector('time')).toBeNull();
  });

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

    expect(included.map((item) => item.dataset['includedSkill'])).toEqual(
      manifest.published.map((item) => item.name),
    );
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
    expect(element.querySelector('time[datetime="2026-09-17"]')?.textContent).toBe('17/09/2026');
    expect(help?.textContent).toContain('instalação para toda a organização');
    expect(help?.textContent).toContain('Cowork');
  });

  // Chasing an indicator ends in a WhatsApp send, and that send lands on a
  // choice between the desktop app and WhatsApp Web — two independent
  // sessions. The setup page is where a person prepares the environment, so it
  // is where the connection is worth naming, before a queue dead-ends on a QR
  // code. The agent-driven mode is stricter: it cannot reach a native app.
  it('should orient connecting WhatsApp before the agent sends anything', async () => {
    const element = await render();
    const packageCard = element.querySelector<HTMLElement>('.package-card');

    expect(packageCard?.textContent).toContain('aplicativo do computador ou o WhatsApp Web');
    expect(packageCard?.textContent).toContain('conexões separadas');
    expect(packageCard?.textContent).toContain('no mesmo navegador');
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
