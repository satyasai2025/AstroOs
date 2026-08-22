import { test, expect } from "@playwright/test";

test.describe("Priority 20: Prospective Research Validation & Rule Lifecycle Studio", () => {
  test("loads prospective studio, pre-registers rule, executes forward prospective evaluation, and inspects metrics, drift, and ledger", async ({
    page,
  }) => {
    await page.goto("/research/prospective");

    // 1. Verify Page Header
    await expect(page.locator("h1")).toContainText(
      "Priority 20: Prospective Research Validation & Rule Lifecycle Engine"
    );

    // 2. Run Prospective Validation
    const runBtn = page.locator("button:has-text('Run Prospective Validation')");
    await expect(runBtn).toBeVisible();
    await runBtn.click();

    // 3. Verify Metric Cards
    await expect(page.locator("span:has-text('Prospective ROC-AUC')")).toBeVisible({ timeout: 20000 });
    await expect(page.locator("span:has-text('Brier & Log Loss')")).toBeVisible();
    await expect(page.locator("span:has-text('Empirical Lift')")).toBeVisible();
    await expect(page.locator("span:has-text('Lifecycle Classification')")).toBeVisible();

    // 4. Verify Metrics Tab
    await expect(page.locator("text=Prospective Validation Metrics")).toBeVisible();
    await expect(page.locator("text=PR-AUC")).toBeVisible();
    await expect(page.locator("text=Precision (PPV)")).toBeVisible();

    // 5. Navigate to Drift Tab
    await page.click("button:has-text('Temporal & Cohort Drift Analysis (PSI)')");
    await expect(page.locator("text=PSI Stability Metric")).toBeVisible();
    await expect(page.locator("text=Drift Verification Status")).toBeVisible();

    // 6. Navigate to Pre-Registration Tab
    await page.click("button:has-text('Immutable Pre-Registration Ledger')");
    await expect(page.locator("text=Frozen Rule:")).toBeVisible();
    await expect(page.locator("text=SHA-256 Hash:")).toBeVisible();
  });
});
