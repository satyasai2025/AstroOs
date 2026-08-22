import fs from 'fs';
import path from 'path';
import type { AxeResults, Result } from 'axe-core';

export interface PageScanRecord {
  stepName: string;
  url: string;
  timestamp: string;
  status: 'passed' | 'failed' | 'error';
  errorMessage?: string;
  violationCount: number;
  violations: Array<{
    id: string;
    impact: string | null | undefined;
    description: string;
    help: string;
    helpUrl: string;
    affectedNodes: number;
    nodes: Array<{ html: string; target: string[] }>;
  }>;
}

export class AccessibilityReporter {
  private scans: PageScanRecord[] = [];
  private outputDir: string;

  constructor(outputDir: string = './accessibility-reports') {
    this.outputDir = outputDir;
  }

  public recordSuccess(stepName: string, url: string, results: AxeResults) {
    this.scans.push({
      stepName,
      url,
      timestamp: new Date().toISOString(),
      status: results.violations.length === 0 ? 'passed' : 'failed',
      violationCount: results.violations.length,
      violations: results.violations.map((v: Result) => ({
        id: v.id,
        impact: v.impact,
        description: v.description,
        help: v.help,
        helpUrl: v.helpUrl,
        affectedNodes: v.nodes.length,
        nodes: v.nodes.map((n) => ({
          html: n.html,
          target: n.target.map(String),
        })),
      })),
    });
  }

  public recordError(stepName: string, url: string, error: Error) {
    this.scans.push({
      stepName,
      url,
      timestamp: new Date().toISOString(),
      status: 'error',
      errorMessage: error.message,
      violationCount: 0,
      violations: [],
    });
  }

  public generateReport() {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }

    const totalSteps = this.scans.length;
    const passedSteps = this.scans.filter((s) => s.status === 'passed').length;
    const stepsWithViolations = this.scans.filter((s) => s.status === 'failed').length;
    const erroredSteps = this.scans.filter((s) => s.status === 'error').length;
    const totalViolations = this.scans.reduce((sum, s) => sum + s.violationCount, 0);

    // Save JSON
    const jsonPath = path.join(this.outputDir, 'axe-report.json');
    fs.writeFileSync(jsonPath, JSON.stringify(this.scans, null, 2), 'utf-8');

    // Build Step Cards HTML
    const stepCardsHtml = this.scans
      .map((scan) => {
        let bodyHtml = '';
        if (scan.status === 'error') {
          bodyHtml = `<p style="color: #ef4444;"><strong>Execution Error:</strong> ${scan.errorMessage}</p>`;
        } else if (scan.violations.length === 0) {
          bodyHtml = `<p style="color: #10b981;">✓ 0 accessibility violations found.</p>`;
        } else {
          bodyHtml = scan.violations
            .map((v) => {
              const nodesHtml = v.nodes
                .slice(0, 3)
                .map((n) => `<pre>Target: ${n.target.join(' ')}\nHTML: ${escapeHtml(n.html)}</pre>`)
                .join('');
              return `
                <div class="violation">
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>${escapeHtml(v.help)} (<code>${escapeHtml(v.id)}</code>)</strong>
                    <span class="badge badge-impact-${v.impact || 'minor'}">${v.impact || 'minor'}</span>
                  </div>
                  <p style="margin: 0.4rem 0; font-size: 0.9rem;">${escapeHtml(v.description)} <a href="${v.helpUrl}" target="_blank" style="color: #38bdf8;">More info</a></p>
                  <p style="font-size: 0.8rem; color: #94a3b8;">Affected nodes (${v.affectedNodes}):</p>
                  ${nodesHtml}
                </div>
              `;
            })
            .join('');
        }

        return `
          <div class="step-card">
            <div class="step-header">
              <div>
                <strong>${escapeHtml(scan.stepName)}</strong>
                <span style="color: #94a3b8; font-size: 0.85rem; margin-left: 0.75rem;">${escapeHtml(scan.url)}</span>
              </div>
              <span class="badge badge-${scan.status}">${scan.status}</span>
            </div>
            <div class="step-body">
              ${bodyHtml}
            </div>
          </div>
        `;
      })
      .join('\n');

