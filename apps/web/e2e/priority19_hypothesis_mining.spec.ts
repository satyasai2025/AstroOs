import { test, expect } from "@playwright/test";

test.describe("Priority 19: Research Discovery & Hypothesis Mining Studio", () => {
  test("loads hypothesis mining studio, executes discovery engine, inspects leaderboard, primitives, and holdout replication", async ({
    page,
  }) => {
    await page.goto("/research/hypothesis-mining");

    // 1. Verify Page Header
    await expect(page.locator("h1")).toContainText(
      "Priority 19: Research Discovery & Hypothesis Mining Engine"
    );

    // 2. Trigger Discovery Engine
    const runBtn = page.locator("button:has-text('Run Discovery Engine')");
    await expect(runBtn).toBeVisible();
    await runBtn.click();

    // 3. Verify Metric Cards
    await expect(page.locator("span:has-text('Combinations Evaluated')")).toBeVisible({ timeout: 20000 });
    await expect(page.locator("span:has-text('Candidate Hypotheses')")).toBeVisible();
    await expect(page.locator("span:has-text('Replicated & Validated')")).toBeVisible();
    await expect(page.locator("span:has-text('FDR Rejected')")).toBeVisible();

    // 4. Verify Leaderboard Tab
    await expect(page.locator("text=Discovered Hypotheses Leaderboard")).toBeVisible();
    await expect(page.locator("text=REPLICATED VALIDATED").first()).toBeVisible();

    // 5. Navigate to Primitives Tab
    await page.click("button:has-text('Pattern Primitives & Astrological Decomposition')");
    await expect(page.locator("text=Pattern Primitives for:")).toBeVisible();

    // 6. Navigate to Replication Tab
    await page.click("button:has-text('Independent Holdout Replication Matrix')");
    await expect(page.locator("text=Independent Holdout Replication Records")).toBeVisible();
    await expect(page.locator("text=CONFIRMED REPLICATION").first()).toBeVisible();
  });
});
