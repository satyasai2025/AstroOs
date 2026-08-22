import { test, expect } from "@playwright/test";

test.describe("Priority 18: Large-Scale Distributed / Local Cohort Optimization Studio", () => {
  test("loads batch optimizer studio, launches chunked batch job, inspects worker telemetry and checkpoints", async ({
    page,
  }) => {
    await page.goto("/research/batch-optimizer");

    // 1. Verify Page Header
    await expect(page.locator("h1")).toContainText(
      "Priority 18: Large-Scale Distributed / Local Cohort Optimization"
    );

    // 2. Launch Batch Job
    const launchBtn = page.locator("button:has-text('Launch Batch Job')");
    await expect(launchBtn).toBeVisible();
    await launchBtn.click();

    // 3. Verify Metric Cards
    await expect(page.locator("span:has-text('Total Evaluated')")).toBeVisible({ timeout: 20000 });
    await expect(page.locator("span:has-text('Average Throughput')")).toBeVisible();
    await expect(page.locator("span:has-text('Cache Hit Rate')")).toBeVisible();
    await expect(page.locator("span:has-text('Aggregate ROC-AUC')")).toBeVisible();

    // 4. Verify Workers Tab
    await expect(page.locator("text=Parallel Compute Workers")).toBeVisible();
    await expect(page.locator("text=worker-1")).toBeVisible();

    // 5. Navigate to Checkpoints Tab
    await page.click("button:has-text('SHA-256 State Checkpoints')");
    await expect(page.locator("text=Immutable SHA-256 Checkpoint Ledger")).toBeVisible();
    await expect(page.locator("text=Chunk 2")).toBeVisible({ timeout: 10000 });

    // 6. Navigate to Metrics Tab
    await page.click("button:has-text('Online Stream Convergence Metrics')");
    await expect(page.locator("text=Aggregate Log Loss")).toBeVisible();
    await expect(page.locator("text=Aggregate Hit Rate")).toBeVisible();
  });
});
