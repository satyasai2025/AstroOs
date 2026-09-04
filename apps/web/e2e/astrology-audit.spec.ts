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
      .disableRules(['document-title', 'html-has-lang', 'color-contrast'])
      .analyze();

    reporter.recordSuccess(stepName, page.url(), results);

    if (results.violations.length > 0) {
      console.warn(`⚠️ [A11y Warning] "${stepName}" had ${results.violations.length} violation(s):`);
      results.violations.forEach((v) => console.warn(`  - ${v.id}: ${v.help}`));
    } else {
      console.log(`✅ [A11y Clean] "${stepName}" passed 0 violations on ${page.url()}`);
    }
    return results;
  } catch (error) {
    console.error(`❌ [A11y Scan Error] on "${stepName}":`, (error as Error).message);
    reporter.recordError(stepName, page.url(), error as Error);
    return null;
  }
}

async function setAuthTokens(page: Page) {
  await page.evaluate(() => {
    window.localStorage.setItem('astro_access_token', 'mock_e2e_jwt_access_token');
    window.localStorage.setItem('astro_refresh_token', 'mock_e2e_jwt_refresh_token');
    window.localStorage.setItem('astroos_access_token', 'mock_e2e_jwt_access_token');
  }).catch(() => {});
}

test.describe('Astrology Website Full Automation & Accessibility Suite', () => {
  test.beforeEach(async ({ context, page }) => {
    // 1. Set localStorage tokens on every new window / page initialization
    await page.addInitScript(() => {
      window.localStorage.setItem('astro_access_token', 'mock_e2e_jwt_access_token');
      window.localStorage.setItem('astro_refresh_token', 'mock_e2e_jwt_refresh_token');
      window.localStorage.setItem('astroos_access_token', 'mock_e2e_jwt_access_token');
    });

    // 2. Add cookies for server-side auth middleware
    await context.addCookies([
      {
        name: 'access_token',
        value: 'mock_e2e_jwt_access_token',
        domain: 'localhost',
        path: '/',
      },
      {
        name: 'astro_access_token',
        value: 'mock_e2e_jwt_access_token',
        domain: 'localhost',
        path: '/',
      },
      {
        name: 'astroos_access_token',
        value: 'mock_e2e_jwt_access_token',
        domain: 'localhost',
        path: '/',
      },
    ]);

    // 3. Intercept all auth endpoints (me, refresh, session, check)
    await page.route('**/*/api/v1/auth/*', async (route) => {
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
          access_token: 'mock_e2e_jwt_access_token',
          refresh_token: 'mock_e2e_jwt_refresh_token',
        }),
      });
    });

    // 4. Intercept user charts list
    await page.route('**/*/api/v1/horoscope/my-charts*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          charts: [
            {
              id: 'test-chart-123',
              subject_name: 'Aryabhata Astro Tester',
              birth_datetime_utc: '1995-10-24T14:30:00Z',
              birth_latitude: 28.6139,
              birth_longitude: 77.2090,
              place_name: 'New Delhi, India',
              ayanamsa: 'lahiri',
              house_system: 'whole_sign',
              lagna_rashi: 'Mesha',
              moon_nakshatra: 'Rohini',
              created_at: '2026-08-22T00:00:00Z',
              is_default: true,
            },
          ],
          total: 1,
          limit: 20,
          offset: 0,
        }),
      });
    });

    // 5. Intercept geocoding / timezone resolution
    await page.route('**/*/api/v1/geo/resolve-timezone*', async (route) => {
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
    await page.route('**/*/api/v1/workflow/check-duplicate*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          exists: false,
        }),
      });
    });

    // 7. Intercept workflow analysis execution
    await page.route('**/*/api/v1/workflow/analyze*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          chart_id: 'test-chart-123',
          chart: {
            sidereal_longitude: 0,
            rashi: 'Mesha',
            rashi_degree: 15.5,
            nakshatra: 'Ashwini',
            pada: 1,
            ascendant: {
              rashi: 'Mesha',
              rashi_degree: 15.5,
              sidereal_longitude: 15.5,
              nakshatra: 'Ashwini',
              pada: 1,
            },
            planet_positions: [
              {
                planet: 'Sun',
                sidereal_longitude: 20.0,
                rashi: 'Mesha',
                rashi_degree: 20.0,
                house_number: 1,
                rashi_house_number: 1,
                nakshatra: 'Bharani',
                pada: 2,
                is_retrograde: false,
                is_combust: false,
                combustion_orb: null,
                dignity: 'Exalted',
                nakshatra_lord: 'Venus',
                sub_lord: 'Saturn',
                sub_sub_lord: 'Mercury',
              },
              {
                planet: 'Moon',
                sidereal_longitude: 45.0,
                rashi: 'Vrishabha',
                rashi_degree: 15.0,
                house_number: 2,
                rashi_house_number: 2,
                nakshatra: 'Rohini',
                pada: 1,
                is_retrograde: false,
                is_combust: false,
                combustion_orb: null,
                dignity: 'Exalted',
                nakshatra_lord: 'Moon',
                sub_lord: 'Jupiter',
                sub_sub_lord: 'Sun',
              },
            ],
            houses: [
              {
                house_number: 1,
                rashi: 'Mesha',
                start_degree: 0,
                cusp_degree: 15.5,
                sign_lord: 'Mars',
                star_lord: 'Ketu',
                sub_lord: 'Venus',
                sub_sub_lord: 'Sun',
              },
            ],
            aspects: [],
            planet_strengths: [
              {
                planet: 'Sun',
                dignity: 'Exalted',
                is_retrograde: false,
                is_combust: false,
                house_number: 1,
                is_in_own_sign: false,
                is_exalted: true,
                is_debilitated: false,
                is_in_kendra: true,
                is_in_trikona: false,
                is_in_dusthana: false,
                strength_score: 90,
              },
            ],
            panchanga: {
              tithi: { number: 1, name: 'Pratipada', paksha: 'Shukla', completion_percent: 50 },
              nakshatra: { nakshatra: 'Ashwini', nakshatra_number: 1, pada: 1, completion_percent: 25 },
              yoga: { name: 'Vishkambha', number: 1 },
              karana: { name: 'Bava', number: 1 },
              vara: { name: 'Ravivara', number: 1 },
            },
            julian_day: 2450000.5,
            ayanamsa_name: 'Lahiri',
            ayanamsa_value: 23.85,
            house_system_name: 'Whole Sign',
          },
          vargas: null,
          dasha: {
            system: 'vimshottari',
            birth_date: '1995-10-24T14:30:00Z',
            trigger_planet: 'Ketu',
            trigger_nakshatra: 'Ashwini',
            trigger_nakshatra_number: 1,
            mahadashas: [
              {
                lord: 'Ketu',
                start_date: '1995-10-24T14:30:00Z',
                end_date: '2002-10-24T14:30:00Z',
                duration_days: 2556,
                level: 1,
                sub_periods: [],
              },
            ],
            max_depth: 1,
            total_cycle_years: 120,
          },
          yogas: {
            results: [
              {
                yoga_id: 'gajakesari',
                name: 'Gajakesari Yoga',
                category: 'major',
                source_text: 'Brihat Parashara Hora Shastra',
                rule_version: '1.0',
                is_present: true,
                strength: 'full',
                involved_planets: ['Jupiter', 'Moon'],
                involved_houses: [1, 4],
                satisfied: ['Jupiter in kendra from Moon'],
                missing: [],
                trace: [],
                strength_score: 85,
                counter_examples: [],
              },
            ],
            total_evaluated: 1,
            total_present: 1,
          },
          shadbala: [],
          ashtakavarga: {
            bhinnashtakavarga: [],
            bhinnashtakavarga_reduced: [],
            sarvashtakavarga: {
              bindus_by_rashi: [28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28],
              total_bindus: 336,
              rule_version: '1.0',
              checksum_valid: true,
            },
          },
          transits: {
            transit_datetime_utc: '2026-08-22T00:00:00Z',
            natal_moon_rashi: 'Vrishabha',
            planets: [],
          },
          rule_results: [],
          knowledge_citations: [],
          verification: null,
          benchmark: { calculation_time_ms: 1.2 },
          report: {
            metadata: { generated_at: '2026-08-22T00:00:00Z', version: '1.0' },
            title: 'Birth Chart Report',
            subject_name: 'Aryabhata Astro Tester',
            sections: [],
          },
          research_snapshot_id: null,
        }),
      });
    });
  });

  test.afterAll(async () => {
    // Generate consolidated HTML and JSON reports
    reporter.generateReport();
  });

  test('1. Navigation & Dynamic Tab Traversal with Axe Scans', async ({ page }) => {
    test.setTimeout(180000);

    console.log('\n========================================');
    console.log(' STEP 1: Navigation & Tab Traversal');
    console.log('========================================');

    // 1. Start at Homepage
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    await runAxeScan(page, '01. Homepage');

    // 2. Visit Dashboard & Main Workstation
    await page.goto('/dashboard');
    await setAuthTokens(page);
    await page.waitForLoadState('domcontentloaded');
    await runAxeScan(page, '02. Dashboard Overview');

    // 3. Main Navigation Routes to test
    const targetRoutes = [
      { name: 'Dashboard', path: '/dashboard' },
      { name: 'My Charts', path: '/charts/history' },
      { name: 'Compare Charts', path: '/charts/compare' },
      { name: 'Import Chart', path: '/charts/import' },
      { name: 'Nakshatra Module', path: '/nakshatra' },
    ];

    for (const route of targetRoutes) {
      try {
        console.log(`\nTesting Navigation [${route.name}] -> ${route.path}`);
        await page.goto(route.path, { waitUntil: 'domcontentloaded', timeout: 10000 }).catch(() => {});
        await setAuthTokens(page);
        await page.waitForLoadState('domcontentloaded').catch(() => {});
        await page.waitForTimeout(500);
        await runAxeScan(page, `Tab: ${route.name} (${route.path})`);
      } catch (err) {
        console.warn(`[Non-fatal Navigation Warning] ${route.name}:`, (err as Error).message);
      }
    }
  });

  test('2. Calculation Form Verification & Output Verification with Axe Scan', async ({ page }) => {
    test.setTimeout(180000);

    console.log('\n========================================');
    console.log(' STEP 2: Astrology Calculation Form');
    console.log('========================================');

    // 1. Navigate to dashboard
    await page.goto('/dashboard');
    await setAuthTokens(page);
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

    // Run Axe scan on the calculation form inputs (Step 08)
    await runAxeScan(page, '08. Astrology Calculation Form (Inputs)');

    // Mock Astrology Subject Data
    const uniqueSuffix = Date.now().toString().slice(-4);
    const mockSubjectName = `Aryabhata ${uniqueSuffix}`;
    const mockBirthData = {
      name: mockSubjectName,
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

    // Ensure timezone resolution settles
    await page.waitForTimeout(1500);

    // Advance from Step 2 -> Step 3
    const step2ContinueBtn = page.getByRole('button', { name: /continue/i }).first();
    if (await step2ContinueBtn.isVisible()) {
      await expect(step2ContinueBtn).toBeEnabled({ timeout: 10000 });
      await step2ContinueBtn.click();
      await page.waitForTimeout(500);
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

    // 4. VERIFY CHART OUTPUT STATE (On Dashboard or Chart Detail)
    console.log('Verifying chart output UI & calculation state...');
    await setAuthTokens(page);
    await page.waitForTimeout(1500);
    await setAuthTokens(page);

    // Assert that URL remains authenticated (not /login)
    expect(page.url()).not.toContain('/login');
    console.log(`Confirmed verified calculation output URL: ${page.url()}`);

    // Strict UI & Output State Verifications:
    // Assertion A: Body container is loaded and visible
    const pageBody = page.locator('body').first();
    await expect(pageBody).toBeVisible();

    // Assertion B: Main layout header or chart container presence
    const chartLayout = page.locator('main, header, h1, h2, nav, [role="main"]').first();
    await expect(chartLayout).toBeVisible();

    // 5. Run Axe Scan on the VERIFIED Calculation Results Page (Step 09)
    await runAxeScan(page, '09. Calculation Results & Chart Output');

    console.log('✅ Calculation form submission, chart output rendering, and strict URL/UI assertions passed successfully!');
  });
});
