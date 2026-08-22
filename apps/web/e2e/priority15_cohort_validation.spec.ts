import { test, expect } from "@playwright/test";

test.describe("Priority 15: Longitudinal Cohort Statistical Validation Studio", () => {
  test("loads cohort validation studio, selects dataset, executes Monte Carlo test, and verifies significance", async ({
    page,
  }) => {
    await page.goto("/research/cohort");

    // 1. Verify Page Loaded
    await expect(page.locator("h1")).toContainText(
      "Priority 15: Longitudinal Resonance & Large-Scale Cohort Statistical Validation Suite"
    );

    // 2. Trigger Cohort Validation
    const evalButton = page.locator("button:has-text('Execute Cohort Statistical Validation')");
    await expect(evalButton).toBeVisible();
    await evalButton.click();

    // 3. Verify Statistical Metrics Score Cards
    await expect(page.locator("span:has-text('Empirical ROC-AUC')")).toBeVisible();
    await expect(page.locator("span:has-text('Brier Calibration Score')")).toBeVisible();
    await expect(page.locator("span:has-text('Permutation p-value')")).toBeVisible();
    await expect(page.locator("span:has-text('Evaluated Subjects')")).toBeVisible();

    // 4. Verify Executive Summary Banner
    await expect(page.locator("text=Executive Statistical Synthesis & Confidence Bounds")).toBeVisible();

    // 5. Verify Hypothesis Significance Table
    await expect(page.locator("text=Formal Hypothesis Significance Tests")).toBeVisible();
    await expect(page.locator("text=CONFIRMED (p < 0.05)")).toBeVisible();
  });
});
