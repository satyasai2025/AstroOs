import { test, expect } from '@playwright/test';

test.describe('Planet Explorer Canonical Routing & Shared Context E2E', () => {
  test.beforeEach(async ({ context, page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('astro_access_token', 'mock_e2e_jwt_access_token');
      window.localStorage.setItem('astro_refresh_token', 'mock_e2e_jwt_refresh_token');
      window.localStorage.setItem('astroos_access_token', 'mock_e2e_jwt_access_token');
    });

    await context.addCookies([
      {
        name: 'access_token',
        value: 'mock_e2e_jwt_access_token',
        domain: 'localhost',
        path: '/',
      },
    ]);
  });

  test('Legacy /charts?view=planets redirects to canonical /charts/planets', async ({ page }) => {
    await page.goto('/charts?view=planets');
    await expect(page).toHaveURL(/\/charts\/planets/);
  });

  test('Planet Explorer renders header, 9-graha bar, and right sidebar', async ({ page }) => {
    await page.goto('/charts/planets');
    await expect(page.locator('h1')).toContainText('Planet Explorer');
    await expect(page.locator('text=13-Parameter Structural Map')).toBeVisible();
    await expect(page.locator('text=Strength Overview')).toBeVisible();
    await expect(page.locator('text=Key Relations')).toBeVisible();
  });
});
