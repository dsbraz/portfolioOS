import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { KpiCard } from './kpi-card';

@Component({
  imports: [KpiCard],
  template: `
    <app-kpi-card
      [label]="label"
      [value]="value"
      [subtitle]="subtitle"
      [tone]="tone"
      [supportingIcon]="supportingIcon"
    />
  `,
})
class TestHost {
  label = 'Total Startups';
  value = '12';
  subtitle = 'No portfolio';
  tone: 'default' | 'positive' | 'negative' | 'neutral' = 'positive';
  supportingIcon: string | null = 'trending_up';
}

describe('KpiCard', () => {
  let fixture: ComponentFixture<TestHost>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TestHost],
    }).compileComponents();

    fixture = TestBed.createComponent(TestHost);
    fixture.detectChanges();
  });

  it('should render label and value', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Total Startups');
    expect(el.textContent).toContain('12');
  });

  it('should render subtitle when provided', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('No portfolio');
  });

  it('should apply the tone to the footnote', () => {
    const foot = fixture.nativeElement.querySelector('.kpi-foot') as HTMLElement | null;
    expect(foot?.classList.contains('kpi-foot-positive')).toBe(true);
  });

  // A tone-colored footnote must keep its icon: the brand never signals state
  // with color alone.
  it('should pair a toned footnote with its supporting icon', () => {
    const icon = fixture.nativeElement.querySelector('.kpi-foot-icon') as HTMLElement | null;
    expect(icon).not.toBeNull();
    expect(icon?.textContent).toContain('trending_up');
  });
});
