import { test, expect } from "@playwright/test";

test.describe("Priority 14: Inverse Natal Profiling & Rectification Studio", () => {
  test("loads rectification studio, adds event, executes Bayesian search, and inspects candidate", async ({
    page,
  }) => {
    await page.goto("/research/rectification");

    // 1. Verify Page Loaded
    await expect(page.locator("h1")).toContainText(
      "Priority 14: Inverse Natal Profiling & Evolutionary Chart Rectification Studio"
    );

    // 2. Add Life Event
    await page.click("button:has-text('+ Add Event')");
    await expect(page.locator("span:has-text('Event(s) Configured')")).toBeVisible();

    // 3. Trigger Bayesian Rectification Search
    const searchBtn = page.locator("button:has-text('Run Bayesian Rectification Search')");
    await expect(searchBtn).toBeVisible();
    await searchBtn.click();

    // 4. Verify Metrics Rendered
    await expect(page.locator("span:has-text('Candidates Evaluated')")).toBeVisible();
    await expect(page.locator("span:has-text('Best Offset')")).toBeVisible();
    await expect(page.locator("span:has-text('Posterior Probability')")).toBeVisible();
    await expect(page.locator("span:has-text('Matched Events')")).toBeVisible();

    // 5. Verify Candidate Table
    await expect(page.locator("text=Ranked Candidate Moments")).toBeVisible();
    await expect(page.locator("text=Per-Event Verification Traces")).toBeVisible();

    // 6. Test Candidate Inspection Switch
    const inspectButtons = page.locator("button:has-text('Inspect')");
    if ((await inspectButtons.count()) > 1) {
      await inspectButtons.nth(1).click();
      await expect(page.locator("text=Candidate Audit:")).toBeVisible();
    }
  });
});
