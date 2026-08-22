import { test, expect } from '@playwright/test';

test.describe('AstroDSL Rule IDE & Sandbox E2E Verification', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept backend requests for deterministic Playwright E2E execution
    await page.route('**/api/v1/techniques/custom/', async (route, request) => {
      if (request.method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              rule_id: 'custom-gajakesari-01',
              name: 'Gajakesari Yoga',
              description: 'Jupiter in Kendra from Moon',
              dsl_source: 'PLANET("Jupiter").house IN KENDRA_HOUSES',
              category: 'classical_yoga',
              tags: ['gajakesari', 'jupiter'],
              author: 'AstroOS Core Engine',
              version: '1.0.0',
              created_at: '2026-08-21T00:00:00Z',
            },
          ]),
        });
      } else {
        await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ message: 'Success' }) });
      }
    });

    await page.route('**/api/v1/techniques/custom/dsl/validate', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          is_valid: true,
          dsl_source: 'PLANET("Jupiter").house IN KENDRA_HOUSES',
          ast_representation: 'BinaryOp(FunctionCall(PLANET), IN, List)',
        }),
      });
    });

    await page.route('**/api/v1/techniques/custom/dsl/test-evaluate', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          is_satisfied: true,
          evaluated_value: true,
          execution_time_ms: 0.42,
          trace: [
            { node_type: 'FunctionCall', expression: 'PLANET("Jupiter")', result: '{house: 4}' },
            { node_type: 'BinaryOp', expression: 'house IN KENDRA_HOUSES', result: 'True' },
          ],
        }),
      });
    });
  });

  test('should render AstroDSL IDE component and validate preset template syntax', async ({ page }) => {
    await page.goto('http://localhost:3000/research/astro-dsl');

    // Verify Header Title & Badge
    await expect(page.locator('h2')).toContainText('AstroDSL Rule IDE & Sandbox Engine');
    await expect(page.getByText('Priority 9 Engine')).toBeVisible();

    // Verify Preset Templates
    const templateBtn = page.getByRole('button', { name: /Gajakesari Yoga/i });
    await expect(templateBtn).toBeVisible();

    // Click Validate Syntax
    const validateBtn = page.getByRole('button', { name: /Validate Syntax/i });
    await validateBtn.click();

    // Verify Valid Syntax Badge
    await expect(page.getByText('✓ Valid Syntax')).toBeVisible();
  });

  test('should evaluate AstroDSL rule against sandbox chart and show trace steps', async ({ page }) => {
    await page.goto('http://localhost:3000/research/astro-dsl');

    // Click Test on Chart
    const testBtn = page.getByRole('button', { name: /Test on Chart/i });
    await testBtn.click();

    // Verify Verdict Card & Execution Trace
    await expect(page.getByText('TRUE (Satisfied)')).toBeVisible();
    await expect(page.getByText('AST Tree-Walker Trace')).toBeVisible();
  });
});
