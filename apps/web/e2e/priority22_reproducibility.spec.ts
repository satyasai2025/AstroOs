import { test, expect } from "@playwright/test";

test.describe("Priority 22: Research Reproducibility & Independent Validation Studio", () => {
  test("loads frozen manifests, independently re-executes manifest, and inspects metric-diff and cryptographic audit certificate", async ({
    page,
  }) => {
    // 1. Visit Reproducibility Studio
    await page.goto("/research/reproducibility");

    // Verify Page Header
    await expect(page.locator("h1")).toContainText(
      "Priority 22: Research Reproducibility & Independent Validation Engine"
    );

    // Verify Top Metric Cards
    await expect(page.locator("span:has-text('Frozen Run Manifests')")).toBeVisible();
    await expect(page.locator("span:has-text('Replication Precision')")).toBeVisible();
    await expect(page.locator("span:has-text('Drift Classification')")).toBeVisible();
    await expect(page.locator("span:has-text('P11 Snapshot DAG')")).toBeVisible();

    // 2. Run Independent Validation
    const reproBtn = page.locator("button:has-text('Run Independent Validation')");
    await expect(reproBtn).toBeVisible();
    await reproBtn.click();

    // 3. Verify Exact Metric-Diff Table
    await expect(page.locator("th:has-text('Metric Name')")).toBeVisible();
    await expect(page.locator("th:has-text('Frozen Baseline')")).toBeVisible();
    await expect(page.locator("span:has-text('EXACT MATCH')").first()).toBeVisible();

    // 4. Switch to Cryptographic Audit Certificate Tab
    await page.click("button:has-text('Cryptographic Audit & Lineage')");
    await expect(page.locator("text=Audit Certificate ID:")).toBeVisible();
    await expect(page.locator("text=Execution Latency:")).toBeVisible();
    await expect(page.locator("text=Audit Summary:")).toBeVisible();
  });
});
