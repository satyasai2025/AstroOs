import { test, expect } from "@playwright/test";

test.describe("Priority 25: Research Decision & Evidence Action Studio", () => {
  test("loads decision action studio, evaluates empirical research readiness, inspects action verdict, scorecard, policy, and non-causal disclosures", async ({
    page,
  }) => {
    // 1. Visit Research Decision Action Studio
    await page.goto("/research/decision-action");

    // Verify Page Header
    await expect(page.locator("h1")).toContainText(
      "Priority 25: Research Decision & Evidence Action Engine"
    );

    // Verify Metric Cards
    await expect(page.locator("text=Empirical Research Action Verdict")).toBeVisible();
    await expect(page.locator("text=Readiness Score")).toBeVisible();
    await expect(page.locator("text=P23 Synthesized Confidence")).toBeVisible();

    // 2. Evaluate Research Action Decision
    const evalBtn = page.locator("button:has-text('Evaluate Action Decision')");
    await expect(evalBtn).toBeVisible();
    await evalBtn.click();

    // 3. Inspect Factor Scorecard Tab
    await expect(page.locator("text=Cohort Monte Carlo Statistical Significance")).toBeVisible();
    await expect(page.locator("text=Blind Forward Prospective Validation")).toBeVisible();
    await expect(page.locator("text=Independent Manifest Reproducibility & Zero Drift")).toBeVisible();

    // 4. Switch to Evidence vs Risks Tab
    await page.click("button:has-text('Evidence vs Risks')");
    await expect(page.locator("text=Supporting Empirical Evidence")).toBeVisible();
    await expect(page.locator("text=Risk & Attenuation Factors")).toBeVisible();

    // 5. Switch to Next-Step Policy Tab
    await page.click("button:has-text('Next-Step Policy')");
    await expect(page.locator("text=Actionable Next-Step Policy")).toBeVisible();
    await expect(page.locator("text=Planning Priority")).toBeVisible();

    // 6. Switch to Non-Causal Epistemics Tab
    await page.click("button:has-text('Non-Causal Epistemics & Lineage')");
    await expect(page.locator("text=Epistemic Scope & Non-Causal Boundary Declarations")).toBeVisible();
    await expect(page.locator("text=P11 Cryptographic Snapshot Lineage")).toBeVisible();
  });
});
