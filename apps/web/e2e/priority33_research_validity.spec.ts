import { test, expect } from "@playwright/test";

test.describe("Priority 33: Research Validity & Statistical Integrity Studio", () => {
  test("loads validity studio, executes assessment, inspects all 7 tabs, checks diagnostics, baselines, Wilson CIs, final verdict, and non-causal disclosures", async ({ page }) => {
    // 1. Navigate to Research Validity Studio
    await page.goto("/research/validity");
    await page.waitForLoadState("networkidle");

    // Verify Title & Epistemic Non-Causal Disclosure Banner
    await expect(page.locator("text=Priority 33: Research Validity & Statistical Integrity Engine")).toBeVisible();
    await expect(page.locator("text=Validity assessment evaluates statistical integrity, temporal ordering").first()).toBeVisible();

    // 2. Tab 1 — Overview
    await expect(page.locator("text=Research Validity Verdict")).toBeVisible();
    await expect(page.locator("text=Usable Observations")).toBeVisible();
    await expect(page.locator("text=Temporal Integrity").first()).toBeVisible();
    await expect(page.locator("text=Data Leakage").first()).toBeVisible();
    await expect(page.locator("text=Baseline Lift").first()).toBeVisible();

    // 3. Tab 2 — Dataset Manifest
    await page.click("button:has-text('📁 Dataset Manifest')");
    await expect(page.locator("text=Research Dataset Manifest")).toBeVisible();
    await expect(page.locator("text=Manifest SHA-256 Hash:")).toBeVisible();

    // 4. Tab 3 — Bias & Integrity
    await page.click("button:has-text('🛡️ Bias & Integrity')");
    await expect(page.locator("text=Selection Bias Diagnostic")).toBeVisible();
    await expect(page.locator("text=Data Leakage Diagnostic")).toBeVisible();

    // 5. Tab 4 — Statistics
    await page.click("button:has-text('📈 Statistics')");
    await expect(page.locator("text=Statistical Results & Wilson 95% Confidence Intervals")).toBeVisible();
    await expect(page.locator("text=CLASSIFICATION_ACCURACY")).toBeVisible();

    // 6. Tab 5 — Baselines
    await page.click("button:has-text('⚖️ Baselines')");
    await expect(page.locator("text=Model vs Baseline Comparison")).toBeVisible();
    await expect(page.locator("text=Majority Class Baseline")).toBeVisible();

    // 7. Tab 6 — Final Verdict
    await page.click("button:has-text('🏆 Final Verdict')");
    await expect(page.locator("text=Final Research Integrity Verdict")).toBeVisible();
    await expect(page.locator("text=Verdict Rationale & Explanations")).toBeVisible();

    // 8. Tab 7 — Provenance
    await page.click("button:has-text('🔐 Provenance')");
    await expect(page.locator("text=Validity Provenance & Snapshot Linkage")).toBeVisible();
    await expect(page.locator("text=Analysis SHA-256 Fingerprint:")).toBeVisible();
  });
});
