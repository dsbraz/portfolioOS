import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { KpiCard } from './kpi-card';

@Component({
  imports: [KpiCard],
  template: `<app-kpi-card [icon]="icon" [label]="label" [value]="value" [subtitle]="subtitle" />`,
})
class TestHost {
  icon = 'business';
  label = 'Total Startups';
  value = '12';
  subtitle = 'No portfolio';
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
});
