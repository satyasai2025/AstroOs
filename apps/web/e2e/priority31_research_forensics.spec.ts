import { test, expect } from "@playwright/test";

test.describe("Priority 31: Research Forensic & Evidence Reconstruction Studio", () => {
  test("loads forensic studio, verifies verdict, evidence chain, reconstruction, timeline, synthetic-vs-real distinction, cryptographic seals, and non-causal disclosures", async ({ page }) => {
    // 1. Navigate to Research Forensics Studio
    await page.goto("/research/forensics");
    await page.waitForLoadState("networkidle");

    // Verify Title & Header
    await expect(page.locator("text=Priority 31: Research Forensic & Evidence Reconstruction Engine")).toBeVisible();
    await expect(page.locator("text=FORENSIC_EPISTEMIC_DISCLOSURE").first()).toBeVisible();
    await expect(page.locator("text=SYNTHETIC_DATA_DISCLOSURE").first()).toBeVisible();

    // 2. Verify Tab 1 — Forensic Verdict & Metrics Cards
    await expect(page.locator("text=Independent Forensic Audit Verdict")).toBeVisible();
    await expect(page.locator("text=RECONSTRUCTED_WITH_ZERO_DRIFT").first()).toBeVisible();
    await expect(page.locator("text=EXACT MATCH (100%)")).toBeVisible();
    await expect(page.locator("text=INTACT & CONTINUOUS")).toBeVisible();

    // 3. Switch to Tab 2 — Evidence Chain
    await page.click("button:has-text('🔗 Evidence Chain')");
    await expect(page.locator("text=Collected Forensic Evidence Chain —")).toBeVisible();
    await expect(page.locator("text=SYNTHETIC_GENERATED_EVIDENCE").first()).toBeVisible();
    await expect(page.locator("text=CLASSICAL_REFERENCE_EVIDENCE").first()).toBeVisible();

    // 4. Switch to Tab 3 — Reconstruction & Replay
    await page.click("button:has-text('🔄 Reconstruction & Replay')");
    await expect(page.locator("text=Original Output Canonical Hash:")).toBeVisible();
    await expect(page.locator("text=Reconstructed Output Canonical Hash:")).toBeVisible();
    await expect(page.locator("text=Intermediate Calculation Trace Steps")).toBeVisible();

    // 5. Switch to Tab 4 — Provenance Timeline
    await page.click("button:has-text('📈 Provenance Timeline')");
    await expect(page.locator("text=P1 → P31 Interactive Lineage & Provenance Trace")).toBeVisible();
    await expect(page.locator("text=P1-P9 — EphemerisEngine")).toBeVisible();

    // 6. Switch to Tab 5 — Synthetic vs Real Evidence
    await page.click("button:has-text('📊 Synthetic vs Real Evidence')");
    await expect(page.locator("text=Synthetic / Generated")).toBeVisible();
    await expect(page.locator("text=Classical Reference")).toBeVisible();
    await expect(page.locator("text=Derived Computational")).toBeVisible();

    // 7. Switch to Tab 6 — Cryptographic Seals
    await page.click("button:has-text('🔐 Cryptographic Seals')");
    await expect(page.locator("text=P31 Forensic SHA-256 Seal")).toBeVisible();
    await expect(page.locator("text=P11 Snapshot DAG:")).toBeVisible();
    await expect(page.locator("text=P30 Publication Seal:")).toBeVisible();
  });
});
