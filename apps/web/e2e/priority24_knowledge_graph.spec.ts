import { test, expect } from "@playwright/test";

test.describe("Priority 24: Evidence-Weighted Research Knowledge Graph Studio", () => {
  test("loads knowledge graph studio, queries multi-domain ontology, inspects deterministic edge weights, clusters, and non-causal disclosures", async ({
    page,
  }) => {
    // 1. Visit Research Knowledge Graph Studio
    await page.goto("/research/knowledge-graph");

    // Verify Page Header
    await expect(page.locator("h1")).toContainText(
      "Priority 24: Evidence-Weighted Research Knowledge Graph"
    );

    // Verify Metric Cards
    await expect(page.locator("span:has-text('Graph Nodes')")).toBeVisible();
    await expect(page.locator("span:has-text('Weighted Edges')")).toBeVisible();
    await expect(page.locator("span:has-text('Hypothesis Clusters')")).toBeVisible();
    await expect(page.locator("span:has-text('Epistemic Status')")).toBeVisible();
    await expect(page.locator("text=100% NON-CAUSAL")).toBeVisible();

    // 2. Query Research Knowledge Graph
    const queryBtn = page.locator("button:has-text('Query Research Knowledge Graph')");
    await expect(queryBtn).toBeVisible();
    await queryBtn.click();

    // 3. Inspect Topology Tab
    await expect(page.locator("text=Guru (Jupiter)").first()).toBeVisible();
    await expect(page.locator("text=7th House (Kalatra Bhava)").first()).toBeVisible();

    // 4. Switch to Evidence-Weighted Edges Tab
    await page.click("button:has-text('Evidence-Weighted Edges')");
    await expect(page.locator("th:has-text('Source Node')")).toBeVisible();
    await expect(page.locator("th:has-text('Relationship')")).toBeVisible();
    await expect(page.locator("th:has-text('Weight (W)')")).toBeVisible();
    await expect(page.locator("text=Deterministic Closed-Form Weighting")).toBeVisible();

    // 5. Switch to Cross-Hypothesis Clusters Tab
    await page.click("button:has-text('Cross-Hypothesis Clusters')");
    await expect(page.locator("text=Cluster ID: chc-marriage-timing-01")).toBeVisible();

    // 6. Switch to Multi-Technique Interactions Tab
    await page.click("button:has-text('Multi-Technique Interactions')");
    await expect(page.locator("text=OBSERVED_POSITIVE_CONFLUENCE").first()).toBeVisible();

    // 7. Switch to Epistemic & Non-Causal Tab
    await page.click("button:has-text('Non-Causal Epistemic Disclosure')");
    await expect(page.locator("text=Strict Epistemic & Non-Causal Boundary Declarations")).toBeVisible();
    await expect(page.locator("text=Zero Physical Causality Claims (`is_causal_claimed: False`)")).toBeVisible();
  });
});
