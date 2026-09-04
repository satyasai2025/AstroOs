import { chromium } from 'playwright';
import { execSync } from 'child_process';
import path from 'path';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const ARTIFACT_DIR = 'C:/Users/rkmau/.gemini/antigravity/brain/0f76b406-e98c-48d1-84c2-076aee1e3938';

function getRealAuthToken() {
  const output = execSync(
    `.venv\\Scripts\\python.exe -c "from apps.api.security.jwt import create_access_token; tok, _ = create_access_token('bc50cc61-9ade-49af-b301-89a66465367e', 'researcher'); print(tok.strip())"`
  );
  return output.toString().trim();
}

async function run() {
  const token = getRealAuthToken();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  await page.addInitScript((tok) => {
    window.localStorage.setItem("astro_access_token", tok);
    window.localStorage.setItem("astro_refresh_token", tok);
  }, token);

  try {
    console.log('Navigating to /charts...');
    await page.goto(`${BASE_URL}/charts`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    // Look for Select Chart button
    const selectChartBtn = page.getByRole('button', { name: /Select Chart/i });
    if (await selectChartBtn.isVisible()) {
      await selectChartBtn.click();
      await page.waitForTimeout(1000);
      // Click first chart in modal if present
      const firstChart = page.locator('[role="dialog"] button, [role="dialog"] [role="button"], .cursor-pointer').first();
      if (await firstChart.isVisible()) {
        await firstChart.click();
        await page.waitForTimeout(2000);
      }
    }

    // Now go to Yogas tab
    console.log('Navigating to Yogas view...');
    await page.goto(`${BASE_URL}/charts?view=yogas`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(4000);
    const yogasScreenshot = path.join(ARTIFACT_DIR, 'yogas_view_loaded.png');
    await page.screenshot({ path: yogasScreenshot, fullPage: false });
    console.log(`Saved screenshot: ${yogasScreenshot}`);

    // Now go to Divisional view
    console.log('Navigating to Divisional view...');
    await page.goto(`${BASE_URL}/charts?view=divisional`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(4000);
    const divisionalScreenshot = path.join(ARTIFACT_DIR, 'divisional_view_loaded.png');
    await page.screenshot({ path: divisionalScreenshot, fullPage: false });
    console.log(`Saved screenshot: ${divisionalScreenshot}`);

    console.log('✅ Full chart screenshots captured successfully!');
  } catch (err) {
    console.error('Error capturing screenshots:', err);
  } finally {
    await browser.close();
  }
}

run();
