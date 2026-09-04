const { chromium } = require('playwright');
const AxeBuilder = require('@axe-core/playwright').default;

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const ROUTES = ['/', '/register', '/dashboard'];

async function runAudit() {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('🔍 Running Accessibility Audit...\n');
  let totalViolations = 0;

  for (const route of ROUTES) {
    const url = `${BASE_URL}${route}`;
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForLoadState('networkidle');
      
      const axeResults = await new AxeBuilder({ page })
        .exclude('nextjs-portal')
        .analyze();

      const violations = axeResults.violations;
      totalViolations += violations.length;

      if (violations.length === 0) {
        console.log(`? Route ${route}: 0 Violations`);
      } else {
        console.log(`?? Route ${route}: ${violations.length} Violations`);
        violations.forEach((v) => {
          console.log(`  - [${v.impact}] ${v.id}: ${v.help}`);
        });
      }
    } catch (err) {
      console.log(`? Failed to load ${route}: ${err.message}`);
    }
  }

  await browser.close();
  console.log(`\n?? Audit Completed. Total Core Violations: ${totalViolations}`);
}

runAudit();
