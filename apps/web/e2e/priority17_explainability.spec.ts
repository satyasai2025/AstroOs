import { test, expect } from "@playwright/test";

test.describe("Priority 17: Research & Prediction Explainability Studio", () => {
  test("loads explainability studio, generates deconstruction report, checks tabs and counterfactual live simulation", async ({
    page,
  }) => {
    await page.goto("/research/explainability");

    // 1. Verify Page Header
    await expect(page.locator("h1")).toContainText(
      "Priority 17: Research & Prediction Explainability Engine"
    );

    // 2. Generate Prediction Deconstruction Report
    const genBtn = page.locator("button:has-text('Deconstruct & Explain Prediction')");
    await expect(genBtn).toBeVisible();
    await genBtn.click();

    // 3. Verify Metric Cards & Narrative Synthesis with proper timeout
    await expect(page.locator("span:has-text('Confidence Score')")).toBeVisible({ timeout: 20000 });
    await expect(page.locator("span:has-text('Atomic Factors')")).toBeVisible();
    await expect(page.locator("span:has-text('Canonical Citations')")).toBeVisible();
    await expect(page.locator("span:has-text('Recalculated Scenarios')")).toBeVisible();
    await expect(page.locator("text=Plain English Narrative Synthesis")).toBeVisible();
    await expect(page.locator("text=Traceable P1–P16 Lineage Provenance Chain")).toBeVisible();

    // 4. Verify Factor Waterfall Tab
    await expect(page.locator("text=Model Factor Attribution Waterfall")).toBeVisible();
    await expect(page.locator("text=Factor Context & Provenance")).toBeVisible();

    // 5. Navigate to Classical Tab
    await page.click("button:has-text('Canonical Classical Shloka Provenance')");
    await expect(page.locator("text=Canonical Classical Text Citations & Astrological Rules")).toBeVisible();
    await expect(page.locator("text=VERIFIED CANONICAL").first()).toBeVisible();

    // 6. Navigate to Counterfactual Tab
    await page.click("button:has-text('Counterfactual Sensitivity Analysis')");
    await expect(page.locator("text=Pre-Computed Engine Recalculation Scenarios")).toBeVisible();
    await expect(page.locator("text=Interactive Counterfactual Playground")).toBeVisible();

    // 7. Run Interactive Counterfactual Simulation
    const simBtn = page.locator("button:has-text('Simulate Perturbation')");
    await expect(simBtn).toBeVisible();
    await simBtn.click();
    await expect(page.locator("text=Recalculated by:")).toBeVisible({ timeout: 15000 });
  });
});
