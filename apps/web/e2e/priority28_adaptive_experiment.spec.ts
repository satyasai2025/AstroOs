import { test, expect } from "@playwright/test";

test.describe("Priority 28: Adaptive Research & Sequential Experiment Studio", () => {
  test("loads adaptive experiment studio, evaluates sequential interim look, inspects alpha spending, immutable commitment, strata, and governance", async ({
    page,
  }) => {
    // 1. Visit Research Adaptive Experiment Studio
    await page.goto("/research/adaptive-experiment");

    // Verify Page Header
    await expect(page.locator("h1")).toContainText(
      "Priority 28: Adaptive Research & Experiment Engine"
    );

    // Verify Metric Cards
    await expect(page.locator("text=Interim Decision Verdict")).toBeVisible();
    await expect(page.locator("text=Information Fraction (t)")).toBeVisible();
    await expect(page.locator("text=Cumulative Alpha Spent (α*)")).toBeVisible();

    // 2. Evaluate Sequential Interim Look
    const evalBtn = page.locator("button:has-text('Evaluate Sequential Interim Look')");
    await expect(evalBtn).toBeVisible();
    await evalBtn.click();

    // 3. Inspect Sequential Boundaries & Stopping Rules Tab
    await expect(page.locator("text=Sequential Decision Diagnosis")).toBeVisible();
    await expect(page.locator("th:has-text('Alpha Spent (α*)')")).toBeVisible();
    await expect(page.locator("th:has-text('Efficacy z_α')")).toBeVisible();

    // 4. Switch to Immutable Pre-Trial Commitment Tab
    await page.click("button:has-text('Immutable Pre-Trial Commitment')");
    await expect(page.locator("text=Anti-HARKing Enforcement")).toBeVisible();
    await expect(page.locator("text=Immutable Rule & Parameter Commitment")).toBeVisible();
    await expect(page.locator("text=Spending Function Method")).toBeVisible();

    // 5. Switch to Predefined Stratification & Blinded Sample Size Tab
    await page.click("button:has-text('Predefined Stratification & Blinded Sample Size')");
    await expect(page.locator("text=Predefined Cohort Strata (Frozen Pre-Trial)")).toBeVisible();
    await expect(page.locator("text=Information-Blind Sample Size Re-estimation")).toBeVisible();
    await expect(page.locator("th:has-text('Stratum Name')")).toBeVisible();

    // 6. Switch to Non-Causal Epistemic Governance Tab
    await page.click("button:has-text('Non-Causal Epistemic Governance')");
    await expect(page.locator("text=Epistemic Scope & Sequential Testing Guardrails")).toBeVisible();
    await expect(page.locator("text=P11 Cryptographic Snapshot Lineage")).toBeVisible();
  });
});
