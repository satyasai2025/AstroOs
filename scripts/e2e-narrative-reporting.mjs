/**
 * AstroOS — Full Narrative & Comparative Reporting Real Browser E2E Test
 *
 * Runs against live FastAPI backend (http://127.0.0.1:8000) and Next.js (http://localhost:3000).
 */

import { chromium } from "playwright";
import { execSync } from "child_process";

function getRealAuthToken() {
  const output = execSync(
    `.venv\\Scripts\\python.exe -c "from apps.api.security.jwt import create_access_token; tok, _ = create_access_token('bc50cc61-9ade-49af-b301-89a66465367e', 'researcher'); print(tok.strip())"`
  );
  return output.toString().trim();
}

async function runE2E() {
  console.log("🚀 Starting Full Narrative & Comparative Reporting Real Browser E2E Verification...\n");

  const token = getRealAuthToken();
  console.log("🔑 Authenticated Live Researcher Token Obtained.");

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      console.log(`[Browser Console Error]:`, msg.text());
    }
  });
  page.on("pageerror", (err) => console.error("[Browser Page Error]:", err.message));

  // Initialize authenticated session in localStorage
  await page.addInitScript((tok) => {
    window.localStorage.setItem("astro_access_token", tok);
    window.localStorage.setItem("astro_refresh_token", tok);
  }, token);

  try {
    // ══════════════════════════════════════════════════════════════════════════
    // PART 1: FULL 9-SECTION STRUCTURED NARRATIVE REPORT (/reports/full)
    // ══════════════════════════════════════════════════════════════════════════
    console.log("📍 Step 1: Navigating to http://localhost:3000/reports/full ...");
    await page.goto("http://localhost:3000/reports/full", { waitUntil: "networkidle", timeout: 45000 });
    console.log(`   Current URL: ${page.url()}`);

    // Wait for Narrative Report Workspace
    await page.waitForSelector('[data-testid="narrative-report-workspace"]', { timeout: 25000 });
    console.log("✅ Step 1 Passed: Narrative Report Workspace loaded!");

    // Verify Multi-Varga Dignity Matrix
    console.log("\n📊 Step 2: Verifying Multi-Varga Dignity Matrix (D1, D9, D10, D7)...");
    await page.waitForSelector("text=Multi-Varga Dignity Spectrum", { timeout: 15000 });
    await page.waitForSelector("text=D1 Rashi", { timeout: 15000 });
    await page.waitForSelector("text=D9 Navamsha", { timeout: 15000 });
    await page.waitForSelector("text=D10 Dashamsha", { timeout: 15000 });
    await page.waitForSelector("text=D7 Saptamsha", { timeout: 15000 });
    await page.waitForSelector("text=VARGOTTAMA", { timeout: 15000 });
    console.log("✅ Step 2 Passed: Multi-Varga matrix and Vargottama dignities verified!");

    // Verify 9 Standardized Report Sections
    console.log("\n📜 Step 3: Verifying all 9 Standardized Report Sections...");
    await page.waitForSelector("text=1. Executive Summary & Chart Architecture", { timeout: 15000 });
    await page.waitForSelector("text=2. Multi-Varga Comparative Dignity Analysis", { timeout: 15000 });
    await page.waitForSelector("text=3. Classical Yogas & 5-Step Evidence Chains", { timeout: 15000 });
    await page.waitForSelector("text=4. Vimshottari Dasha Chronological Hierarchy", { timeout: 15000 });
    await page.waitForSelector("text=5. Gochara Transits & Ashtakavarga Confluence", { timeout: 15000 });
    await page.waitForSelector("text=6. Krishnamurti Paddhati (KP) Cuspal Analysis", { timeout: 15000 });
    await page.waitForSelector("text=7. Sarvatobhadra Chakra (SBC) Vedha Matrix", { timeout: 15000 });
    await page.waitForSelector("text=8. Comparative Findings & Synastry Matrix", { timeout: 15000 });
    await page.waitForSelector("text=9. Limitations & Epistemic Boundaries", { timeout: 15000 });
    console.log("✅ Step 3 Passed: All 9 Standardized Sections verified!");

    // Verify Technical Evidence Table & IDs
    console.log("\n🏷️ Step 4: Verifying Technical Evidence Tracking IDs...");
    await page.waitForSelector("text=EVID-D1-LAGNA", { timeout: 15000 });
    await page.waitForSelector("text=EVID-D1-MOON", { timeout: 15000 });
    await page.waitForSelector("text=EVID-VARGA-JUPITER", { timeout: 15000 });
    console.log("✅ Step 4 Passed: Technical evidence data items and tracking IDs verified!");

    // Test One-Click Exports (JSON, CSV, HTML, PDF)
    console.log("\n💾 Step 5: Testing Export Toolbar Buttons...");
    await page.waitForSelector('[data-testid="export-json-btn"]', { timeout: 15000 });
    await page.waitForSelector('[data-testid="export-csv-btn"]', { timeout: 15000 });
    await page.waitForSelector('[data-testid="export-html-btn"]', { timeout: 15000 });
    await page.waitForSelector('[data-testid="export-pdf-btn"]', { timeout: 15000 });
    console.log("✅ Step 5 Passed: Export toolbar buttons (PDF/HTML/CSV/JSON) verified!");

    // ══════════════════════════════════════════════════════════════════════════
    // PART 2: COMPARATIVE SYNASTRY WORKSPACE (/reports/comparison)
    // ══════════════════════════════════════════════════════════════════════════
    console.log("\n📍 Step 6: Navigating to http://localhost:3000/reports/comparison ...");
    await page.goto("http://localhost:3000/reports/comparison", { waitUntil: "networkidle", timeout: 45000 });
    console.log(`   Current URL: ${page.url()}`);

    // Wait for Comparative Analysis Panel
    await page.waitForSelector('[data-testid="comparative-analysis-panel"]', { timeout: 25000 });
    console.log("✅ Step 6 Passed: Comparative Analysis Panel loaded!");

    // Verify Synastry Metrics
    console.log("\n❤️ Step 7: Verifying Synastry Axes & Ashtakoota Guna Score...");
    await page.waitForSelector("text=Lagna Axis Relationship", { timeout: 15000 });
    await page.waitForSelector("text=Lunar Axis Relationship", { timeout: 15000 });
    await page.waitForSelector("text=Guna Score:", { timeout: 15000 });
    console.log("✅ Step 7 Passed: Comparative Lagna/Moon axes and Ashtakoota Guna score verified!");

    console.log("\n==========================================================================");
    console.log("🎉 ALL NARRATIVE & COMPARATIVE REPORTING REAL BROWSER E2E TESTS PASSED 100%!");
    console.log("==========================================================================");
    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error("❌ Browser E2E Test Failed:", err);
    await browser.close();
    process.exit(1);
  }
}

runE2E();
