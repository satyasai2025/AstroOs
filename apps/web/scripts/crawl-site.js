/**
 * AstroOS — Playwright Site Crawler & Route Health Checker
 *
 * Crawls all primary application routes in both Light and Dark modes,
 * monitors console errors and failed HTTP API requests, and captures
 * full-page audit screenshots.
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('@playwright/test');

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const OUTPUT_DIR = path.join(__dirname, '..', 'crawler-reports');

const ROUTES = [
  '/dashboard',
  '/charts',
  '/charts/birth',
  '/charts/transit',
  '/charts/compare',
  '/ai/explain',
  '/charts/kp',
  '/settings',
];

const THEMES = ['light', 'dark'];

async function runCrawler() {
  console.log('====================================================');
  console.log('🚀 Starting AstroOS Playwright Site Health Crawler');
  console.log(`🌐 Base URL: ${BASE_URL}`);
  console.log(`📁 Reports Output: ${OUTPUT_DIR}`);
  console.log('====================================================\n');

  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  let browser;
  try {
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
  } catch (err) {
    console.error('❌ Failed to launch Chromium browser with Playwright.');
    console.error('If browsers are not yet installed, run: npx playwright install chromium\n');
    console.error(err.message);
    process.exit(1);
  }

  const results = [];
  let totalErrors = 0;
  let totalFailedRequests = 0;

  for (const theme of THEMES) {
    console.log(`\n🎨 Testing Theme: ${theme.toUpperCase()} MODE`);
    console.log('----------------------------------------------------');

    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      colorScheme: theme,
      deviceScaleFactor: 1,
    });

    for (const route of ROUTES) {
      const page = await context.newPage();
      const pageErrors = [];
      const consoleErrors = [];
      const failedRequests = [];
      const startTime = Date.now();

      // Listen for unhandled page runtime errors
      page.on('pageerror', (err) => {
        pageErrors.push(err.message || String(err));
      });

      // Listen for browser console errors
      page.on('console', (msg) => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });

      // Listen for HTTP response status codes (flag 400, 404, 500, etc.)
      page.on('response', (response) => {
        const status = response.status();
        const url = response.url();
        if (status >= 400) {
          failedRequests.push({ url, status, statusText: response.statusText() });
        }
      });

      const cleanRouteName = route === '/' ? 'home' : route.replace(/^\//, '').replace(/\//g, '_');
      const screenshotFilename = `${cleanRouteName}_${theme}.png`;
      const screenshotPath = path.join(OUTPUT_DIR, screenshotFilename);

      let httpStatus = 200;
      let loadSuccess = true;
      let errorMessage = null;

      try {
        const response = await page.goto(`${BASE_URL}${route}`, {
          waitUntil: 'networkidle',
          timeout: 25000,
        });

        if (response) {
          httpStatus = response.status();
          if (httpStatus >= 400) {
            loadSuccess = false;
          }
        }

        // Apply theme class and localStorage setting
        await page.evaluate((currentTheme) => {
          if (currentTheme === 'dark') {
            document.documentElement.classList.add('dark');
            document.documentElement.setAttribute('data-theme', 'dark');
            try {
              localStorage.setItem('theme', 'dark');
            } catch (e) {}
          } else {
            document.documentElement.classList.remove('dark');
            document.documentElement.setAttribute('data-theme', 'light');
            try {
              localStorage.setItem('theme', 'light');
            } catch (e) {}
          }
        }, theme);

        // Allow UI animations to settle
        await page.waitForTimeout(600);

        // Take full-page screenshot
        await page.screenshot({
          path: screenshotPath,
          fullPage: true,
        });
      } catch (err) {
        loadSuccess = false;
        errorMessage = err.message;
        pageErrors.push(err.message);
      }

      const durationMs = Date.now() - startTime;
      const hasErrors = pageErrors.length > 0 || consoleErrors.length > 0 || failedRequests.length > 0 || !loadSuccess;

      if (hasErrors) {
        totalErrors += pageErrors.length + consoleErrors.length;
        totalFailedRequests += failedRequests.length;
      }

      const result = {
        route,
        theme,
        httpStatus,
        durationMs,
        loadSuccess,
        pageErrors,
        consoleErrors,
        failedRequests,
        screenshot: screenshotFilename,
        errorMessage,
      };

      results.push(result);

      const statusIcon = hasErrors ? '⚠️' : '✅';
      console.log(
        `${statusIcon} [${theme.toUpperCase()}] ${route.padEnd(20)} | Status: ${httpStatus} | ${durationMs}ms | Console Errs: ${consoleErrors.length + pageErrors.length} | Failed HTTP: ${failedRequests.length}`
      );

      if (hasErrors) {
        if (pageErrors.length > 0) {
          console.log(`   🚨 Page Errors: ${pageErrors.join('; ')}`);
        }
        if (consoleErrors.length > 0) {
          console.log(`   ⚠️  Console Errors: ${consoleErrors.slice(0, 3).join('; ')}`);
        }
        if (failedRequests.length > 0) {
          console.log(`   ❌ Failed Requests: ${failedRequests.map((r) => `${r.status} ${r.url}`).slice(0, 3).join('; ')}`);
        }
      }

      await page.close();
    }

    await context.close();
  }

  await browser.close();

  // Save audit summary JSON
  const summaryPath = path.join(OUTPUT_DIR, 'audit-summary.json');
  const summaryData = {
    timestamp: new Date().toISOString(),
    baseUrl: BASE_URL,
    totalRoutesChecked: ROUTES.length * THEMES.length,
    totalErrors,
    totalFailedRequests,
    results,
  };

  fs.writeFileSync(summaryPath, JSON.stringify(summaryData, null, 2), 'utf-8');

  console.log('\n====================================================');
  console.log('📊 Audit Summary Report');
  console.log('====================================================');
  console.log(`Total Checks: ${results.length} (${ROUTES.length} routes × ${THEMES.length} themes)`);
  console.log(`Total Console/Runtime Errors: ${totalErrors}`);
  console.log(`Total Failed API/HTTP Requests: ${totalFailedRequests}`);
  console.log(`Full Audit Report JSON: ${summaryPath}`);
  console.log(`Screenshots Directory: ${OUTPUT_DIR}`);
  console.log('====================================================\n');
}

runCrawler().catch((err) => {
  console.error('Fatal crawler error:', err);
  process.exit(1);
});
