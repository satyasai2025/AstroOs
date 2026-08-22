import { test, expect } from "@playwright/test";

test.describe("Priority 12 — Multi-Dasha Confluence Studio E2E Verification", () => {
  test("should load confluence studio, evaluate multi-dasha matrix, and display peak alignment window", async ({ page }) => {
    // 1. Navigate to /research/confluence
    await page.goto("/research/confluence");

    // 2. Verify Page Header
    await expect(page.locator("h1")).toContainText("AstroOS Polymodal Multi-Dasha Confluence Studio");

    // 3. Verify Dasha Systems Badges
    await expect(page.locator("text=Vimshottari").first()).toBeVisible();
    await expect(page.locator("text=Yogini").first()).toBeVisible();

    // 4. Click Evaluate Confluence Button
    await page.click('button:has-text("Evaluate Polymodal Confluence")');

    // 5. Verify Peak Alignment Card & Density Score
    await expect(page.locator("text=Peak Multi-System Confluence Window")).toBeVisible();
    await expect(page.locator("text=Evaluated Confluence Windows")).toBeVisible();
    await expect(page.locator("text=win-conf-02")).toBeVisible();
  });
});
