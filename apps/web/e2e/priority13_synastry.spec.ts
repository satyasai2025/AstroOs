import { test, expect } from "@playwright/test";

test.describe("Priority 13: Inter-Chart Synastry & Compatibility Studio", () => {
  test("evaluates Ashta-Kuta with classical cancellations, aspects, and joint confluence", async ({
    page,
  }) => {
    await page.goto("/research/synastry");

    // 1. Verify Page Loaded
    await expect(page.locator("h1")).toContainText(
      "Priority 13: Inter-Chart Synastry & Compatibility Studio"
    );

    // 2. Trigger Synastry Evaluation
    const evalButton = page.locator("button:has-text('Evaluate Inter-Chart Synastry')");
    await expect(evalButton).toBeVisible();
    await evalButton.click();

    // 3. Verify Ashta-Kuta Score Cards Rendered
    await expect(page.locator("span:has-text('Ashta-Kuta Total')")).toBeVisible();
    await expect(page.locator("span:has-text('Active Pariharas')")).toBeVisible();
    await expect(page.locator("span:has-text('Harmonic Aspects')")).toBeVisible();
    await expect(page.locator("span:has-text('Joint Confluence')")).toBeVisible();

    // 4. Verify Ashta-Kuta Table & Classical Provenance
    await expect(page.locator("text=Varna Kuta")).toBeVisible();
    await expect(page.locator("text=Nadi Kuta")).toBeVisible();
    await expect(page.locator("text=Classical Dosha Mitigations & Explanations")).toBeVisible();

    // 5. Test Tab Switching: Inter-Chart Aspects
    await page.locator("button:has-text('Inter-Chart Aspects')").click();
    await expect(page.locator("th:has-text('Angle')")).toBeVisible();
    await expect(page.locator("th:has-text('Harmonic Nature')")).toBeVisible();

    // 6. Test Tab Switching: Cross-House Overlays
    await page.locator("button:has-text('Cross-House Overlays')").click();
    await expect(page.locator("th:has-text('Chart A Planet')")).toBeVisible();
    await expect(page.locator("th:has-text('Occupied House in Chart B')")).toBeVisible();

    // 7. Test Tab Switching: Joint Multi-Dasha Confluence Timing
    await page.locator("button:has-text('Joint Multi-Dasha Confluence')").click();
    await expect(page.locator("th:has-text('Joint Confluence Score')")).toBeVisible();
  });
});
