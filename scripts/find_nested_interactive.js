const { chromium } = require('playwright');
const AxeBuilder = require('@axe-core/playwright').default;
const fs = require('fs');
const path = require('path');

const routesManifest = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../apps/web/.next/routes-manifest.json'), 'utf8'));
const staticRoutes = routesManifest.staticRoutes.map(r => r.page).filter(p => !p.includes('_not-found'));

async function scanAllRoutes() {
  console.log(`Scanning ${staticRoutes.length} static routes for accessibility rules (including nested-interactive)...`);
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();

  const nestedInteractiveIssues = [];
  const allViolations = [];

  for (let i = 0; i < staticRoutes.length; i++) {
    const route = staticRoutes[i];
    const url = `http://localhost:3000${route}`;
    process.stdout.write(`[${i + 1}/${staticRoutes.length}] ${route} ... `);

    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
      await page.waitForTimeout(500);

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      const nested = results.violations.filter(v => v.id === 'nested-interactive');
      if (nested.length > 0) {
        console.log(`❌ FOUND nested-interactive: ${nested[0].nodes.length} instance(s)`);
        nestedInteractiveIssues.push({ route, nodes: nested[0].nodes });
      } else if (results.violations.length > 0) {
        console.log(`⚠️ ${results.violations.length} violation(s): ${results.violations.map(v => v.id).join(', ')}`);
        allViolations.push({ route, violations: results.violations });
      } else {
        console.log(`✅ Clean`);
      }
    } catch (err) {
      console.log(`Error: ${err.message}`);
    }
  }

  await browser.close();

  console.log('\n--- SCAN FINISHED ---');
  console.log('Nested Interactive Issues found:', JSON.stringify(nestedInteractiveIssues, null, 2));
}

scanAllRoutes().catch(console.error);
