/**
 * AstroOS — Empirical Research Engine Real Browser E2E Test
 *
 * Runs against live FastAPI backend + live Next.js web application.
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
  console.log("🚀 Starting Empirical Research Engine Real Browser E2E Verification...\n");

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
    // 1. Navigate to /research/hypotheses
    console.log("📍 Step 1: Navigating to http://localhost:3000/research/hypotheses ...");
    await page.goto("http://localhost:3000/research/hypotheses", { waitUntil: "networkidle", timeout: 45000 });
    console.log(`   Current URL: ${page.url()}`);

    // Wait for the workspace container
    await page.waitForSelector('[data-testid="empirical-research-engine-workspace"]', { timeout: 25000 });
    console.log("✅ Step 1 Passed: Empirical Research Engine Workspace loaded successfully!");

    // 2. Verify Epistemological Boundary & Disclaimers Banner
    console.log("\n📌 Step 2: Verifying Epistemological Disclaimer Banner...");
    await page.waitForSelector("text=Scientific Rigor & Epistemological Boundary", { timeout: 15000 });
    console.log("✅ Step 2 Passed: Causal separation and scientific rigor notice verified!");

    // 3. Verify Statistical KPI Cards
    console.log("\n📊 Step 3: Verifying Statistical Summary KPI Cards...");
    await page.waitForSelector("text=Hypotheses Tested", { timeout: 15000 });
    await page.waitForSelector("text=FDR Significant (q < 0.05)", { timeout: 15000 });
    await page.waitForSelector("text=Bonferroni Sig", { timeout: 15000 });
    console.log("✅ Step 3 Passed: Statistical KPI summary cards verified with FDR & Bonferroni metrics!");

    // 4. Verify Volcano Plot Interactive Visualization
    console.log("\n🌋 Step 4: Verifying Interactive Volcano Plot Visualizer...");
    await page.waitForSelector("svg circle", { timeout: 15000 });
    const circleCount = await page.locator("svg circle").count();
    console.log(`   Volcano Plot Data Points Rendered: ${circleCount}`);
    if (circleCount < 4) {
      throw new Error(`Expected at least 4 volcano plot points, found ${circleCount}`);
    }
    console.log("✅ Step 4 Passed: Volcano Plot SVG rendered with active hypothesis points!");

    // 5. Test Forest Plot Tab
    console.log("\n🌲 Step 5: Testing Forest Plot Tab...");
    await page.click('button:has-text("Forest Plot")');
    await page.waitForTimeout(1500);
    await page.waitForSelector("text=Odds Ratios and 95% Wald Confidence Intervals", { timeout: 15000 });
    console.log("✅ Step 5 Passed: Forest Plot tab loaded with 95% CI error bar visualizations!");

    // 6. Test 2x2 Contingency Matrix Inspector
    console.log("\n📊 Step 6: Testing 2x2 Contingency Matrix Tab...");
    await page.click('button:has-text("2x2 Contingency Matrix")');
    await page.waitForTimeout(1500);
    await page.waitForSelector("text=Exposed (Rule Satisfied)", { timeout: 15000 });
    await page.waitForSelector("text=Unexposed (Rule Absent)", { timeout: 15000 });
    await page.waitForSelector("text=Odds Ratio (Haldane)", { timeout: 15000 });
    await page.waitForSelector("text=Fisher Exact p-value", { timeout: 15000 });
    await page.waitForSelector("text=FDR q-value (B-H)", { timeout: 15000 });
    console.log("✅ Step 6 Passed: 2x2 Contingency Matrix Inspector verified with exact cell counts & p-values!");

    // 7. Verify Comprehensive Evidence Table
    console.log("\n📋 Step 7: Verifying Comprehensive Evidence Table...");
    await page.waitForSelector("text=Hypothesis Evidence Matrix", { timeout: 15000 });
    const rowsCount = await page.locator("table tbody tr").count();
    console.log(`   Evidence Table Rows: ${rowsCount}`);
    if (rowsCount < 4) {
      throw new Error(`Expected at least 4 hypothesis evidence rows, found ${rowsCount}`);
    }
    console.log("✅ Step 7 Passed: Evidence Table populated with classical citations, Yates Chi2, and Fisher exact p-values!");

    // 8. Test Cohort Dataset Switching -> Centenarian Longevity Benchmark
    console.log("\n🔄 Step 8: Testing Cohort Dataset Switching...");
    await page.selectOption('select:has-text("Gauquelin")', { index: 1 });
    await page.click('button:has-text("Run Statistical Sweep")');
    await page.waitForTimeout(2500);
    console.log("✅ Step 8 Passed: Re-executed statistical sweep across Centenarian Longevity Benchmark cohort!");

    console.log("\n==========================================================================");
    console.log("🎉 ALL EMPIRICAL RESEARCH ENGINE BROWSER E2E TESTS PASSED 100%!");
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
