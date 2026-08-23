import { test, expect } from "@playwright/test";

test.describe("Priority 29: Research Benchmark Expansion Studio", () => {
  test("loads benchmark expansion studio, executes domain suites, inspects non-medical safety disclosures, and epistemic scope", async ({
    page,
  }) => {
    // 1. Visit Research Benchmark Expansion Studio
    await page.goto("/research/benchmark-expansion");

    // Verify Page Header
    await expect(page.locator("h1")).toContainText(
      "Priority 29: Research Benchmark Expansion Engine"
    );

    // Verify Epistemic Clarification Banner
    await expect(page.locator("text=EPISTEMIC SCOPE CLARIFICATION")).toBeVisible();
    await expect(page.locator("text=Mean Reproduction Accuracy")).toBeVisible();
    await expect(page.locator("span.text-xs.uppercase:has-text('Non-Medical Safety Guardrail')").first()).toBeVisible();

    // 2. Execute Benchmark Suite
    const evalBtn = page.locator("button:has-text('Execute Governed Benchmark Suite')");
    await expect(evalBtn).toBeVisible();
    await evalBtn.click();

    // 3. Inspect Domain Benchmark Suites Tab
    await expect(page.locator("text=BM_CAREER_D10_PROMOTION")).toBeVisible();
    await expect(page.locator("text=BM_WEALTH_DHANA_YOGA")).toBeVisible();
    await expect(page.locator("text=BM_HEALTH_VITALITY_TYPOLOGY")).toBeVisible();

    // 4. Switch to Cross-Domain Comparison Matrix Tab
    await page.click("button:has-text('Cross-Domain Comparison Matrix')");
    await expect(page.locator("text=Cross-Domain Mathematical Reproduction Matrix")).toBeVisible();
    await expect(page.locator("th:has-text('Reproduction Fidelity')")).toBeVisible();

    // 5. Switch to Non-Medical Safety Guardrails Tab
    await page.click("button:has-text('Non-Medical Safety Guardrails')");
    await expect(page.locator("text=Mandatory Non-Medical Safety Declaration")).toBeVisible();
    await expect(page.locator("text=Prohibited Terms Compliance Audit")).toBeVisible();
    await expect(page.locator("text=PROHIBITED / ABSENT").first()).toBeVisible();

    // 6. Switch to P11 Lineage & Cryptographic Provenance Tab
    await page.click("button:has-text('P11 Lineage & Cryptographic Provenance')");
    await expect(page.locator("text=P11 Cryptographic Snapshot Lineage")).toBeVisible();
    await expect(page.locator("text=Cross-Domain Report Hash")).toBeVisible();
  });
});
