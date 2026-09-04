import { test, expect } from "@playwright/test";

test.describe("Priority 34: Research Reproducibility, Replication & Falsification Studio", () => {
  test("loads replication studio, executes replication, inspects all 9 tabs, checks claims, protocol freezing, exact reproduction, dataset independence, falsification, stress tests, final verdict, and non-causal disclosures", async ({ page }) => {
    // 1. Navigate to Research Replication Studio
    await page.goto("/research/replication");
    await page.waitForLoadState("networkidle");

    // Verify Title & Epistemic Non-Causal Disclosure Banner
    await expect(page.locator("text=Priority 34: Research Reproducibility, Replication & Falsification Engine")).toBeVisible();
    await expect(page.locator("text=Successful replication strengthens the evidentiary record").first()).toBeVisible();

    // 2. Tab 1 — Claims
    await expect(page.locator("text=Research Claim Registry")).toBeVisible();
    await expect(page.locator("text=Claim SHA-256 Fingerprint:")).toBeVisible();

    // 3. Tab 2 — Protocol
    await page.click("button:has-text('🔒 Protocol')");
    await expect(page.locator("text=Pre-Registered Protocol")).toBeVisible();
    await expect(page.locator("text=PROTOCOL FROZEN")).toBeVisible();

    // 4. Tab 3 — Reproduction
    await page.click("button:has-text('🔄 Reproduction')");
    await expect(page.locator("text=Exact Computation Reproduction")).toBeVisible();
    await expect(page.locator("text=REPRODUCED_EXACTLY")).toBeVisible();

    // 5. Tab 4 — Replication
    await page.click("button:has-text('🌐 Replication')");
    await expect(page.locator("text=Independent Dataset Replication")).toBeVisible();
    await expect(page.locator("text=DATASET INDEPENDENT")).toBeVisible();

    // 6. Tab 5 — Falsification
    await page.click("button:has-text('🎯 Falsification')");
    await expect(page.locator("text=Negative Control Experiment")).toBeVisible();
    await expect(page.locator("text=Label Permutation Null Model")).toBeVisible();

    // 7. Tab 6 — Stress Tests
    await page.click("button:has-text('⚡ Stress Tests')");
    await expect(page.locator("text=Stress Tests & Stability Diagnostics")).toBeVisible();

    // 8. Tab 7 — Statistics
    await page.click("button:has-text('📈 Statistics')");
    await expect(page.locator("text=Replication Statistical Comparison")).toBeVisible();

    // 9. Tab 8 — Verdict
    await page.click("button:has-text('🏆 Verdict')");
    await expect(page.locator("text=Final Replication Verdict")).toBeVisible();
    await expect(page.locator("text=Verdict Rationale & Explanations")).toBeVisible();

    // 10. Tab 9 — Provenance
    await page.click("button:has-text('🔐 Provenance')");
    await expect(page.locator("text=Replication Provenance & Snapshot Linkage")).toBeVisible();
    await expect(page.locator("text=Replication SHA-256 Fingerprint:")).toBeVisible();
  });
});
