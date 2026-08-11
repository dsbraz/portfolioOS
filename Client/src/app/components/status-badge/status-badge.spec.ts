import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Component, signal } from '@angular/core';
import { By } from '@angular/platform-browser';

import { StatusBadge } from './status-badge';
import { StartupStatus, STARTUP_STATUS_CONFIG } from '../../models/startup.model';

@Component({
  imports: [StatusBadge],
  template: '<app-status-badge [status]="status()" />',
})
class TestHost {
  status = signal(StartupStatus.HEALTHY);
}

describe('StatusBadge', () => {
  let fixture: ComponentFixture<TestHost>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TestHost],
    }).compileComponents();
    fixture = TestBed.createComponent(TestHost);
    fixture.detectChanges();
  });

  it('should render the correct label for HEALTHY', () => {
    const text = fixture.debugElement.query(By.directive(StatusBadge)).nativeElement.textContent;
    expect(text).toContain(STARTUP_STATUS_CONFIG[StartupStatus.HEALTHY].label);
  });

  it('should render the correct label for CRITICAL', () => {
    fixture.componentInstance.status.set(StartupStatus.CRITICAL);
    fixture.detectChanges();
    const text = fixture.debugElement.query(By.directive(StatusBadge)).nativeElement.textContent;
    expect(text).toContain(STARTUP_STATUS_CONFIG[StartupStatus.CRITICAL].label);
  });

  // Regression: the badge used `mat-chip[highlighted]`, whose own container
  // color painted over the component background, so every status rendered with
  // the same tint. Each status must carry its own tone class.
  it('should apply a distinct tone class per status', () => {
    const toneOf = (status: StartupStatus) => {
      fixture.componentInstance.status.set(status);
      fixture.detectChanges();
      const pill = fixture.debugElement.query(By.css('.pill')).nativeElement as HTMLElement;
      return [...pill.classList].find((c) => c.startsWith('pill--'));
    };

    const tones = [
      toneOf(StartupStatus.HEALTHY),
      toneOf(StartupStatus.WARNING),
      toneOf(StartupStatus.CRITICAL),
    ];

    expect(tones.every(Boolean)).toBe(true);
    expect(new Set(tones).size).toBe(3);
  });

  // State must never be communicated by color alone: the written label is what
  // carries the meaning, and the dot is the brand's marker beside it.
  it('should name the status in text, not by color alone', () => {
    const pill = fixture.debugElement.query(By.css('.pill')).nativeElement as HTMLElement;
    expect(pill.textContent?.trim()).toBe(STARTUP_STATUS_CONFIG[StartupStatus.HEALTHY].label);
  });
});
