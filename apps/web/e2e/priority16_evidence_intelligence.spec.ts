import { test, expect } from "@playwright/test";

test.describe("Priority 16: Research Knowledge & Evidence Intelligence Studio", () => {
  test("loads evidence studio, synthesizes intelligence, navigates tabs, and inspects technique provenance", async ({
    page,
  }) => {
    await page.goto("/research/evidence");

    // 1. Verify Page Header
    await expect(page.locator("h1")).toContainText(
      "Priority 16: Research Knowledge & Evidence Intelligence Engine"
    );

    // 2. Synthesize Evidence Intelligence
    const queryBtn = page.locator("button:has-text('Synthesize Evidence Intelligence')");
    await expect(queryBtn).toBeVisible();
    await queryBtn.click();

    // 3. Verify Metric Score Cards
    await expect(page.locator("span:has-text('Techniques Evaluated')")).toBeVisible();
    await expect(page.locator("span:has-text('Grade A (Rigorous)')")).toBeVisible();
    await expect(page.locator("span:has-text('Confirmed Synergies')")).toBeVisible();
    await expect(page.locator("span:has-text('Condition Rules')")).toBeVisible();

    // 4. Verify Leaderboard & Technique Selection
    await expect(page.locator("text=Ranked Astrological Techniques by Empirical Evidence")).toBeVisible();
    await expect(page.locator("text=Technique Provenance")).toBeVisible();

    // 5. Navigate to Synergies Tab
    await page.click("button:has-text('Cross-Technique Synergy Matrix')");
    await expect(page.locator("text=Pairwise Cross-Technique Synergies")).toBeVisible();
    await expect(page.locator("text=CONFIRMED SYNERGY").first()).toBeVisible();

    // 6. Navigate to Conditions Tab
    await page.click("button:has-text('Contextual Condition Attribution Rules')");
    await expect(page.locator("text=Contextual Astrological Conditions")).toBeVisible();
    await expect(page.locator("text=AMPLIFIER").first()).toBeVisible();
  });
});
