import { test, expect } from "@playwright/test";

test.describe("Priority 21: Research Data Governance & Benchmark Validation Studio", () => {
  test("loads dataset registry and benchmark suites, executes benchmark run, and verifies quality audits", async ({
    page,
  }) => {
    // 1. Visit Datasets Studio
    await page.goto("/research/datasets");

    // Verify Page Header
    await expect(page.locator("h1")).toContainText(
      "Priority 21: Research Data Governance & Benchmark Validation Layer"
    );

    // Verify Metric Cards
    await expect(page.locator("span:has-text('Governed Datasets')")).toBeVisible();
    await expect(page.locator("span:has-text('Total Governed Records')")).toBeVisible();
    await expect(page.locator("span:has-text('Canonical Accuracy')")).toBeVisible();

    // Verify Table Row for RS-MARRIAGE-250
    await expect(page.locator("td:has-text('RS-MARRIAGE-250')")).toBeVisible();
    await expect(page.locator("tr:has-text('RS-MARRIAGE-250') span:has-text('VERIFIED_CLEAN')")).toBeVisible();

    // 2. Switch to Benchmarks Tab
    await page.click("button:has-text('Standard Benchmark Suites & Latency')");
    await expect(page.locator("label:has-text('Benchmark Suite')")).toBeVisible();

    const runBmBtn = page.locator("button:has-text('Execute Benchmark Suite')");
    await expect(runBmBtn).toBeVisible();
    await runBmBtn.click();

    // 3. Switch to Audit Tab
    await page.click("button:has-text('Deep Quality Audit & Leakage Report')");
    await expect(page.locator("text=Quality Audit:")).toBeVisible();
    await expect(page.locator("text=Temporal Leakage")).toBeVisible();
  });
});
