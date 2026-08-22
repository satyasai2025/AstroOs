const { chromium } = require('playwright');
const AxeBuilder = require('@axe-core/playwright').default;
const fs = require('fs');
const path = require('path');

const START_URL = process.argv[2] || 'http://localhost:3000/';
const MAX_PAGES = parseInt(process.argv[3] || '50', 10);
const OUTPUT_DIR = path.resolve(__dirname, '../reports');

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

async function runAccessibilityScan() {
  console.log(`\n🚀 Starting Axe Accessibility Crawler & Scanner`);
  console.log(`🌐 Base URL: ${START_URL}`);
  console.log(`📄 Max Pages limit: ${MAX_PAGES}\n`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 }
  });
  const page = await context.newPage();

  const baseUrlObj = new URL(START_URL);
  const queue = [START_URL];
  const visited = new Set();
  const resultsByPage = [];
  const allViolationsMap = new Map(); // id -> { description, help, helpUrl, impact, count, occurrences }

  let pageCount = 0;

  while (queue.length > 0 && pageCount < MAX_PAGES) {
    const currentUrl = queue.shift();
    const normalizedUrl = normalizeUrl(currentUrl);

    if (visited.has(normalizedUrl)) {
      continue;
    }
    visited.add(normalizedUrl);
    pageCount++;

    console.log(`[${pageCount}/${MAX_PAGES}] Scanning: ${currentUrl}`);

    try {
      await page.goto(currentUrl, { waitUntil: 'networkidle', timeout: 30000 }).catch(async () => {
        await page.goto(currentUrl, { waitUntil: 'domcontentloaded', timeout: 15000 });
      });

      // Give dynamic components / react hydration 1 second to settle
      await page.waitForTimeout(1000);

      // Collect internal links
      const hrefs = await page.$$eval('a[href]', (anchors) => anchors.map(a => a.href));
      for (const href of hrefs) {
        try {
          const parsed = new URL(href);
          if (parsed.origin === baseUrlObj.origin) {
            const clean = normalizeUrl(parsed.href);
            // filter out file downloads, static assets, etc.
            if (!visited.has(clean) && !queue.includes(parsed.href) && !isStaticAsset(clean)) {
              queue.push(parsed.href);
            }
          }
        } catch (e) {
          // ignore invalid urls
        }
      }

      // Run Axe analysis
      const axeResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice'])
        .analyze();

      const pageViolations = axeResults.violations;
      const pagePasses = axeResults.passes.length;
      const pageInapplicable = axeResults.inapplicable.length;

      console.log(`   ↳ Found ${pageViolations.length} violation(s) (${pagePasses} passes)`);

      resultsByPage.push({
        url: currentUrl,
        title: await page.title(),
        violationsCount: pageViolations.length,
        passesCount: pagePasses,
        violations: pageViolations
      });

      // Aggregate violations
      for (const v of pageViolations) {
        if (!allViolationsMap.has(v.id)) {
          allViolationsMap.set(v.id, {
            id: v.id,
            impact: v.impact || 'minor',
            description: v.description,
            help: v.help,
            helpUrl: v.helpUrl,
            tags: v.tags,
            pagesCount: 0,
            nodesCount: 0,
            pages: []
          });
        }
        const item = allViolationsMap.get(v.id);
        item.pagesCount += 1;
        item.nodesCount += v.nodes.length;
        item.pages.push({
          url: currentUrl,
          nodes: v.nodes.map(n => ({
            html: n.html,
            target: n.target,
            failureSummary: n.failureSummary
          }))
        });
      }

    } catch (err) {
      console.error(`   ❌ Failed to scan ${currentUrl}: ${err.message}`);
    }
  }

  await browser.close();

  // Summary stats
  const totalViolationsNodes = Array.from(allViolationsMap.values()).reduce((acc, v) => acc + v.nodesCount, 0);
  const severityCounts = { critical: 0, serious: 0, moderate: 0, minor: 0 };

  for (const v of allViolationsMap.values()) {
    const impact = v.impact || 'minor';
    severityCounts[impact] = (severityCounts[impact] || 0) + v.nodesCount;
  }

  console.log('\n=============================================');
  console.log('🏁 ACCESSIBILITY SCAN SUMMARY');
  console.log('=============================================');
  console.log(`Pages Scanned:      ${resultsByPage.length}`);
  console.log(`Total Violations:   ${totalViolationsNodes} element instances`);
  console.log(`  - 🔴 Critical:    ${severityCounts.critical}`);
  console.log(`  - 🟠 Serious:     ${severityCounts.serious}`);
  console.log(`  - 🟡 Moderate:    ${severityCounts.moderate}`);
  console.log(`  - 🔵 Minor:       ${severityCounts.minor}`);
  console.log('=============================================\n');

  // Generate JSON Report
  const jsonReportPath = path.join(OUTPUT_DIR, 'axe_scan_report.json');
  fs.writeFileSync(jsonReportPath, JSON.stringify({
    scanDate: new Date().toISOString(),
    startUrl: START_URL,
    pagesScanned: resultsByPage.length,
    summary: severityCounts,
    totalIssues: totalViolationsNodes,
    ruleSummary: Array.from(allViolationsMap.values()),
    pages: resultsByPage
  }, null, 2));

  // Generate HTML Report
  const htmlReportPath = path.join(OUTPUT_DIR, 'axe_scan_report.html');
  const htmlContent = generateHtmlReport({
    scanDate: new Date().toLocaleString(),
    startUrl: START_URL,
    pagesScanned: resultsByPage.length,
    summary: severityCounts,
    totalIssues: totalViolationsNodes,
    ruleSummary: Array.from(allViolationsMap.values()),
    pages: resultsByPage
  });
  fs.writeFileSync(htmlReportPath, htmlContent);

  console.log(`📄 Reports saved:`);
  console.log(`   HTML: ${htmlReportPath}`);
  console.log(`   JSON: ${jsonReportPath}\n`);
}

