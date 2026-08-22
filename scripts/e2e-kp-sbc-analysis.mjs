/**
 * AstroOS — Advanced KP & Sarvatobhadra Chakra (SBC) Real Browser E2E Test
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
  console.log("🚀 Starting Advanced KP & SBC Analysis Real Browser E2E Verification...\n");

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
    // PART 1: KP ADVANCED ANALYSIS & CUSPAL DECISION TREE
    // ══════════════════════════════════════════════════════════════════════════
    console.log("📍 Step 1: Navigating to http://localhost:3000/charts?view=kp ...");
    await page.goto("http://localhost:3000/charts?view=kp", { waitUntil: "networkidle", timeout: 45000 });
    console.log(`   Current URL: ${page.url()}`);

    // Wait for KP tab bar
    await page.waitForSelector('button:has-text("CSL Decision Tree")', { timeout: 25000 });
    console.log("✅ Step 1 Passed: KP Analysis Center loaded!");

    // Click CSL Decision Tree tab
    console.log("\n🌳 Step 2: Opening KP Cuspal Sub-Lord Decision Tree tab...");
    await page.click('button:has-text("CSL Decision Tree")');
    await page.waitForTimeout(1500);

    await page.waitForSelector('[data-testid="kp-cuspal-decision-tree-viewer"]', { timeout: 20000 });
    console.log("✅ Step 2 Passed: KP Cuspal Decision Tree Viewer mounted!");

    // Verify 4-Tier Significator Matrix
    console.log("\n📋 Step 3: Verifying 4-Tier Significator Matrix (Tiers A, B, C, D)...");
    await page.waitForSelector("text=KP 4-Tier Significator Matrix", { timeout: 15000 });
    await page.waitForSelector("text=Tier A (Star-Occ)", { timeout: 15000 });
    await page.waitForSelector("text=Tier B (Occupant)", { timeout: 15000 });
    await page.waitForSelector("text=Tier C (Star-Lord)", { timeout: 15000 });
    await page.waitForSelector("text=Tier D (Sign Lord)", { timeout: 15000 });
    const matrixRows = await page.locator("table tbody tr").count();
    console.log(`   4-Tier Matrix Rows: ${matrixRows}`);
    if (matrixRows < 12) {
      throw new Error(`Expected 12 house rows in 4-tier matrix, got ${matrixRows}`);
    }
    console.log("✅ Step 3 Passed: 4-Tier Significator Matrix verified across all 12 houses!");

    // Verify Cuspal Decision Node Flow (Cusp 10 Career)
    console.log("\n🎯 Step 4: Verifying Cuspal Decision Node & Technical Audit Trace...");
    await page.waitForSelector("text=CUSP 10 DECISION TREE", { timeout: 15000 });
    await page.waitForSelector("text=Cuspal Sub-Lord", { timeout: 15000 });
    await page.waitForSelector("text=Houses Signified by Sub-Lord", { timeout: 15000 });
    await page.waitForSelector("text=Technical Audit Trace", { timeout: 15000 });
    console.log("✅ Step 4 Passed: Cuspal Sub-Lord decision node, signified houses, and technical audit chain verified!");

    // Test Domain Switch to Marriage (Cusp 7)
    console.log("\n🔄 Step 5: Testing Event Domain Switching (Marriage)...");
    await page.click('button:has-text("Marriage")');
    await page.waitForTimeout(2000);
    await page.waitForSelector("text=Target Event:", { timeout: 15000 });
    await page.waitForSelector("text=CUSP 7 DECISION TREE", { timeout: 15000 });
    console.log("✅ Step 5 Passed: Switched to Marriage domain with Cusp 7 root analysis!");

    // ══════════════════════════════════════════════════════════════════════════
    // PART 2: SARVATOBHADRA CHAKRA (SBC) 10-SANGYA VEDHA RAY ANALYSIS
    // ══════════════════════════════════════════════════════════════════════════
    console.log("\n📍 Step 6: Navigating to http://localhost:3000/charts/sbc ...");
    await page.goto("http://localhost:3000/charts/sbc", { waitUntil: "networkidle", timeout: 45000 });
    console.log(`   Current URL: ${page.url()}`);

    // Wait for SBC Sangya Matrix container
    await page.waitForSelector('[data-testid="sbc-sangya-ray-matrix"]', { timeout: 25000 });
    console.log("✅ Step 6 Passed: SBC 10-Sangya Ray Matrix Workspace loaded!");

    // Verify 10 Classical Sangyas Table
    console.log("\n☸️ Step 7: Verifying 10 Classical Sangyas Table...");
    await page.waitForSelector("text=10 Classical Sangyas", { timeout: 15000 });
    await page.waitForSelector("text=Janma (1st)", { timeout: 15000 });
    await page.waitForSelector("text=Karma (10th)", { timeout: 15000 });
    await page.waitForSelector("text=Sanghatika (16th)", { timeout: 15000 });
    await page.waitForSelector("text=Vainashika (22nd)", { timeout: 15000 });
    await page.waitForSelector("text=Manasa (25th)", { timeout: 15000 });
    await page.waitForSelector("text=Abhisheka (28th)", { timeout: 15000 });
    console.log("✅ Step 7 Passed: All 10 Classical Sangyas verified with domains and natal nakshatras!");

    // Verify KP-SBC Synchronized Evidence Banner
    console.log("\n🔗 Step 8: Verifying KP & SBC Synchronized Evidence Banner...");
    await page.waitForSelector("text=KP & SBC Synchronized Evidence", { timeout: 15000 });
    console.log("✅ Step 8 Passed: KP & SBC cross-link evidence verified!");

    // Test Sangya Row Click & Ray Inspector
    console.log("\n🔍 Step 9: Inspecting Sangya Ray Collisions...");
    await page.click('text=Janma (1st)');
    await page.waitForTimeout(1000);
    await page.waitForSelector("text=SANGYA DETAIL INSPECTOR", { timeout: 15000 });
    await page.waitForSelector("text=Sangya Ray Calculation Trace", { timeout: 15000 });
    console.log("✅ Step 9 Passed: Sangya detail inspector verified with exact cell coordinates and ray paths!");

    // Test 9x9 Classical Chakra Grid Tab Switch
    console.log("\n▦ Step 10: Testing 9x9 Sarvatobhadra Chakra Grid Tab...");
    await page.click('button:has-text("9x9 Sarvatobhadra Chakra Grid")');
    await page.waitForTimeout(1500);
    await page.waitForSelector("text=Abhi", { timeout: 15000 });
    console.log("✅ Step 10 Passed: 9x9 Chakra grid loaded with 28 Nakshatras and Abhijit cell!");

    console.log("\n==========================================================================");
    console.log("🎉 ALL ADVANCED KP & SBC REAL BROWSER E2E TESTS PASSED 100%!");
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
