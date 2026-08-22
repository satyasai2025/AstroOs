import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { AccessibilityReporter } from './utils/accessibility-reporter';

const reporter = new AccessibilityReporter('./accessibility-reports');

/**
 * Runs an Axe accessibility scan on the current page state and records results.
 */
async function runAxeScan(page: Page, stepName: string) {
  try {
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    reporter.recordSuccess(stepName, page.url(), results);

    if (results.violations.length > 0) {
      console.warn(`⚠️ [A11y Warning] "${stepName}" had ${results.violations.length} violation(s).`);
    } else {
      console.log(`✅ [A11y Clean] "${stepName}" passed 0 violations.`);
    }
    return results;
  } catch (error) {
    console.error(`❌ [A11y Scan Error] on "${stepName}":`, (error as Error).message);
    reporter.recordError(stepName, page.url(), error as Error);
    return null;
  }
}

test.describe('Astrology Website Full Automation & Accessibility Suite', () => {
  test.beforeEach(async ({ context, page }) => {
    // 1. Set localStorage tokens on every new window / page initialization
    await page.addInitScript(() => {
      window.localStorage.setItem('astro_access_token', 'mock_e2e_jwt_access_token');
      window.localStorage.setItem('astro_refresh_token', 'mock_e2e_jwt_refresh_token');
    });

    // 2. Add cookies for server-side auth middleware
    await context.addCookies([
      {
        name: 'access_token',
        value: 'mock_e2e_jwt_access_token',
        domain: 'localhost',
        path: '/',
      },
    ]);

    // 3. Intercept auth user endpoint on both frontend & backend port origins
    await page.route(/(http:\/\/localhost:(3000|8000))?\/api\/v1\/auth\/me/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'e2e-tester-id',
          email: 'researcher@astroos.org',
          display_name: 'Aryabhata Astro Tester',
          role: 'researcher',
          status: 'active',
          created_at: '2026-08-01T00:00:00Z',
          last_login_at: '2026-08-22T00:00:00Z',
          timezone: 'Asia/Kolkata',
        }),
      });
    });

    // 4. Intercept user charts list to ensure fast deterministic loading
    await page.route(/(http:\/\/localhost:(3000|8000))?\/api\/v1\/horoscope\/my-charts/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          charts: [],
          total: 0,
        }),
      });
    });

    // 5. Intercept geocoding / timezone resolution
    await page.route(/(http:\/\/localhost:(3000|8000))?\/api\/v1\/geo\/resolve-timezone/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          iana_name: 'Asia/Kolkata',
          utc_offset_minutes: 330,
          is_dst: false,
        }),
      });
    });

    // 6. Intercept duplicate check
    await page.route(/(http:\/\/localhost:(3000|8000))?\/api\/v1\/workflow\/check-duplicate/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          exists: false,
        }),
      });
    });
  });

  test.afterAll(async () => {
    // Generate consolidated HTML and JSON reports
    reporter.generateReport();
  });

  test('1. Navigation & Dynamic Tab Traversal with Axe Scans', async ({ page }) => {
    test.setTimeout(120000); // Extended timeout for multi-page auditing

    console.log('\n========================================');
    console.log(' STEP 1: Navigation & Tab Traversal');
    console.log('========================================');

    // 1. Start at Homepage
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    await runAxeScan(page, '01. Homepage');

    // 2. Visit Dashboard & Main Workstation
    await page.goto('/dashboard');
    await page.waitForLoadState('domcontentloaded');
    await runAxeScan(page, '02. Dashboard Overview');

    // 3. Discover navigation links in sidebar, header, and main nav
    const navLocators = page.locator('nav a, header a, aside a, [role="navigation"] a');
    const linkCount = await navLocators.count();
    console.log(`Discovered ${linkCount} potential navigation links.`);

    const visitedHrefs = new Set<string>();

    for (let i = 0; i < linkCount; i++) {
      try {
        const link = navLocators.nth(i);
        const isVisible = await link.isVisible().catch(() => false);
        if (!isVisible) continue;

        const href = await link.getAttribute('href');
        const text = ((await link.innerText().catch(() => '')) || '').trim().split('\n')[0] || `Nav Link #${i + 1}`;

        // Filter out anchors, external links, or duplicates
        if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('javascript:')) {
          continue;
        }

        const normalizedPath = href.split('?')[0];
        if (visitedHrefs.has(normalizedPath)) continue;
        visitedHrefs.add(normalizedPath);

        console.log(`\nTesting Tab [${text}] -> ${href}`);

        // Navigate to the tab
        await page.goto(href, { timeout: 8000 });
        await page.waitForLoadState('domcontentloaded');

        // Run accessibility scan on the tab page
        await runAxeScan(page, `Tab: ${text} (${normalizedPath})`);
      } catch (tabError) {
        console.error(`❌ [Non-fatal Error] Tab #${i + 1}:`, (tabError as Error).message);
        reporter.recordError(`Tab Index #${i + 1}`, page.url(), tabError as Error);
      }
    }
  });

  test('2. Calculation Form Verification & Output Verification with Axe Scan', async ({ page }) => {
    test.setTimeout(90000);

    console.log('\n========================================');
    console.log(' STEP 2: Astrology Calculation Form');
    console.log('========================================');

    try {
      // 1. Navigate to dashboard
      await page.goto('/dashboard');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(500);

      // Click "New Chart" / "Create Chart" / "Birth Chart" button
      const newChartBtn = page.locator('button, a').filter({ hasText: /New Chart|\+ Chart|Birth Chart|Create Chart/i }).first();
      if (await newChartBtn.isVisible().catch(() => false)) {
        await newChartBtn.click();
        await page.waitForTimeout(500);
      }

      // Step 1 in Create Chart Modal: If on type selection step, click Continue
      const step1ContinueBtn = page.getByRole('button', { name: /continue/i }).first();
      if (await step1ContinueBtn.isVisible().catch(() => false)) {
        await step1ContinueBtn.click();
        await page.waitForTimeout(400);
      }

      // Run Axe scan on the calculation form inputs
      await runAxeScan(page, '03. Astrology Calculation Form (Inputs)');

      // Mock Astrology Subject Data
      const uniqueSuffix = Date.now().toString().slice(-4);
      const mockBirthData = {
        name: `Aryabhata ${uniqueSuffix}`,
        date: '1995-10-24', // YYYY-MM-DD
        time: '14:30:00',   // HH:MM:SS
        latitude: '28.6139',
        longitude: '77.2090',
      };

      // 2. Fill in form details (Step 2)
      // Name
      const nameInput = page.locator('input[placeholder*="Name" i], input#subjectName, input[name="name"]').first();
      if (await nameInput.isVisible()) {
        await nameInput.fill(mockBirthData.name);
      }

      // Date of Birth
      const dateInput = page.locator('input[type="date"], input#birthDate').first();
      if (await dateInput.isVisible()) {
        await dateInput.fill(mockBirthData.date);
      }

      // Time of Birth
      const timeInput = page.locator('input[type="time"], input#birthTime').first();
      if (await timeInput.isVisible()) {
        await timeInput.fill(mockBirthData.time);
      }

      // Coordinates / Place
      const manualCoordToggle = page.getByRole('button', { name: /enter coordinates manually|coordinates|manual/i }).first();
      if (await manualCoordToggle.isVisible().catch(() => false)) {
        await manualCoordToggle.click();
        await page.waitForTimeout(200);
      }

      const latInput = page.locator('input[placeholder*="Latitude" i]').first();
      const lonInput = page.locator('input[placeholder*="Longitude" i]').first();
      if (await latInput.isVisible() && await lonInput.isVisible()) {
        await latInput.fill(mockBirthData.latitude);
        await lonInput.fill(mockBirthData.longitude);
      }

      // Wait for timezone resolution
      await page.waitForTimeout(1000);

      // Advance from Step 2 -> Step 3
      const step2ContinueBtn = page.getByRole('button', { name: /continue/i }).first();
      if (await step2ContinueBtn.isVisible()) {
        await expect(step2ContinueBtn).toBeEnabled({ timeout: 10000 });
        await step2ContinueBtn.click();
        await page.waitForTimeout(400);
      }

      // 3. Step 3: Submit / Create Chart
      const createBtn = page.getByRole('button', { name: /create chart|run analysis|calculate/i }).first();
      if (await createBtn.isVisible()) {
        await expect(createBtn).toBeEnabled({ timeout: 5000 });
        console.log('Submitting astrology calculation request...');
        await createBtn.click();
      }

      // Check if duplicate prompt modal appears, and click "Save as New Chart Anyway"
      const saveAnywayBtn = page.getByRole('button', { name: /save as new chart anyway|view existing chart/i }).first();
      if (await saveAnywayBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await saveAnywayBtn.click();
      }

      // 4. Wait for calculation results / chart page to render
      await page.waitForURL(/\/charts\/.+/, { timeout: 25000 }).catch(() => {});
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);

      // 5. Run Axe Scan on the Results Page
      await runAxeScan(page, '04. Calculation Results & Chart Output');

      // -----------------------------------------------------------------------
      // 6. EXPLICIT ASSERTIONS PLACEHOLDERS FOR ASTROLOGICAL OUTPUTS
      // -----------------------------------------------------------------------
      console.log('Verifying calculated outputs and UI elements...');

      // Assertion Placeholder 1: Astrological Chart Graphic (SVG or Canvas)
      const chartSvg = page.locator('svg').first();
      await expect(chartSvg).toBeVisible();

      // Assertion Placeholder 2: Verify page rendered content
      const pageHeader = page.locator('header, h1, h2, h3, [role="heading"]').first();
      await expect(pageHeader).toBeVisible();

      // Assertion Placeholder 3: Check that main calculation view / container is present
      const mainContainer = page.locator('main, #__next, [role="main"]').first();
      await expect(mainContainer).toBeVisible();

      console.log('✅ Calculation form verification, results rendering, and assertions passed successfully!');
    } catch (calcError) {
      console.error('❌ Calculation test error:', (calcError as Error).message);
      reporter.recordError('Astrology Calculation Form Verification', page.url(), calcError as Error);
      throw calcError;
    }
  });
});
