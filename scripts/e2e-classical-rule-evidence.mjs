/**
 * AstroOS — Classical Rule Evidence Engine Real Browser E2E Test
 *
 * Verifies the 5-Step Classical Evidence Chain and Knowledge Graph Integration
 * across live FastAPI backend + Next.js web application.
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
  console.log("🚀 Starting Classical Rule Evidence Engine Real Browser E2E Verification...\n");

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
    // 1. Navigate to /knowledge
    console.log("📍 Step 1: Navigating to http://localhost:3000/knowledge ...");
    await page.goto("http://localhost:3000/knowledge", { waitUntil: "networkidle", timeout: 45000 });
    console.log(`   Current URL: ${page.url()}`);

    // Wait for the workspace container
    await page.waitForSelector('[data-testid="classical-rule-evidence-workspace"]', { timeout: 25000 });
    console.log("✅ Step 1 Passed: Classical Rule Evidence Engine Workspace loaded successfully!");

    // 2. Verify Canonical Verification Seal
    console.log("\n📌 Step 2: Verifying Canonical Verification Standard Seal...");
    await page.waitForSelector("text=Canonical Verification Standard", { timeout: 15000 });
    console.log("✅ Step 2 Passed: Canonical verification seal verified!");

    // 3. Verify Step 1: Rule Taxonomy
    console.log("\n📜 Step 3: Verifying Step 1 (Rule Taxonomy & Category)...");
    await page.waitForSelector("text=STEP 1: RULE TAXONOMY", { timeout: 15000 });
    await page.waitForSelector("text=Gajakesari Yoga", { timeout: 15000 });
    console.log("✅ Step 3 Passed: Step 1 (Rule Taxonomy) rendered!");

    // 4. Verify Step 2: Canonical Sanskrit Citation
    console.log("\n📖 Step 4: Verifying Step 2 (Canonical Sanskrit Verse & Translation)...");
    await page.waitForSelector("text=STEP 2: CANONICAL SANSKRIT CITATION", { timeout: 15000 });
    await page.waitForSelector("text=Brihat Parashara Hora Shastra", { timeout: 15000 });
    await page.waitForSelector("text=kendrasthite devagurau", { timeout: 15000 });
    console.log("✅ Step 4 Passed: Step 2 (Sanskrit Citation & Devanagari verse) verified!");

    // 5. Verify Step 3: Required Astrological Conditions
    console.log("\n📋 Step 5: Verifying Step 3 (Required Astrological Conditions)...");
    await page.waitForSelector("text=STEP 3: REQUIRED ASTROLOGICAL CONDITIONS", { timeout: 15000 });
    await page.waitForSelector("text=Jupiter placed in Kendra", { timeout: 15000 });
    console.log("✅ Step 5 Passed: Step 3 (Required Conditions Checklist) verified!");

    // 6. Verify Step 4: Actual Computed Chart Evidence
    console.log("\n🎯 Step 6: Verifying Step 4 (Actual Computed Chart Evidence)...");
    await page.waitForSelector("text=STEP 4: ACTUAL COMPUTED CHART EVIDENCE", { timeout: 15000 });
    await page.waitForSelector("text=CONDITION MET", { timeout: 15000 });
    console.log("✅ Step 6 Passed: Step 4 (Actual Chart Evidence Extraction) verified!");

    // 7. Verify Step 5: Technical Result & Strength Meter
    console.log("\n📊 Step 7: Verifying Step 5 (Strength Score & Technical Result)...");
    await page.waitForSelector("text=STEP 5: TECHNICAL RESULT & STRENGTH SCORE", { timeout: 15000 });
    await page.waitForSelector("text=/100", { timeout: 15000 });
    console.log("✅ Step 7 Passed: Step 5 (Strength Meter & Fructification Verdict) verified!");

    // 8. Test Rule Selection Switching (Hamsa Yoga)
    console.log("\n🔄 Step 8: Testing Rule Switching in Sidebar...");
    await page.click('text=Hamsa Yoga');
    await page.waitForTimeout(1500);
    await page.waitForSelector("text=Pancha Mahapurusha Yogas", { timeout: 15000 });
    await page.waitForSelector("text=svarkṣottuṅagate jīve", { timeout: 15000 });
    console.log("✅ Step 8 Passed: Switched to Hamsa Yoga and verified updated 5-step evidence chain!");

    console.log("\n==========================================================================");
    console.log("🎉 ALL CLASSICAL RULE EVIDENCE ENGINE BROWSER E2E TESTS PASSED 100%!");
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
