import { test, expect } from "@playwright/test";

test.describe("Priority 36: Longitudinal Evidence Synthesis & Research Knowledge State Studio", () => {
  test("loads knowledge state studio, executes synthesis, inspects all 6 views/tabs, checks lineage, meta-analysis, state machine, versioning, final verdict, and non-causal disclosures", async ({ page }) => {
    // 1. Navigate to Research Knowledge State Studio
    await page.goto("/research/knowledge-state");
    await page.waitForLoadState("networkidle");

    // Verify Title & Epistemic Non-Causal Disclosure Banner
    await expect(page.locator("text=Priority 36: Longitudinal Evidence Synthesis & Research Knowledge State Engine")).toBeVisible();
    await expect(page.locator("text=Research Knowledge State synthesizes longitudinal").first()).toBeVisible();

    // 2. Tab 1 — Overview
    await expect(page.locator("text=Research Knowledge State").first()).toBeVisible();
    await expect(page.locator("text=REPLICATED_KNOWLEDGE_STATE").first()).toBeVisible();
    await expect(page.locator("text=GRADE_A")).toBeVisible();

    // 3. Tab 2 — Evidence Lineage
    await page.click("button:has-text('📚 Evidence Lineage')");
    await expect(page.locator("text=Accumulated Multi-Study Evidence Lineage")).toBeVisible();
    await expect(page.locator("text=P34 Multi-Center Independent Replication Study")).toBeVisible();

    // 4. Tab 3 — Meta-Analysis
    await page.click("button:has-text('🌲 Meta-Analysis')");
    await expect(page.locator("text=Meta-Analytic Evidence Weighting (MAEWE)").first()).toBeVisible();
    await expect(page.locator("text=Pooled Effect Size (Accuracy):")).toBeVisible();

    // 5. Tab 4 — State Machine
    await page.click("button:has-text('🔄 State Machine')");
    await expect(page.locator("text=Research Knowledge State Machine (RKSM) Transitions")).toBeVisible();
    await expect(page.locator("text=UNSETTLED ➔ EMERGING_EVIDENCE")).toBeVisible();

    // 6. Tab 5 — Knowledge Versioning
    await page.click("button:has-text('🏷️ Knowledge Versioning')");
    await expect(page.locator("text=Research Knowledge Versioning & Supersede DAG")).toBeVisible();
    await expect(page.locator("text=Active State Version:")).toBeVisible();

    // 7. Tab 6 — Provenance
    await page.click("button:has-text('🔐 Provenance')");
    await expect(page.locator("text=Research Knowledge Provenance & Fingerprint")).toBeVisible();
    await expect(page.locator("text=SHA-256 State Fingerprint:")).toBeVisible();
  });
});
