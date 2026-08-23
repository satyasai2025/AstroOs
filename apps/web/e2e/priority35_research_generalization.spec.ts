import { test, expect } from "@playwright/test";

test.describe("Priority 35: External Validity, Generalization & Domain Transportability Studio", () => {
  test("loads generalization studio, executes assessment, inspects all 6 views/tabs, checks domains, distribution shift, matrix, boundaries, failure regions, final verdict, and non-causal disclosures", async ({ page }) => {
    // 1. Navigate to Research Generalization Studio
    await page.goto("/research/generalization");
    await page.waitForLoadState("networkidle");

    // Verify Title & Epistemic Non-Causal Disclosure Banner
    await expect(page.locator("text=Priority 35: External Validity, Generalization & Domain Transportability Engine")).toBeVisible();
    await expect(page.locator("text=External generalization evaluates performance transportability").first()).toBeVisible();

    // 2. Tab 1 — Overview
    await expect(page.locator("text=External Validity & Generalization Verdict")).toBeVisible();
    await expect(page.locator("text=GENERALIZES")).toBeVisible();

    // 3. Tab 2 — Domains
    await page.click("button:has-text('🏛️ Domains')");
    await expect(page.locator("text=Source Domain Definition").first()).toBeVisible();
    await expect(page.locator("text=Target Domains Registry")).toBeVisible();

    // 4. Tab 3 — Distribution Shift
    await page.click("button:has-text('🔀 Distribution Shift')");
    await expect(page.locator("text=Distribution Shift Engine Diagnostics")).toBeVisible();
    await expect(page.locator("text=Feature Drift Score")).toBeVisible();

    // 5. Tab 4 — Generalization Matrix
    await page.click("button:has-text('🧩 Generalization Matrix')");
    await expect(page.locator("text=Cross-Domain Generalization Matrix")).toBeVisible();
    await expect(page.locator("text=SUPPORTED").first()).toBeVisible();

    // 6. Tab 5 — Boundaries & Failures
    await page.click("button:has-text('🚨 Boundaries & Failures')");
    await expect(page.locator("text=Domain Operational Boundaries")).toBeVisible();
    await expect(page.locator("text=Failure Region Detection")).toBeVisible();

    // 7. Tab 6 — Verdict & Provenance
    await page.click("button:has-text('🏆 Verdict & Provenance')");
    await expect(page.locator("text=Verdict Rationale & Explanations")).toBeVisible();
    await expect(page.locator("text=SHA-256 Analysis Fingerprint:")).toBeVisible();
  });
});
