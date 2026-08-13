import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { NEVER, Observable, of, throwError } from 'rxjs';

import { routes } from '../../app.routes';
import { authGuard } from '../../guards/auth.guard';
import { Skill, SkillListResponse } from '../../models/skill.model';
import { SkillService } from '../../services/skill.service';
import { Ai } from './ai';

describe('Ai', () => {
  let fixture: ComponentFixture<Ai>;
  let component: Ai;

  const platformSkill: Skill = {
    name: 'operar-portfolioos',
    description: 'Consulta e administra toda a plataforma pelo navegador.',
    version: '2026-08-13',
    writes: true,
    reads_external: true,
    published: true,
    files: ['SKILL.md', 'references/monitoring.md'],
  };
  const readSkill: Skill = {
    name: 'preparar-agenda',
    description: 'Prepara a próxima conversa usando os dados da startup.',
    version: '2026-08-11',
    writes: false,
    reads_external: true,
    published: true,
    files: ['SKILL.md'],
  };
  const writeSkill: Skill = {
    name: 'granola-reuniao',
    description: 'Prepara e registra uma reunião depois da confirmação.',
    version: '2026-08-11',
    writes: true,
    reads_external: true,
    published: true,
    files: ['SKILL.md'],
  };
  const blockedSkill: Skill = {
    name: 'auditoria-qualitativa',
    description: 'Encontra riscos e contradições no texto livre.',
    version: '2026-08-11',
    writes: false,
    reads_external: true,
    published: false,
    blocked_reason: 'Aguardando aprovação da política de trânsito de dados.',
  };
  const catalog: SkillListResponse = {
    items: [platformSkill, readSkill, writeSkill, blockedSkill],
    total: 4,
  };
  const skillServiceSpy = {
    list: vi.fn<() => Observable<SkillListResponse>>(),
    downloadPack: vi.fn<() => Observable<Blob>>(),
  };

  async function render(
    response: Observable<SkillListResponse> = of(catalog),
  ): Promise<HTMLElement> {
    skillServiceSpy.list.mockReturnValue(response);
    fixture = TestBed.createComponent(Ai);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  beforeEach(async () => {
    skillServiceSpy.downloadPack.mockReturnValue(
      of(new Blob(['portfolioOS'], { type: 'application/zip' })),
    );
    await TestBed.configureTestingModule({
      imports: [Ai],
      providers: [provideNoopAnimations(), { provide: SkillService, useValue: skillServiceSpy }],
    }).compileComponents();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  it('should present one portfolioOS package and one download call to action', async () => {
    const element = await render();
    const packageCard = element.querySelector<HTMLElement>('.package-card');
    const downloadButtons = element.querySelectorAll<HTMLButtonElement>('.package-download');

    expect(element.querySelector('h1')?.textContent?.trim()).toBe('IA no portfolioOS');
    expect(packageCard?.querySelector('h2')?.textContent).toContain('Pacote de skills portfolioOS');
    expect(packageCard?.textContent).toContain('pacote');
    expect(packageCard?.textContent).toContain('Instale uma vez');
    expect(packageCard?.textContent).toContain('descobre automaticamente');
    expect(downloadButtons).toHaveLength(1);
    expect(downloadButtons[0].type).toBe('button');
    expect(downloadButtons[0].getAttribute('aria-label')).toBe(
      'Baixar pacote de skills portfolioOS',
    );
  });

  it('should fetch the package through the authenticated HTTP pipeline', async () => {
    const createObjectUrl = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:portfolioos');
    const revokeObjectUrl = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
    const anchorClick = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => undefined);
    const element = await render();

    element.querySelector<HTMLButtonElement>('.package-download')?.click();
    fixture.detectChanges();

    expect(skillServiceSpy.downloadPack).toHaveBeenCalledOnce();
    expect(createObjectUrl).toHaveBeenCalledWith(expect.any(Blob));
    expect(anchorClick).toHaveBeenCalledOnce();
    expect(revokeObjectUrl).toHaveBeenCalledWith('blob:portfolioos');
  });

  it('should expose the package preparation state in the download button name', async () => {
    skillServiceSpy.downloadPack.mockReturnValue(NEVER);
    const element = await render();
    const downloadButton = element.querySelector<HTMLButtonElement>('.package-download');

    downloadButton?.click();
    fixture.detectChanges();

    expect(downloadButton?.disabled).toBe(true);
    expect(downloadButton?.getAttribute('aria-label')).toBe(
      'Preparando pacote de skills portfolioOS',
    );
  });

  it('should report a package download failure and allow retrying', async () => {
    skillServiceSpy.downloadPack.mockReturnValue(throwError(() => new Error('offline')));
    const element = await render();
    const downloadButton = element.querySelector<HTMLButtonElement>('.package-download');

    downloadButton?.click();
    fixture.detectChanges();

    expect(element.querySelector('[role="alert"]')?.textContent).toContain(
      'Não foi possível baixar o pacote',
    );
    expect(downloadButton?.disabled).toBe(false);
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
    }
    expect(instructions[0].textContent).toContain('plano');
    expect(instructions[1].textContent).toContain('plano');
  });

  it('should remove per-skill actions, setup branches and copy controls', async () => {
    const element = await render();

    expect(element.querySelector('[role="tab"], input[type="radio"]')).toBeNull();
    expect(element.querySelector('.start-button, .copy-button, [data-prompt-skill]')).toBeNull();
    expect(element.textContent).not.toContain('Começar');
    expect(element.querySelectorAll('a, button')).toHaveLength(1);
  });

  it('should derive an informative package list from published API skills', async () => {
    const element = await render();
    const included = Array.from(element.querySelectorAll<HTMLElement>('[data-included-skill]'));

    expect(included).toHaveLength(3);
    const platform = element.querySelector<HTMLElement>(
      '[data-included-skill="operar-portfolioos"]',
    );
    const agenda = element.querySelector<HTMLElement>('[data-included-skill="preparar-agenda"]');
    const meeting = element.querySelector<HTMLElement>('[data-included-skill="granola-reuniao"]');
    expect(platform?.querySelector('h3')?.textContent).toContain('Operar toda a plataforma');
    expect(platform?.textContent).toContain('Escrita com confirmação');
    expect(agenda?.querySelector('h3')?.textContent).toContain('Preparar agenda');
    expect(agenda?.textContent).toContain('Somente leitura');
    expect(meeting?.querySelector('h3')?.textContent).toContain('Registrar reunião');
    expect(meeting?.textContent).toContain('Escrita com confirmação');
    expect(included.every((item) => item.querySelector('a, button, input') === null)).toBe(true);
    expect(element.querySelector('[data-included-skill="auditoria-qualitativa"]')).toBeNull();
  });

  it('should keep blocked skills outside the package and release them from API data', async () => {
    const element = await render();
    const blockedSection = element.querySelector<HTMLElement>('.blocked-section');
    const blockedItem = element.querySelector<HTMLElement>(
      '[data-blocked-skill="auditoria-qualitativa"]',
    );

    expect(blockedSection?.textContent).toContain('não fazem parte do pacote atual');
    expect(blockedItem?.textContent).toContain('Auditar o portfólio');
    expect(blockedItem?.textContent).toContain(blockedSkill.blocked_reason);
    expect(blockedItem?.querySelector('a, button, input')).toBeNull();

    component.skills.set([
      readSkill,
      writeSkill,
      { ...blockedSkill, published: true, blocked_reason: undefined, files: ['SKILL.md'] },
    ]);
    fixture.detectChanges();

    expect(element.querySelector('.blocked-section')).toBeNull();
    expect(element.querySelector('[data-included-skill="auditoria-qualitativa"]')).toBeTruthy();
  });

  it('should show natural request examples without presenting them as skill prompts', async () => {
    const element = await render();
    const examples = element.querySelector<HTMLElement>('.request-examples');

    expect(examples?.querySelectorAll('q')).toHaveLength(4);
    expect(examples?.textContent).toContain('Prepare a agenda para minha reunião');
    expect(examples?.textContent).toContain('Registre minha conversa do Granola');
    expect(examples?.textContent).toContain('ainda não reportaram');
    expect(examples?.textContent).toContain('Mova o deal');
    expect(examples?.querySelector('button, [data-prompt-skill]')).toBeNull();
  });

  it('should keep concise safety, help and the guidance review date near setup', async () => {
    const element = await render();
    const packageCard = element.querySelector<HTMLElement>('.package-card');
    const help = element.querySelector<HTMLDetailsElement>('.support-details');

    expect(packageCard?.textContent).toContain('Nunca digite sua senha no chat');
    expect(packageCard?.textContent).toContain('link de indicador é um segredo');
    expect(packageCard?.textContent).toContain('Revise a prévia antes de permitir uma gravação');
    expect(element.querySelector('time[datetime="2026-08-13"]')).toBeTruthy();
    expect(help?.textContent).toContain('instalação para toda a organização');
    expect(help?.textContent).toContain('Cowork');
  });

  it('should announce loading, loaded and failure states', async () => {
    let element = await render(NEVER);
    expect(element.querySelector('.ai-page')?.getAttribute('aria-busy')).toBe('true');
    expect(element.querySelector('[role="status"]')?.textContent).toContain('Carregando');

    fixture.destroy();
    element = await render();
    expect(element.querySelector('.ai-page')?.hasAttribute('aria-busy')).toBe(false);
    expect(element.querySelector('#package-contents')).toBeTruthy();

    fixture.destroy();
    element = await render(throwError(() => new Error('offline')));
    expect(element.querySelector('.ai-page')?.hasAttribute('aria-busy')).toBe(false);
    expect(element.querySelector('[role="alert"]')?.textContent).toContain(
      'Não foi possível carregar',
    );
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
