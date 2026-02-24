import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HealthBar } from './health-bar';
import { HealthDistribution } from '../../models/portfolio.model';

@Component({
  imports: [HealthBar],
  template: `<app-health-bar [distribution]="distribution" />`,
})
class TestHost {
  distribution: HealthDistribution = { healthy: 0, warning: 0, critical: 0 };
}

describe('HealthBar', () => {
  let fixture: ComponentFixture<TestHost>;
  let host: TestHost;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TestHost],
    }).compileComponents();

    fixture = TestBed.createComponent(TestHost);
    host = fixture.componentInstance;
  });

  it('should show no segments for empty distribution', () => {
    host.distribution = { healthy: 0, warning: 0, critical: 0 };
    fixture.detectChanges();
    const component = fixture.debugElement.children[0].componentInstance as HealthBar;
    expect(component.total()).toBe(0);
    expect(component.segments()).toEqual([]);
  });

  it('should compute correct percentages', () => {
    host.distribution = { healthy: 3, warning: 1, critical: 1 };
    fixture.detectChanges();
    const component = fixture.debugElement.children[0].componentInstance as HealthBar;
    expect(component.total()).toBe(5);
    const segments = component.segments();
    expect(segments.length).toBe(3);
    expect(segments[0].pct).toBe(60);
    expect(segments[1].pct).toBe(20);
    expect(segments[2].pct).toBe(20);
  });

  it('should filter out zero-count segments', () => {
    host.distribution = { healthy: 2, warning: 0, critical: 1 };
    fixture.detectChanges();
    const component = fixture.debugElement.children[0].componentInstance as HealthBar;
    const segments = component.segments();
    expect(segments.length).toBe(2);
    expect(segments.map((s) => s.label)).toEqual(['Saudavel', 'Critico']);
  });
});
