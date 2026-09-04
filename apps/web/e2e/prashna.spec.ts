import { test, expect } from '@playwright/test';

test.describe('AstroOS Prashna / Horary Analysis End-to-End Pipeline', () => {
  const goldenResponse = {
    canonical_inputs: {
      question: 'Will I get this job?',
      moment_utc: '2026-08-22T06:52:00.000Z',
      latitude: 18.5204,
      longitude: 73.8567,
      place_name: 'Pune, Maharashtra, India',
      ayanamsa: 'lahiri',
    },
    astronomical_facts: {
      ascendant: {
        sign: 'Libra',
        longitude: 209.1406,
        degree_str: "29° 08' 26\"",
        sign_lord: 'Venus',
        star_lord: 'Jupiter',
        sub_lord: 'Sun',
        sub_sub_lord: 'Saturn',
      },
      moon: {
        sign: 'Scorpio',
        longitude: 238.7873,
        degree_str: "28° 47' 14\"",
        sign_lord: 'Mars',
        star_lord: 'Mercury',
        sub_lord: 'Saturn',
        sub_sub_lord: 'Venus',
      },
      vara_lord: 'Saturn',
      hora_lord: 'Jupiter',
    },
    planets: [
      {
        planet: 'Sun',
        sign: 'Leo',
        degree_str: "05° 25' 12\"",
        degree_float: 5.42,
        nakshatra: 'Magha',
        pada: 2,
        sign_lord: 'Sun',
        star_lord: 'Ketu',
        sub_lord: 'Saturn',
        sub_sub_lord: 'Mercury',
        house_number: 11,
      },
      {
        planet: 'Moon',
        sign: 'Scorpio',
        degree_str: "28° 47' 14\"",
        degree_float: 28.7873,
        nakshatra: 'Jyeshtha',
        pada: 4,
        sign_lord: 'Mars',
        star_lord: 'Mercury',
        sub_lord: 'Saturn',
        sub_sub_lord: 'Venus',
        house_number: 2,
      },
      {
        planet: 'Mars',
        sign: 'Gemini',
        degree_str: "18° 12' 40\"",
        degree_float: 18.21,
        nakshatra: 'Ardra',
        pada: 4,
        sign_lord: 'Mercury',
        star_lord: 'Rahu',
        sub_lord: 'Moon',
        sub_sub_lord: 'Sun',
        house_number: 9,
      },
      {
        planet: 'Mercury',
        sign: 'Leo',
        degree_str: "22° 15' 00\"",
        degree_float: 22.25,
        nakshatra: 'Purva Phalguni',
        pada: 3,
        sign_lord: 'Sun',
        star_lord: 'Venus',
        sub_lord: 'Saturn',
        sub_sub_lord: 'Jupiter',
        house_number: 11,
      },
      {
        planet: 'Jupiter',
        sign: 'Cancer',
        degree_str: "19° 40' 11\"",
        degree_float: 19.67,
        nakshatra: 'Ashlesha',
        pada: 1,
        sign_lord: 'Moon',
        star_lord: 'Mercury',
        sub_lord: 'Venus',
        sub_sub_lord: 'Moon',
        house_number: 10,
      },
      {
        planet: 'Venus',
        sign: 'Virgo',
        degree_str: "12° 05' 33\"",
        degree_float: 12.09,
        nakshatra: 'Hasta',
        pada: 1,
        sign_lord: 'Mercury',
        star_lord: 'Moon',
        sub_lord: 'Rahu',
        sub_sub_lord: 'Mars',
        house_number: 12,
      },
      {
        planet: 'Saturn',
        sign: 'Pisces',
        degree_str: "06° 45' 18\"",
        degree_float: 6.755,
        nakshatra: 'Uttara Bhadrapada',
        pada: 2,
        sign_lord: 'Jupiter',
        star_lord: 'Saturn',
        sub_lord: 'Mercury',
        sub_sub_lord: 'Sun',
        house_number: 6,
      },
      {
        planet: 'Rahu',
        sign: 'Aquarius',
        degree_str: "14° 30' 00\"",
        degree_float: 14.5,
        nakshatra: 'Shatabhisha',
        pada: 3,
        sign_lord: 'Saturn',
        star_lord: 'Rahu',
        sub_lord: 'Jupiter',
        sub_sub_lord: 'Saturn',
        house_number: 5,
      },
      {
        planet: 'Ketu',
        sign: 'Leo',
        degree_str: "14° 30' 00\"",
        degree_float: 14.5,
        nakshatra: 'Purva Phalguni',
        pada: 1,
        sign_lord: 'Sun',
        star_lord: 'Venus',
        sub_lord: 'Venus',
        sub_sub_lord: 'Rahu',
        house_number: 11,
      },
    ],
    cusps: [
      {
        house: 1,
        sign: 'Libra',
        degree_str: "29° 08' 26\"",
        degree_float: 209.14,
        nakshatra: 'Vishakha',
        pada: 3,
        sign_lord: 'Venus',
        star_lord: 'Jupiter',
        sub_lord: 'Sun',
        sub_sub_lord: 'Saturn',
      },
      {
        house: 2,
        sign: 'Scorpio',
        degree_str: "28° 22' 30\"",
        degree_float: 238.375,
        nakshatra: 'Jyeshtha',
        pada: 4,
        sign_lord: 'Mars',
        star_lord: 'Mercury',
        sub_lord: 'Saturn',
        sub_sub_lord: 'Mercury',
      },
      {
        house: 10,
        sign: 'Leo',
        degree_str: "00° 57' 15\"",
        degree_float: 120.954,
        nakshatra: 'Magha',
        pada: 1,
        sign_lord: 'Sun',
        star_lord: 'Ketu',
        sub_lord: 'Venus',
        sub_sub_lord: 'Venus',
      },
      {
        house: 11,
        sign: 'Virgo',
        degree_str: "03° 07' 47\"",
        degree_float: 153.13,
        nakshatra: 'Uttara Phalguni',
        pada: 2,
        sign_lord: 'Mercury',
        star_lord: 'Sun',
        sub_lord: 'Saturn',
        sub_sub_lord: 'Rahu',
      },
    ],
    ruling_planets_ct: {
      day_lord: 'Saturn',
      hora_lord: 'Jupiter',
      entries: [
        {
          point_name: 'Ascendant (Lagna)',
          sign_lord: 'Venus',
          star_lord: 'Jupiter',
          sub_lord: 'Sun',
          sub_sub_lord: 'Saturn',
        },
        {
          point_name: 'Moon (Chandra)',
          sign_lord: 'Mars',
          star_lord: 'Mercury',
          sub_lord: 'Saturn',
          sub_sub_lord: 'Venus',
        },
        {
          point_name: 'Day Lord (Vara)',
          sign_lord: 'Saturn',
          star_lord: '—',
          sub_lord: '—',
          sub_sub_lord: '—',
        },
        {
          point_name: 'Hora Lord',
          sign_lord: 'Jupiter',
          star_lord: '—',
          sub_lord: '—',
          sub_sub_lord: '—',
        },
      ],
    },
    judgement: {
      verdict: 'YES',
      confidence_percentage: 91,
      primary_indication: 'Affirmative Indication for Job Selection',
      summary:
        'Canonical KP Prashna analysis indicates strong promise for job selection. 10th Cuspal Sub-Lord Venus connects with fruitful houses (11, 2, 6) and Hora Lord Jupiter reinforces positive outcome.',
      key_evidences: [
        {
          factor: '10th Cuspal Sub-Lord',
          indication: 'Very Positive',
          explanation: '10th CSL signifies 11th and 2nd houses, promising success.',
          weight: 45,
        },
        {
          factor: 'Ruling Planets & Hora',
          indication: 'Positive',
          explanation: 'Hora Lord Jupiter in 10th house is a prime significator.',
          weight: 35,
        },
        {
          factor: 'Moon Strength',
          indication: 'Positive',
          explanation: 'Moon in 2nd house of accumulated gains.',
          weight: 15,
        },
      ],
      relevant_houses: [
        {
          house: 10,
          sign: 'Leo',
          lord: 'Sun',
          strength: 'Strong',
          note: 'Primary career bhava with benefic aspects.',
        },
        {
          house: 11,
          sign: 'Virgo',
          lord: 'Mercury',
          strength: 'Strong',
          note: 'Fulfilment of desires and career gains.',
        },
      ],
      supporting_rules: [
        {
          rule_id: 'PRASNA-CSL-10',
          rule_principle: '10th Cuspal Sub-Lord signifies 2, 6, 10 or 11 for career fruition',
          reference: 'K.P. Reader Vol IV',
          triggered: 'Yes',
          weight: 45,
        },
        {
          rule_id: 'PRASNA-RP-HORA',
          rule_principle: 'Hora Lord concordant with primary question significators',
          reference: 'Classical Horary Confluence',
          triggered: 'Yes',
          weight: 35,
        },
        {
          rule_id: 'PRASNA-MOON-FAV',
          rule_principle: 'Moon occupies favorable bhava without malefic combustion',
          reference: 'Prashna Marga',
          triggered: 'Yes',
          weight: 15,
        },
      ],
      timing: {
        likely_window: 'Sep 2026 – Nov 2026',
        dasha_mahadasha: 'Mercury Mahadasha',
        antardasha: 'Saturn Antardasha',
        transit_support: 'Jupiter in Cancer aspecting key houses',
        moon_cycle: 'Shukla Paksha (Waxing)',
      },
      conclusions: [
        'Candidate has strong astrological indication for job acquisition.',
        'Offer letter and confirmation most likely between September and November 2026.',
      ],
    },
  };

  test('should load /charts/prashna and execute complete Golden Case pipeline', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Stub /auth/me on any host
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'e2e-test-user',
          email: 'test@astroos.org',
          username: 'e2e_tester',
          role: 'researcher',
        }),
      });
    });

    // Stub /auth/refresh so token refresh never fails / redirects to /login
    await page.route('**/api/v1/auth/refresh', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'e2e-test-token',
          refresh_token: 'e2e-refresh-token',
        }),
      });
    });

    // Stub the Prashna calculation endpoint with the golden response
    await page.route('**/api/v1/prashna/calculate', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(goldenResponse),
      });
    });

    // Catch-all for any other unmocked background api endpoints to prevent 401s
    await page.route('**/api/v1/**', async (route) => {
      if (route.request().url().includes('/prashna/calculate') ||
          route.request().url().includes('/auth/me') ||
          route.request().url().includes('/auth/refresh')) {
        await route.fallback();
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({}),
        });
      }
    });

    // Step 1 – Visit the public login page
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Step 2 – Write auth tokens into localStorage from the correct origin context
    await page.evaluate(() => {
      window.localStorage.setItem('astro_access_token', 'e2e-test-token');
      window.localStorage.setItem('astro_refresh_token', 'e2e-refresh-token');
    });

    // Step 3 – Navigate to the protected Prashna route
    await page.goto('/charts/prashna');

    // Step 4 – Wait for the Prashna entry form to appear
    await page.waitForSelector('#prashna-question', { timeout: 30000 });

    // 1. Fill Golden Case inputs
    await page.locator('#prashna-question').fill('Will I get this job?');
    await page.locator('#prashna-date').fill('2026-08-22');
    await page.locator('#prashna-time').fill('12:22:00');
    await page.locator('#prashna-place').fill('Pune, Maharashtra, India');

    // 2. Submit Calculation
    const submitBtn = page.getByRole('button', { name: /Cast Prashna Chart & Reveal Verdict/i });
    await expect(submitBtn).toBeVisible();
    await submitBtn.click();

    // 3. Verify Overview Tab renders Canonical Facts
    await expect(page.locator('text=Will I get this job?').first()).toBeVisible();
    await expect(page.locator('text=Libra').first()).toBeVisible();
    await expect(page.locator('text=Scorpio').first()).toBeVisible();
    await expect(page.locator('text=Favorable').first()).toBeVisible();
    await expect(page.locator('text=91% Confidence').first()).toBeVisible();

    // 4. Verify all 7 tabs are interactable and render properly
    // Chart Tab
    await page.getByRole('button', { name: 'Chart', exact: true }).click();
    await expect(page.locator('text=Horary D1').first()).toBeVisible();

    // Significators Tab
    await page.getByRole('button', { name: 'Significators', exact: true }).click();
    await expect(page.locator('text=KP 4-Fold Planetary Significators Table')).toBeVisible();
    await expect(page.locator('text=Jyeshtha (P4)')).toBeVisible();

    // Houses Tab
    await page.getByRole('button', { name: 'Houses', exact: true }).click();
    await expect(page.locator('text=12 Cuspal Sub-Lords (CSL) & House Alignment')).toBeVisible();
    await expect(page.getByRole('cell', { name: 'House 1', exact: true })).toBeVisible();

    // Ruling & Moon Tab
    await page.getByRole('button', { name: '👑 Ruling & Moon', exact: true }).click();
    await expect(page.locator('text=5-Fold Krishnamurti Ruling Planets (RP) Hierarchy')).toBeVisible();
    await expect(page.locator('text=Vara Lord (Day Lord)')).toBeVisible();

    // Timing & Timeline Tab
    await page.getByRole('button', { name: '⏳ Timing & Timeline', exact: true }).click();
    await expect(page.locator('text=Fructification Timeline & Transit Milestone Tracker')).toBeVisible();
    await expect(page.locator('text=Sep 2026 – Nov 2026').first()).toBeVisible();

    // AI Astrologer Tab
    await page.getByRole('button', { name: '✨ AI Astrologer', exact: true }).click();
    await expect(page.locator('text=AI Astrologer Deep Interpretation')).toBeVisible();
    await expect(page.locator('text=Candidate has strong astrological indication').first()).toBeVisible();

    // 5. Assert zero unexpected runtime console errors
    const fatalErrors = consoleErrors.filter(
      (e) => !e.includes('Hydration') && !e.includes('favicon')
    );
    expect(fatalErrors).toHaveLength(0);
  });
});
