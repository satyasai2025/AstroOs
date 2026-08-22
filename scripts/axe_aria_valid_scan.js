const { chromium } = require('playwright');
const AxeBuilder = require('@axe-core/playwright').default;

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  const urls = [
    'http://localhost:3000/login',
    'http://localhost:3000/register',
    'http://localhost:3000/forgot-password',
    'http://localhost:3000/reset-password',
  ];

  for (const url of urls) {
    try {
      await page.goto(url, { waitUntil: 'load', timeout: 15000 });
      await page.waitForTimeout(1500);
      const results = await new AxeBuilder({ page })
        .withRules(['aria-valid-attr-value'])
        .analyze();

      if (results.violations.length > 0) {
        console.log(`\n❌ ${url}:`);
        for (const v of results.violations) {
          console.log(`  Rule: ${v.id} (${v.impact})`);
          console.log(`  Help: ${v.help}`);
          for (const node of v.nodes) {
            console.log(`  Element: ${node.html}`);
            console.log(`  Target:  ${JSON.stringify(node.target)}`);
            console.log(`  Message: ${node.any.map(c => c.message).join('; ')}`);
            console.log(`  ---`);
          }
        }
      } else {
        console.log(`✅ ${url}: 0 aria-valid-attr-value issues`);
      }
    } catch (e) {
      console.log(`⚠️ ${url}: ${e.message}`);
    }
  }

  await browser.close();
})();