function normalizeUrl(urlStr) {
  try {
    const u = new URL(urlStr);
    u.hash = '';
    return u.toString().replace(/\/$/, '');
  } catch (e) {
    return urlStr;
  }
}

function isStaticAsset(urlStr) {
  return /\.(png|jpg|jpeg|gif|svg|ico|css|js|woff|woff2|ttf|pdf|zip|mp4|webm)$/i.test(urlStr);
}

function generateHtmlReport(data) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Axe Accessibility Scan Report - ${escapeHtml(data.startUrl)}</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --critical: #ef4444;
      --serious: #f97316;
      --moderate: #eab308;
      --minor: #3b82f6;
      --pass: #22c55e;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 24px;
      line-height: 1.5;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
    }
    header {
      border-bottom: 1px solid var(--border);
      padding-bottom: 20px;
      margin-bottom: 24px;
    }
    h1 {
      margin: 0 0 8px 0;
      font-size: 26px;
      color: #38bdf8;
    }
    .meta {
      color: var(--text-muted);
      font-size: 14px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      text-align: center;
    }
    .stat-val {
      font-size: 32px;
      font-weight: 700;
      margin-top: 4px;
    }
    .badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }
    .badge.critical { background: rgba(239, 68, 68, 0.2); color: var(--critical); border: 1px solid var(--critical); }
    .badge.serious { background: rgba(249, 115, 22, 0.2); color: var(--serious); border: 1px solid var(--serious); }
    .badge.moderate { background: rgba(234, 179, 8, 0.2); color: var(--moderate); border: 1px solid var(--moderate); }
    .badge.minor { background: rgba(59, 130, 246, 0.2); color: var(--minor); border: 1px solid var(--minor); }

    .section-title {
      font-size: 20px;
      margin: 28px 0 16px 0;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .issue-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      margin-bottom: 16px;
      padding: 18px;
    }
    .issue-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
    }
    .issue-title {
      font-size: 16px;
      font-weight: 600;
      color: #fff;
    }
    .issue-desc {
      color: var(--text-muted);
      font-size: 14px;
      margin: 6px 0 12px 0;
    }
    .node-box {
      background: #090d16;
      border: 1px solid #1e293b;
      border-radius: 6px;
      padding: 12px;
      margin-top: 10px;
      font-size: 13px;
      font-family: monospace;
      overflow-x: auto;
    }
    .node-selector {
      color: #38bdf8;
      font-weight: 600;
      margin-bottom: 4px;
    }
    .node-html {
      color: #fca5a5;
      white-space: pre-wrap;
      word-break: break-all;
    }
    .node-summary {
      color: #cbd5e1;
      font-size: 12px;
      margin-top: 6px;
      font-family: sans-serif;
    }
    a.help-link {
      color: #38bdf8;
      text-decoration: none;
      font-size: 13px;
    }
    a.help-link:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🛡️ Axe Accessibility Scan Report</h1>
      <div class="meta">
        <strong>Target:</strong> ${escapeHtml(data.startUrl)} | 
        <strong>Date:</strong> ${escapeHtml(data.scanDate)} | 
        <strong>Pages Scanned:</strong> ${data.pagesScanned}
      </div>
    </header>

    <div class="grid">
      <div class="stat-card">
        <div class="badge critical">Critical</div>
        <div class="stat-val" style="color: var(--critical)">${data.summary.critical || 0}</div>
      </div>
      <div class="stat-card">
        <div class="badge serious">Serious</div>
        <div class="stat-val" style="color: var(--serious)">${data.summary.serious || 0}</div>
      </div>
      <div class="stat-card">
        <div class="badge moderate">Moderate</div>
        <div class="stat-val" style="color: var(--moderate)">${data.summary.moderate || 0}</div>
      </div>
      <div class="stat-card">
        <div class="badge minor">Minor</div>
        <div class="stat-val" style="color: var(--minor)">${data.summary.minor || 0}</div>
      </div>
    </div>

    <div class="section-title">⚠️ Accessibility Violations by Rule (${data.ruleSummary.length} rules violated)</div>

    ${data.ruleSummary.length === 0 ? '<p style="color: var(--pass);">🎉 No accessibility violations found!</p>' : ''}

    ${data.ruleSummary.map(rule => `
      <div class="issue-card">
        <div class="issue-header">
          <div>
            <span class="badge ${rule.impact}">${rule.impact}</span>
            <span class="issue-title" style="margin-left: 8px;">${escapeHtml(rule.help)} (<code>${escapeHtml(rule.id)}</code>)</span>
          </div>
          <div>
            <a class="help-link" href="${rule.helpUrl}" target="_blank" rel="noopener">Learn more ↗</a>
          </div>
        </div>
        <div class="issue-desc">${escapeHtml(rule.description)}</div>
        <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 8px;">
          Found on <strong>${rule.pagesCount}</strong> page(s) (<strong>${rule.nodesCount}</strong> total affected element(s))
        </div>

        <details>
          <summary style="cursor: pointer; color: #38bdf8; font-size: 13px; margin-bottom: 8px;">View affected elements</summary>
          ${rule.pages.map(page => `
            <div style="margin-top: 8px;">
              <div style="font-size: 13px; font-weight: 600; color: #94a3b8;">Page: <code>${escapeHtml(page.url)}</code></div>
              ${page.nodes.map(node => `
                <div class="node-box">
                  <div class="node-selector">${escapeHtml(node.target.join(' > '))}</div>
                  <div class="node-html">${escapeHtml(node.html)}</div>
                  ${node.failureSummary ? `<div class="node-summary">${escapeHtml(node.failureSummary)}</div>` : ''}
                </div>
              `).join('')}
            </div>
          `).join('')}
        </details>
      </div>
    `).join('')}

    <div class="section-title">📄 Scanned Pages Breakdown (${data.pages.length} pages)</div>
    <div class="issue-card">
      <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
        <thead>
          <tr style="text-align: left; border-bottom: 1px solid var(--border); color: var(--text-muted);">
            <th style="padding: 8px;">Page Title / URL</th>
            <th style="padding: 8px; text-align: center;">Violations</th>
            <th style="padding: 8px; text-align: center;">Passes</th>
          </tr>
        </thead>
        <tbody>
          ${data.pages.map(p => `
            <tr style="border-bottom: 1px solid #1e293b;">
              <td style="padding: 10px 8px;">
                <div style="font-weight: 600; color: #fff;">${escapeHtml(p.title || 'Untitled')}</div>
                <div style="font-size: 12px; color: var(--text-muted);">${escapeHtml(p.url)}</div>
              </td>
              <td style="padding: 8px; text-align: center; color: ${p.violationsCount > 0 ? 'var(--critical)' : 'var(--pass)'}; font-weight: 600;">
                ${p.violationsCount}
              </td>
              <td style="padding: 8px; text-align: center; color: var(--pass); font-weight: 600;">
                ${p.passesCount}
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>`;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

runAccessibilityScan().catch(err => {
  console.error('Fatal error during accessibility scan:', err);
  process.exit(1);
});
