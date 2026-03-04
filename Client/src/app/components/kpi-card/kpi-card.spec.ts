import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { KpiCard } from './kpi-card';

@Component({
  imports: [KpiCard],
  template: `
    <app-kpi-card
      [icon]="icon"
      [label]="label"
      [value]="value"
      [subtitle]="subtitle"
      [tone]="tone"
      [supportingIcon]="supportingIcon"
    />
  `,
})
class TestHost {
  icon = 'business';
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

  it('should render supporting icon when provided', () => {
    const icon = fixture.nativeElement.querySelector('.kpi-subtitle-icon') as HTMLElement | null;
    expect(icon).not.toBeNull();
    expect(icon?.textContent).toContain('trending_up');
  });

  it('should apply positive tone class to icon wrapper', () => {
    const iconWrapper = fixture.nativeElement.querySelector('.kpi-icon-wrapper') as HTMLElement | null;
    expect(iconWrapper?.classList.contains('kpi-icon-positive')).toBe(true);
  });
});
