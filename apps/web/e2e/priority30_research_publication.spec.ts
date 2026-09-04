import { test, expect } from "@playwright/test";

test.describe("Priority 30: Research Publication & Cryptographic Audit Report Studio", () => {
  test("loads publication studio, compiles report, inspects non-causal declarations, audit chain, and SHA-256 seal", async ({ page }) => {
    // 1. Navigate to Publication Studio
    await page.goto("/research/publication");
    await page.waitForLoadState("networkidle");

    // Verify Title & Header
    await expect(page.locator("text=Priority 30: Research Publication & Cryptographic Audit Report")).toBeVisible();
    await expect(page.locator("text=PUBLICATION_EPISTEMIC_DECLARATION")).toBeVisible();

    // 2. Verify Top Metrics Cards (allow time for initial pipeline compilation)
    await expect(page.locator("text=Pipeline Stages")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=P1→P29").first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=Audit Chain Entries")).toBeVisible();
    await expect(page.locator("text=Non-Causal Compliance")).toBeVisible();

    // 3. Inspect Publication Report Tab & Sections
    await expect(page.locator("button:has-text('📝 Publication Report')")).toBeVisible();
    await expect(page.locator("text=Abstract").first()).toBeVisible();
    await expect(page.locator("text=Methodology").first()).toBeVisible();
    await expect(page.locator("text=Epistemic Limitations").first()).toBeVisible();

    // Click Epistemic Limitations section
    await page.click("button:has-text('Epistemic Limitations')");
    await expect(page.locator("text=NON-CAUSAL COMPLIANT ✓").first()).toBeVisible();

    // 4. Switch to Cryptographic Audit Chain Tab
    await page.click("button:has-text('🔗 Cryptographic Audit Chain')");
    await expect(page.locator("text=Cryptographic Audit Chain —")).toBeVisible();
    await expect(page.locator("text=P1-P9").first()).toBeVisible();
    await expect(page.locator("text=P29").first()).toBeVisible();

    // 5. Switch to SHA-256 Report Seal Tab
    await page.click("button:has-text('🔐 SHA-256 Report Seal')");
    await expect(page.locator("text=Report SHA-256 Cryptographic Seal")).toBeVisible();
    await expect(page.locator("text=P11 Root Snapshot:")).toBeVisible();
  });
});
