import { test, expect } from "@playwright/test";

test.describe("Priority 23: Research Decision & Evidence Synthesis Studio", () => {
  test("loads decision synthesis studio, executes multi-layer synthesis, and inspects epistemic separation, conflicts, and P1-P22 lineage", async ({
    page,
  }) => {
    // 1. Visit Decision Synthesis Studio
    await page.goto("/research/decision-synthesis");

    // Verify Page Header
    await expect(page.locator("h1")).toContainText(
      "Priority 23: Research Decision & Evidence Synthesis Engine"
    );

    // Verify Top Metric Cards
    await expect(page.locator("span:has-text('Confidence Tier')")).toBeVisible();
    await expect(page.locator("span:has-text('Synthesized Score')")).toBeVisible();
    await expect(page.locator("span:has-text('Replicated Hypotheses')")).toBeVisible();
    await expect(page.locator("span:has-text('Lineage Integrity')")).toBeVisible();

    // 2. Generate Defensible Decision Synthesis
    const synthBtn = page.locator("button:has-text('Generate Defensible Decision Synthesis')");
    await expect(synthBtn).toBeVisible();
    await synthBtn.click();

    // 3. Inspect Epistemic Separation Badges
    await expect(page.locator("span:has-text('CLASSICAL_CANONICAL_RULE')").first()).toBeVisible();
    await expect(page.locator("span:has-text('EMPIRICALLY_SUPPORTED_PROSPECTIVE_RULE')").first()).toBeVisible();

    // 4. Switch to Contradiction & Arbitration Tab
    await page.click("button:has-text('Evidence Conflicts & Arbitration')");
    await expect(page.locator("text=Conflict: NATAL_PROMISE_VS_TIMING_BLOCK")).toBeVisible();
    await expect(page.locator("text=Arbitration: TIMING_DOMINATES_CAPACITY")).toBeVisible();

    // 5. Switch to Lineage DAG Tab
    await page.click("button:has-text('End-to-End P1 → P22 Lineage DAG')");
    await expect(page.locator("text=P1_EPHEMERIS")).toBeVisible();
    await expect(page.locator("text=P22_REPRODUCIBILITY")).toBeVisible();

    // 6. Switch to Summary Tab
    await page.click("button:has-text('Defensible Research Synthesis')");
    await expect(page.locator("text=Recommended Prediction Factors:")).toBeVisible();
  });
});
