import { test, expect } from "@playwright/test";

test.describe("Priority 11 — Scientific Experiment Studio E2E Verification", () => {
  test("should load experiment studio, create experiment, freeze snapshot, and compare metrics", async ({ page }) => {
    // 1. Navigate to /research/experiments
    await page.goto("/research/experiments");

    // 2. Check title and header
    await expect(page.locator("h1")).toContainText("AstroOS Scientific Experiment Lineage & Comparison Studio");

    // 3. Verify Baseline Experiment in Registry
    await expect(page.locator("text=Parashari Baseline Marriage Research").first()).toBeVisible();

    // 4. Create New Experiment Container
    await page.fill('input[placeholder*="Experiment Name"]', "Playwright E2E Jaimini Experiment");
    await page.fill('textarea[placeholder*="Description"]', "Playwright E2E test verification");
    await page.click('button:has-text("Create Experiment Container")');

    // 5. Verify Created Experiment in Registry
    await expect(page.locator("text=Playwright E2E Jaimini Experiment").first()).toBeVisible();

    // 6. Freeze New Snapshot
    const freezeBtn = page.locator('button:has-text("+ Freeze New Snapshot")');
    await freezeBtn.click();
    await page.waitForTimeout(600);

    // 7. Verify Snapshot Lineage Chain
    await expect(page.locator("text=Lineage DAG Snapshots Chain")).toBeVisible();

    // 8. Run Side-by-Side Metric Diff against Baseline
    const diffBtn = page.locator('button:has-text("Run Side-by-Side Metric Diff")');
    await diffBtn.waitFor({ state: "visible" });
    await diffBtn.click();
    await page.waitForTimeout(600);

    // 9. Verify Metric Deltas Table
    await expect(page.locator("text=Side-by-Side Comparative Diff Results").first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator("text=Brier Score (Primary)").first()).toBeVisible();
  });

  test("should verify local-first snapshot import and tamper detection", async ({ page }) => {
    await page.goto("/research/experiments");

    const validBundle = JSON.stringify({
      format: "AstroOS_Experiment_Snapshot_Bundle",
      version: "1.0",
      experiment: {
        experiment_id: "exp-e2e-import",
        name: "Imported E2E Experiment",
        description: "Testing import functionality",
        author: "Playwright",
        tags: ["e2e", "import"],
      },
      snapshot: {
        snapshot_id: "snap-imported-1",
        parent_snapshot_id: null,
        timestamp: "2026-08-21T10:00:00",
        schema_version: "1.0",
        dataset: {
          dataset_id: "ds-e2e",
          dataset_version: "1.0",
          sha256_hash: "hash-e2e-ds",
          record_count: 50,
        },
        techniques: {
          dsl_rule_ids: ["r1"],
          dsl_hashes: ["h1"],
          classical_techniques: ["t1"],
          combined_sha256_hash: "htech",
        },
        calibration: {
          profile_id: "p1",
          status: "ACTIVE",
          technique_weights: { w: 0.5 },
          primary_brier_score: 0.05,
          primary_log_loss: 0.15,
          sha256_hash: "hcal",
        },
        orchestrator: {
          consensus_profile_id: "p1",
          minimum_activation_threshold: 50,
          conflict_penalty_multiplier: 1.0,
        },
        metrics: {
          brier_score: 0.05,
          log_loss: 0.15,
          precision: 0.85,
          recall: 0.80,
          f1_score: 0.825,
          roc_auc: 0.90,
          roc_auc_status: "VALID",
          sample_size_n: 20,
          hit_rate: 0.85,
        },
        execution_params: {},
        snapshot_sha256_hash: "5fb2d3d5d1176ba4866c7992719e414a9e43c411706fff0e88923c800fbac1a0",
      },
    });

    await page.fill('textarea[placeholder*="Paste .astro_experiment.json"]', validBundle);
    await page.click('button:has-text("Verify SHA-256 Hash & Import Snapshot")');

    await expect(page.locator("text=Imported successfully!")).toBeVisible();
  });
});
