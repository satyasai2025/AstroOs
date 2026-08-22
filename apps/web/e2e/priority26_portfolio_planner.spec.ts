import { test, expect } from "@playwright/test";

test.describe("Priority 26: Research Portfolio & Experiment Planner Studio", () => {
  test("loads portfolio planner studio, plans scientific experiments, inspects EvidencePriorityScores, dynamic budget matrix, and manifest", async ({
    page,
  }) => {
    // 1. Visit Research Portfolio Planner Studio
    await page.goto("/research/portfolio-planner");

    // Verify Page Header
    await expect(page.locator("h1")).toContainText(
      "Priority 26: Research Portfolio & Experiment Planner"
    );

    // Verify Metric Cards
    await expect(page.locator("text=Total Compute Budget")).toBeVisible();
    await expect(page.locator("text=Hypotheses Ranked")).toBeVisible();
    await expect(page.locator("text=Tier A Allocation")).toBeVisible();

    // 2. Generate Research Portfolio Plan
    const planBtn = page.locator("button:has-text('Generate Portfolio Plan')");
    await expect(planBtn).toBeVisible();
    await planBtn.click();

    // 3. Inspect Prioritization Leaderboard Tab
    await expect(page.locator("th:has-text('Candidate Rule')")).toBeVisible();
    await expect(page.locator("th:has-text('Formula Expression')")).toBeVisible();
    await expect(page.locator("th:has-text('EvidencePriorityScore')")).toBeVisible();

    // 4. Switch to Dynamic Budget Allocation Tab
    await page.click("button:has-text('Dynamic Budget Allocation Matrix')");
    await expect(page.locator("text=TIER A (PRIMARY TRIAL)")).toBeVisible();
    await expect(page.locator("text=TIER B (REPLICATION STUDY)")).toBeVisible();

    // 5. Switch to Pre-Registration Manifest Tab
    await page.click("button:has-text('Pre-Registration Experiment Manifest')");
    await expect(page.locator("text=Pre-Registration Experiment Execution Manifest")).toBeVisible();
    await expect(page.locator("text=Status: PRE_REGISTERED_FOR_EXECUTION")).toBeVisible();

    // 6. Switch to Non-Causal Epistemic Governance Tab
    await page.click("button:has-text('Non-Causal Epistemic Governance')");
    await expect(page.locator("text=Epistemic Scope & Information Gain Boundary Disclosures")).toBeVisible();
    await expect(page.locator("text=P11 Cryptographic Snapshot Lineage & Reproducibility")).toBeVisible();
  });
});