    // Save HTML Report
    const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AstroOS Accessibility & Test Audit Report</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0b0f19; color: #e2e8f0; margin: 0; padding: 2rem; }
    .container { max-width: 1200px; margin: auto; }
    h1 { color: #f8fafc; font-size: 1.8rem; margin-bottom: 0.5rem; }
    .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1.5rem 0; }
    .card { background: #131b2e; border-radius: 8px; padding: 1.25rem; border: 1px solid #1e293b; }
    .card .val { font-size: 2rem; font-weight: bold; margin-top: 0.5rem; }
    .card.pass .val { color: #10b981; }
    .card.fail .val { color: #f59e0b; }
    .card.err .val { color: #ef4444; }
    .step-card { background: #131b2e; border-radius: 8px; margin-bottom: 1rem; border: 1px solid #1e293b; overflow: hidden; }
    .step-header { padding: 1rem; background: #1e293b; display: flex; justify-content: space-between; align-items: center; }
    .step-body { padding: 1rem; }
    .badge { padding: 0.25rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    .badge-passed { background: #065f46; color: #34d399; }
    .badge-failed { background: #78350f; color: #fbbf24; }
    .badge-error { background: #7f1d1d; color: #f87171; }
    .badge-impact-critical { background: #b91c1c; color: #fee2e2; }
    .badge-impact-serious { background: #c2410c; color: #ffedd5; }
    .badge-impact-moderate { background: #b45309; color: #fef3c7; }
    .badge-impact-minor { background: #374151; color: #e5e7eb; }
    .violation { background: #0b0f19; border-radius: 6px; padding: 0.75rem; margin-top: 0.5rem; border-left: 4px solid #f59e0b; }
    code { background: #020617; padding: 0.2rem 0.4rem; border-radius: 4px; font-size: 0.85rem; color: #93c5fd; }
    pre { background: #020617; padding: 0.75rem; border-radius: 6px; overflow-x: auto; font-size: 0.8rem; color: #f1f5f9; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🪐 AstroOS — Accessibility & Flow Audit Report</h1>
    <p style="color: #94a3b8;">Generated on ${new Date().toLocaleString()}</p>

    <div class="summary-cards">
      <div class="card"><div class="label">Total Scanned Steps</div><div class="val">${totalSteps}</div></div>
      <div class="card pass"><div class="label">Clean / Passed</div><div class="val">${passedSteps}</div></div>
      <div class="card fail"><div class="label">Steps with Violations</div><div class="val">${stepsWithViolations}</div></div>
      <div class="card err"><div class="label">Errors / Crashes</div><div class="val">${erroredSteps}</div></div>
      <div class="card"><div class="label">Total A11y Violations</div><div class="val">${totalViolations}</div></div>
    </div>

    <h2>Step by Step Results</h2>
    ${stepCardsHtml}
  </div>
</body>
</html>`;

    const htmlPath = path.join(this.outputDir, 'axe-report.html');
    fs.writeFileSync(htmlPath, htmlContent, 'utf-8');

    console.log(`\n======================================================`);
    console.log(`📊 ACCESSIBILITY & TEST AUDIT COMPLETE`);
    console.log(`- Total Steps Tested : ${totalSteps}`);
    console.log(`- A11y Clean Steps   : ${passedSteps}`);
    console.log(`- Steps w/ Warnings  : ${stepsWithViolations}`);
    console.log(`- Failed/Error Steps : ${erroredSteps}`);
    console.log(`- Reports Saved At   : ${path.resolve(this.outputDir)}`);
    console.log(`  HTML Report: ${path.resolve(htmlPath)}`);
    console.log(`  JSON Report: ${path.resolve(jsonPath)}`);
    console.log(`======================================================\n`);
  }
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
