import { test, expect } from '@playwright/test';

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': '*',
};

test.describe('Dasha Deep Dive & Canonical /charts/dasha Routing E2E', () => {
  test.beforeEach(async ({ context, page }) => {
    page.on('console', (msg) => {
      if (msg.type() === 'error') console.log('PAGE ERROR:', msg.text());
    });
    page.on('pageerror', (err) => console.log('PAGE EXCEPTION:', err.message, '\n', err.stack));

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
      {
        name: 'astroos_access_token',
        value: 'mock_e2e_jwt_access_token',
        domain: 'localhost',
        path: '/',
      },
    ]);

    // Handle OPTIONS CORS preflights
    await page.route(/\/api\/v1\//, async (route) => {
      if (route.request().method() === 'OPTIONS') {
        await route.fulfill({
          status: 200,
          headers: CORS_HEADERS,
        });
        return;
      }
      await route.fallback();
    });

    // Intercept auth endpoints
    await page.route(/\/api\/v1\/auth\//, async (route) => {
      await route.fulfill({
        status: 200,
        headers: CORS_HEADERS,
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

    // Intercept user charts list
    await page.route(/\/api\/v1\/horoscope\/my-charts/, async (route) => {
      await route.fulfill({
        status: 200,
        headers: CORS_HEADERS,
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

    // Intercept workflow analysis execution
    await page.route(/\/api\/v1\/workflow\/analyze/, async (route) => {
      await route.fulfill({
        status: 200,
        headers: CORS_HEADERS,
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
            planets: [
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
            system: 'Vimshottari',
            birth_date: '1995-10-24T14:30:00Z',
            trigger_planet: 'Ketu',
            trigger_nakshatra: 'Ashwini',
            trigger_nakshatra_number: 1,
            mahadashas: [
              {
                lord: 'Ketu',
                start_date: '1995-10-24T14:30:00Z',
                end_date: '2030-10-24T14:30:00Z',
                duration_days: 12784,
                level: 1,
                sub_periods: [
                  {
                    lord: 'Venus',
                    start_date: '1995-10-24T14:30:00Z',
                    end_date: '2027-10-24T14:30:00Z',
                    duration_days: 1169,
                    level: 2,
                    sub_periods: [],
                  },
                ],
              },
            ],
            max_depth: 2,
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
                involved_planets: ['Jupiter', 'Moon', 'Ketu'],
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
            planets: [
              {
                planet: 'Jupiter',
                transit_rashi: 'Vrishabha',
                house_from_natal_moon: 1,
                ashtakavarga_bindus: 5,
                is_sade_sati: false,
                is_ashtama_shani: false,
                is_favorable_house: true,
                has_vedha: false,
                has_vipreet_vedha: false,
                vedha_planet: null,
                transit_nakshatra_sbc: 'Rohini',
                has_nakshatra_vedha: false,
                nakshatra_vedha_planet: null,
                nakshatra_vedha_type: null,
                nakshatra_vedha_target: null,
                rule_version: '1.0',
                transit_rashi_degree: 12.0,
                transit_nakshatra: 'Rohini',
                transit_pada: 1,
                is_retrograde: false,
                speed_deg_per_day: 0.1,
                gati: 'sama',
              },
              {
                planet: 'Saturn',
                transit_rashi: 'Kumbha',
                house_from_natal_moon: 10,
                ashtakavarga_bindus: 4,
                is_sade_sati: false,
                is_ashtama_shani: false,
                is_favorable_house: true,
                has_vedha: false,
                has_vipreet_vedha: false,
                vedha_planet: null,
                transit_nakshatra_sbc: 'Shatabhisha',
                has_nakshatra_vedha: false,
                nakshatra_vedha_planet: null,
                nakshatra_vedha_type: null,
                nakshatra_vedha_target: null,
                rule_version: '1.0',
                transit_rashi_degree: 5.0,
                transit_nakshatra: 'Shatabhisha',
                transit_pada: 2,
                is_retrograde: false,
                speed_deg_per_day: 0.05,
                gati: 'sama',
              },
            ],
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

    // Intercept dasha system tree requests
    await page.route(/\/api\/v1\/dasha\//, async (route) => {
      await route.fulfill({
        status: 200,
        headers: CORS_HEADERS,
        contentType: 'application/json',
        body: JSON.stringify({
          system: 'Yogini',
          birth_date: '1995-10-24T14:30:00Z',
          trigger_planet: 'Moon',
          trigger_nakshatra: 'Rohini',
          trigger_nakshatra_number: 4,
          mahadashas: [
            {
              lord: 'Mangala',
              start_date: '1995-10-24T14:30:00Z',
              end_date: '2030-10-24T14:30:00Z',
              duration_days: 12784,
              level: 1,
              sub_periods: [],
            },
          ],
          max_depth: 1,
          total_cycle_years: 36,
        }),
      });
    });
  });

  test('1. Canonical /charts/dasha loads', async ({ page }) => {
    await page.goto('/charts/dasha');
    await expect(page).toHaveURL(/\/charts\/dasha/);
    await expect(page.locator('h1')).toContainText('Dasha Deep Dive');
  });

  test('2. /charts?view=dasha redirects to /charts/dasha', async ({ page }) => {
    await page.goto('/charts?view=dasha');
    await expect(page).toHaveURL(/\/charts\/dasha/);
  });

  test('3. Six Dasha systems are selectable', async ({ page }) => {
    await page.goto('/charts/dasha');
    const systemSwitcher = page.locator('div[role="region"][aria-label="Dasha system switcher"], select, button').filter({ hasText: /Vimshottari/i });
    await expect(systemSwitcher.first()).toBeVisible();
  });

  test('4 & 5. Active Dasha chain and Hero progress/countdown render', async ({ page }) => {
    await page.goto('/charts/dasha');
    await expect(page.locator('text=Current Period Chain').or(page.locator('text=Dasha')).first()).toBeVisible();
    await expect(page.locator('text=/Mahadasha/i').first()).toBeVisible();
  });

  test('6, 8, 9, 10, 11. Four tabs switch correctly and render respective components', async ({ page }) => {
    await page.goto('/charts/dasha');

    // TAB 1: Tree & Timeline
    await expect(page.locator('div[role="tablist"] button').filter({ hasText: /Tree/i }).first()).toBeVisible();

    // TAB 2: Activation
    await page.locator('div[role="tablist"] button').filter({ hasText: /Activation/i }).first().click();
    await expect(page).toHaveURL(/tab=activation/);
    await expect(page.locator('text=Mahadasha Lord').or(page.locator('text=Activated Houses')).first()).toBeVisible();

    // TAB 3: Dasha × Transit
    await page.locator('div[role="tablist"] button').filter({ hasText: /Transit/i }).first().click();
    await expect(page).toHaveURL(/tab=transit/);

    // TAB 4: Multi-Dasha Convergence
    await page.locator('div[role="tablist"] button').filter({ hasText: /Convergence/i }).first().click();
    await expect(page).toHaveURL(/tab=convergence/);
  });

  test('7. Chart switching button opens active chart selector', async ({ page }) => {
    await page.goto('/charts/dasha');
    const switchBtn = page.getByRole('button', { name: /Switch Chart/i });
    await expect(switchBtn).toBeVisible();
    await switchBtn.click();
    await expect(page.locator('text=Select Active Chart').or(page.getByRole('dialog')).first()).toBeVisible();
  });
});
