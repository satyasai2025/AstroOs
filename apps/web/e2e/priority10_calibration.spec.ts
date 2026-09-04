import { test, expect } from '@playwright/test';

test.describe('Priority 10 — Calibration & Audit Trail E2E Verification', () => {
  test.beforeEach(async ({ page }) => {
    // Auto-accept any browser window.alert dialogs
    page.on('dialog', (dialog) => dialog.accept());

    // Intercept backend requests for deterministic Playwright E2E execution
    await page.route('**/api/v1/research/calibration/profiles*', async (route, request) => {
      if (request.url().includes('activate')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            profile_id: 'cand-f892a10c',
            name: 'Candidate Weight Profile 10',
            description: 'Calibrated candidate profile',
            dataset_id: 'ds-test-01',
            status: 'ACTIVE',
            technique_weights: { chara_dasha_v1: 0.85 },
            primary_brier_score: 0.042,
            primary_log_loss: 0.135,
            diagnostic_f1: 0.875,
            diagnostic_roc_auc: 0.920,
            roc_auc_status: 'VALID',
            created_at: '2026-08-21T00:00:00Z',
            activated_at: '2026-08-21T12:00:00Z',
            activated_by: 'researcher',
          }),
        });
        return;
      }

      if (request.method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              profile_id: 'cand-f892a10c',
              name: 'Candidate Weight Profile 10',
              description: 'Calibrated candidate profile',
              dataset_id: 'ds-test-01',
              status: 'DRAFT_CANDIDATE',
              technique_weights: { chara_dasha_v1: 0.85 },
              primary_brier_score: 0.042,
              primary_log_loss: 0.135,
              diagnostic_f1: 0.875,
              diagnostic_roc_auc: 0.920,
              roc_auc_status: 'VALID',
              created_at: '2026-08-21T00:00:00Z',
            },
          ]),
        });
      } else {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            profile_id: 'cand-new123',
            name: 'New Draft Candidate Profile',
            description: 'User generated draft',
            dataset_id: 'ds-test-01',
            status: 'DRAFT_CANDIDATE',
            technique_weights: { chara_dasha_v1: 0.85 },
            primary_brier_score: 0.042,
            primary_log_loss: 0.135,
            diagnostic_f1: 0.875,
            diagnostic_roc_auc: 0.920,
            roc_auc_status: 'VALID',
            created_at: '2026-08-21T00:00:00Z',
          }),
        });
      }
    });

    await page.route('**/api/v1/research/calibration/audit-trail*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            audit_id: 'audit-101',
            timestamp: '2026-08-21T12:00:00Z',
            dataset_id: 'ds-test-01',
            dataset_version: '1.0',
            event_type: 'marriage',
            train_events_count: 70,
            holdout_events_count: 30,
            primary_brier_score: 0.042,
            primary_log_loss: 0.135,
            diagnostic_f1: 0.875,
            diagnostic_roc_auc: 0.920,
            roc_auc_status: 'VALID',
            candidate_profile_id: 'cand-f892a10c',
            status: 'DRAFT_CANDIDATE',
            action: 'CANDIDATE_PROFILE_CREATED',
            notes: 'Created candidate profile',
          },
        ]),
      });
    });
  });

  test('should render calibration dashboard, verify draft status, and allow explicit activation', async ({ page }) => {
    await page.goto('http://localhost:3000/research/backtest');

    // Verify Header
    await expect(page.locator('h2')).toContainText('Autonomous Backtesting & Dynamic Weight Calibration');

    // Verify Draft Status Badge
    await expect(page.getByText('DRAFT_CANDIDATE').first()).toBeVisible();

    // Verify Primary Metrics (Brier Score & Log Loss)
    await expect(page.getByText('Primary Brier:').first()).toBeVisible();

    // Click Explicit Activation
    const activateBtn = page.getByRole('button', { name: /Explicitly Activate Candidate Profile/i });
    await activateBtn.click();
  });

  test('should display immutable calibration audit trail log table', async ({ page }) => {
    await page.goto('http://localhost:3000/research/backtest');

    // Switch to Audit Log tab
    const auditTabBtn = page.getByRole('button', { name: /Immutable Audit Log/i });
    await auditTabBtn.click();

    // Verify Table Headers & Log Row
    await expect(page.getByText('Immutable Calibration Audit Trail')).toBeVisible();
    await expect(page.getByText('audit-101')).toBeVisible();
  });
});
