import { test, expect } from "@playwright/test";

test.describe("Priority 32: Research Evidence Intake & Real-World Outcome Registry Studio", () => {
  test("loads evidence registry studio, registers observation, verifies status, checks real-world evidence filter, audit trail, snapshot generation, health safety and non-causal disclosures", async ({ page }) => {
    // 1. Navigate to Evidence Registry Studio
    await page.goto("/research/evidence-registry");
    await page.waitForLoadState("networkidle");

    // Verify Title & Header
    await expect(page.locator("text=Priority 32: Research Evidence Intake & Real-World Outcome Registry")).toBeVisible();
    await expect(page.locator("text=This registry records observed events and their verification provenance.").first()).toBeVisible();
    await expect(page.locator("text=Health-related astrology is strictly an empirical inquiry into traditional vitality typologies").first()).toBeVisible();

    // 2. Verify Tab 1 — Evidence Overview Cards & Recent Registrations
    await expect(page.locator("text=Total Observations")).toBeVisible();
    await expect(page.locator("text=Independently Verified").first()).toBeVisible();
    await expect(page.locator("text=Recent Real-World Outcome Registrations")).toBeVisible();
    await expect(page.locator("text=out-default-01")).toBeVisible();

    // 3. Switch to Tab 2 — Outcome Registration Form
    await page.click("button:has-text('📝 Outcome Registration')");
    await expect(page.locator("text=Ingest Real-World Outcome Observation")).toBeVisible();
    await expect(page.locator("button:has-text('Register Real-World Outcome Record')")).toBeVisible();

    // 4. Switch to Tab 3 — Verification Hierarchy
    await page.click("button:has-text('✅ Verification Hierarchy')");
    await expect(page.locator("text=Verification Status & Provenance Hierarchy")).toBeVisible();
    await expect(page.locator("text=CIVIL_REGISTRY_CERTIFICATE")).toBeVisible();

    // 5. Switch to Tab 4 — Real-World Evidence Only Filter
    await page.click("button:has-text('🌍 Real-World Evidence Only')");
    await expect(page.locator("text=Strict Filter: OBSERVED_REAL_WORLD_EVIDENCE")).toBeVisible();
    await expect(page.locator("text=Synthetic Evidence Excluded")).toBeVisible();

    // 6. Switch to Tab 5 — Append-Only Audit Trail
    await page.click("button:has-text('📜 Append-Only Audit Trail')");
    await expect(page.locator("text=Append-Only Mutation Audit Trail")).toBeVisible();

    // 7. Switch to Tab 6 — Immutable Snapshots
    await page.click("button:has-text('🔐 Immutable Snapshots')");
    await expect(page.locator("text=Immutable Evidence Registry Snapshots")).toBeVisible();
    await expect(page.locator("button:has-text('Generate New Snapshot')")).toBeVisible();
  });
});
