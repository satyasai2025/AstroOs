import { test, expect } from "@playwright/test";

test.describe("Priority 27: Longitudinal Outcome Tracking Studio", () => {
  test("loads longitudinal tracking studio, evaluates prospective outcome stream, inspects dual-mechanism drift diagnosis, time series, and governance", async ({
    page,
  }) => {
    // 1. Visit Research Longitudinal Tracking Studio
    await page.goto("/research/longitudinal-tracking");

    // Verify Page Header
    await expect(page.locator("h1")).toContainText(
      "Priority 27: Longitudinal Outcome Tracking Engine"
    );

    // Verify Metric Cards
    await expect(page.locator("text=Cumulative Hit Rate")).toBeVisible();
    await expect(page.locator("text=Total Subjects Tracked")).toBeVisible();
    await expect(page.locator("text=Population Stability (PSI)")).toBeVisible();

    // 2. Evaluate Tracking Metrics
    const evalBtn = page.locator("button:has-text('Evaluate Tracking Metrics')");
    await expect(evalBtn).toBeVisible();
    await evalBtn.click();

    // 3. Inspect Dual-Mechanism Drift Diagnosis Tab
    await expect(page.locator("text=Population Distribution Drift (PSI)")).toBeVisible();
    await expect(page.locator("text=Statistical Degradation Test (Two-Proportion Z-Test)")).toBeVisible();

    // 4. Switch to Quarterly Time-Series Intervals Tab
    await page.click("button:has-text('Quarterly Time-Series Intervals')");
    await expect(page.locator("text=2026-Q1")).toBeVisible();
    await expect(page.locator("text=2026-Q2")).toBeVisible();

    // 5. Switch to Real-World Observation Stream Tab
    await page.click("button:has-text('Real-World Observation Stream')");
    await expect(page.locator("th:has-text('Subject ID')")).toBeVisible();
    await expect(page.locator("th:has-text('Predicted Window')")).toBeVisible();
    await expect(page.locator("th:has-text('Actual Event Date')")).toBeVisible();

    // 6. Switch to Non-Causal Epistemic Governance Tab
    await page.click("button:has-text('Non-Causal Epistemic Governance')");
    await expect(page.locator("text=Epistemic Scope & Longitudinal Observational Boundaries")).toBeVisible();
    await expect(page.locator("text=P11 Cryptographic Snapshot Lineage")).toBeVisible();
  });
});
