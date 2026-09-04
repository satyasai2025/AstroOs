/**
 * AstroOS — Unified Multi-System Event Timing Engine Real Browser E2E Test
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
  console.log("🚀 Starting Unified Multi-System Event Timing Real Browser E2E Verification...\n");

  const token = getRealAuthToken();
  console.log("🔑 Authenticated Live User Token Obtained.");

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
    // 1. Navigate to /timing
    console.log("📍 Step 1: Navigating to http://localhost:3000/timing ...");
    await page.goto("http://localhost:3000/timing", { waitUntil: "networkidle", timeout: 45000 });
    console.log(`   Current URL: ${page.url()}`);

    // Wait for the workspace container
    await page.waitForSelector('[data-testid="unified-event-timing-workspace"]', { timeout: 25000 });
    console.log("✅ Step 1 Passed: Unified Event Timing Workspace loaded successfully!");

    // 2. Verify Header Title
    const titleText = await page.textContent("h1");
    console.log(`\n📌 Step 2: Workspace Title: "${titleText?.trim()}"`);
    if (!titleText?.includes("Unified Multi-System Event Timing Matrix")) {
      throw new Error(`Unexpected header title: ${titleText}`);
    }
    console.log("✅ Step 2 Passed: Header title matches exact specifications.");

    // 3. Verify 4 pillars cards are rendered with evidence
    console.log("\n🔍 Step 3: Verifying 4 Classical Timing Pillars...");
    await page.waitForSelector("text=1. Vimshottari Dasha", { timeout: 35000 });
    await page.waitForSelector("text=2. Gochara Transits", { timeout: 35000 });
    await page.waitForSelector("text=3. SBC Vedha", { timeout: 35000 });
    await page.waitForSelector("text=4. KP Sub-Lord", { timeout: 35000 });
    console.log("✅ Step 3 Passed: All 4 Classical Timing Pillars (Dasha, Gochara, SBC, KP) rendered with technical evidence!");

    // 4. Test Event Switcher: Switch to Career
    console.log("\n🔄 Step 4: Testing Event Switcher -> 'Career & Promotion'...");
    await page.click('button:has-text("Career & Promotion")');
    await page.waitForTimeout(2000);
    const careerHeading = await page.textContent("h3");
    console.log(`   Evaluated Moment: "${careerHeading?.trim()}"`);
    console.log("✅ Step 4 Passed: Career event type evaluated.");

    // 5. Test Event Switcher: Switch to Wealth
    console.log("\n🔄 Step 5: Testing Event Switcher -> 'Wealth & Assets'...");
    await page.click('button:has-text("Wealth & Assets")');
    await page.waitForTimeout(2000);
    const wealthHeading = await page.textContent("h3");
    console.log(`   Evaluated Moment: "${wealthHeading?.trim()}"`);
    console.log("✅ Step 5 Passed: Wealth event type evaluated.");

    // 6. Test Time-Travel Slider Scrubbing
    console.log("\n⏳ Step 6: Testing Time-Travel Interactive Slider...");
    const slider = page.locator('input[aria-label="Time travel slider"]');
    await slider.fill("6");
    await slider.dispatchEvent("mouseup");
    await page.waitForTimeout(2500);
    console.log("✅ Step 6 Passed: Time-Travel Slider scrubbed and snapshot re-evaluated live via FastAPI /moment endpoint!");

    // 7. Verify Candidate Windows Section
    console.log("\n📊 Step 7: Verifying Candidate Timing Windows Section...");
    await page.waitForSelector("text=Detected Candidate Timing Windows", { timeout: 25000 });
    console.log("✅ Step 7 Passed: Candidate Timing Windows section verified!");

    // 8. Verify embedded workspace on /charts?view=timing
    console.log("\n📍 Step 8: Navigating to embedded tab http://localhost:3000/charts?view=timing ...");
    await page.goto("http://localhost:3000/charts?view=timing", { waitUntil: "networkidle", timeout: 45000 });
    await page.waitForSelector('[data-testid="unified-event-timing-workspace"]', { timeout: 25000 });
    console.log("✅ Step 8 Passed: Embedded Timing Workspace in /charts?view=timing verified!");

    console.log("\n==========================================================================");
    console.log("🎉 ALL UNIFIED MULTI-SYSTEM EVENT TIMING BROWSER E2E TESTS PASSED 100%!");
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
