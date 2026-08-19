import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { formatIsoDate } from '../../models/formatters';
import { Skill } from '../../models/skill.model';
import { SkillService } from '../../services/skill.service';

const SKILL_TITLES: Record<string, string> = {
  'operar-portfolioos': 'Operar toda a plataforma',
  'preparar-agenda': 'Preparar agenda de uma startup',
  'granola-reuniao': 'Registrar reunião de conselho',
  'cobrar-indicadores': 'Cobrar indicadores em falta',
  'auditoria-qualitativa': 'Auditar o portfólio',
};

const SKILL_ORDER: Record<string, number> = {
  'operar-portfolioos': 0,
  'preparar-agenda': 1,
  'granola-reuniao': 2,
  'cobrar-indicadores': 3,
};

@Component({
  selector: 'app-ai',
  imports: [MatButtonModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './ai.html',
  styleUrl: './ai.scss',
})
export class Ai implements OnInit {
  private readonly skillService = inject(SkillService);

  readonly loading = signal(true);
  readonly skills = signal<Skill[] | null>(null);
  readonly downloading = signal(false);
  readonly downloadFailed = signal(false);
  readonly publishedSkills = computed(() =>
    (this.skills() ?? [])
      .filter((skill) => skill.published)
      .sort((left, right) => (SKILL_ORDER[left.name] ?? 99) - (SKILL_ORDER[right.name] ?? 99)),
  );
  readonly blockedSkills = computed(() =>
    (this.skills() ?? []).filter((skill) => !skill.published),
  );

  /**
   * The newest version among the published capabilities, in ISO form.
   *
   * Derived, never typed by hand: the page used to hardcode a date and quietly
   * drifted behind the package it describes — announcing instructions older
   * than the ones being downloaded, which is the exact failure the notice is
   * there to prevent.
   */
  readonly revisedAt = computed(() => {
    const versions = this.publishedSkills()
      .map((skill) => skill.version)
      .filter((version): version is string => !!version)
      .sort();
    return versions.at(-1) ?? null;
  });

  /** `2026-08-19` → `19/08/2026`, the form the page shows. */
  readonly revisedAtLabel = computed(() => {
    const iso = this.revisedAt();
    if (iso === null) return null;
    const [year, month, day] = iso.split('-');
    return `${day}/${month}/${year}`;
  });

  ngOnInit(): void {
    this.skillService.list().subscribe({
      next: (response) => {
        this.skills.set(response.items);
        this.loading.set(false);
      },
      error: () => {
        this.skills.set(null);
        this.loading.set(false);
      },
    });
  }

  downloadPack(): void {
    if (this.downloading()) return;

    this.downloading.set(true);
    this.downloadFailed.set(false);
    this.skillService.downloadPack().subscribe({
      next: (packageBlob) => {
        const objectUrl = URL.createObjectURL(packageBlob);
        const downloadLink = document.createElement('a');
        downloadLink.href = objectUrl;
        downloadLink.download = 'portfolioos.zip';
        downloadLink.hidden = true;
        document.body.append(downloadLink);
        try {
          downloadLink.click();
        } finally {
          downloadLink.remove();
          URL.revokeObjectURL(objectUrl);
          this.downloading.set(false);
        }
      },
      error: () => {
        this.downloadFailed.set(true);
        this.downloading.set(false);
      },
    });
  }

  skillTitle(skill: Skill): string {
    return SKILL_TITLES[skill.name] ?? this.titleFromName(skill.name);
  }

  skillStatus(skill: Skill): string {
    return skill.writes ? 'Escrita com confirmação' : 'Somente leitura';
  }

  formatVersion(version: string): string {
    return formatIsoDate(version) ?? version;
  }

  private titleFromName(name: string): string {
    const words = name.replaceAll('-', ' ');
    return `${words.charAt(0).toUpperCase()}${words.slice(1)}`;
  }
}
