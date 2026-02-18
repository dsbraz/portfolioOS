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
});
