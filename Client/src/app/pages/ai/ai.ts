import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { formatIsoDate } from '../../models/formatters';
import { SkillPackManifest } from '../../models/skill-pack.model';
import { SkillPackService } from '../../services/skill-pack.service';

@Component({
  selector: 'app-ai',
  imports: [MatButtonModule, MatIconModule],
  templateUrl: './ai.html',
  styleUrl: './ai.scss',
})
export class Ai implements OnInit {
  private readonly skillPackService = inject(SkillPackService);

  /** Generated with the zip, so the page never lists a package it does not serve. */
  readonly manifest = signal<SkillPackManifest | null>(null);
  readonly loading = signal(true);
  readonly revisedAtLabel = computed(() => formatIsoDate(this.manifest()?.revised_at));

  ngOnInit(): void {
    this.skillPackService.getManifest().subscribe({
      next: (manifest) => {
        this.manifest.set(manifest);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
