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
  console.log('📸 Capturing live screenshots of Yogas, SBC, and Classical Rule Evidence...');
  const token = getRealAuthToken();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  await page.addInitScript((tok) => {
    window.localStorage.setItem("astro_access_token", tok);
    window.localStorage.setItem("astro_refresh_token", tok);
  }, token);

  try {
    // 1. Screenshot /charts?view=yogas
    console.log('Navigating to /charts?view=yogas...');
    await page.goto(`${BASE_URL}/charts?view=yogas`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    const yogasScreenshot = path.join(ARTIFACT_DIR, 'yogas_view_verified.png');
    await page.screenshot({ path: yogasScreenshot, fullPage: false });
    console.log(`Saved screenshot: ${yogasScreenshot}`);

    // 2. Screenshot /charts/sbc
    console.log('Navigating to /charts/sbc...');
    await page.goto(`${BASE_URL}/charts/sbc`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    const sbcScreenshot = path.join(ARTIFACT_DIR, 'sbc_view_verified.png');
    await page.screenshot({ path: sbcScreenshot, fullPage: false });
    console.log(`Saved screenshot: ${sbcScreenshot}`);

    // 3. Screenshot /knowledge
    console.log('Navigating to /knowledge...');
    await page.goto(`${BASE_URL}/knowledge`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    const ruleScreenshot = path.join(ARTIFACT_DIR, 'classical_rule_evidence_verified.png');
    await page.screenshot({ path: ruleScreenshot, fullPage: false });
    console.log(`Saved screenshot: ${ruleScreenshot}`);

    // 4. Screenshot /charts?view=divisional
    console.log('Navigating to /charts?view=divisional...');
    await page.goto(`${BASE_URL}/charts?view=divisional`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    const divisionalScreenshot = path.join(ARTIFACT_DIR, 'divisional_view_verified.png');
    await page.screenshot({ path: divisionalScreenshot, fullPage: false });
    console.log(`Saved screenshot: ${divisionalScreenshot}`);

    console.log('✅ All screenshots captured successfully!');
  } catch (err) {
    console.error('Error capturing screenshots:', err);
  } finally {
    await browser.close();
  }
}

run();
