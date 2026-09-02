/**
 * AstroOS — Scholar Consultation Dossier PDF Generator
 * =====================================================
 * Generates an executive, print-ready, high-resolution Shastric Consultation PDF dossier.
 * Uses resilient Blob ObjectURL navigation with interactive print controls.
 */

export interface ConsultationPdfData {
  native_name?: string;
  domain?: string;
  scan_horizon?: string;
  timeline_summary?: {
    total_windows_scanned?: number;
    pratyaksha_events_count?: number;
    latent_potential_count?: number;
    transient_triggers_count?: number;
  };
  varga_fusion?: {
    overall_varga_harmony?: number;
    fused_domain_scores?: Record<string, number>;
    bhavottama_planets?: string[];
    vargottama_planets?: string[];
  };
  sudarshana_chakra?: {
    lagna_rashi?: string;
    moon_rashi?: string;
    sun_rashi?: string;
    tri_fold_harmony_score?: number;
    current_scd?: {
      age_years?: number;
      active_house?: number;
      primary_theme?: string;
      significations?: string[];
    };
  };
  bhrigu_bindu?: {
    rashi?: string;
    rashi_degree?: number;
    nakshatra?: string;
    pada?: number;
    house_from_lagna?: number;
    transit_date?: string;
    activation_status?: string;
    planets_conjunct?: string[];
    planets_aspecting?: string[];
  };
  sarvato_bhadra_chakra?: {
    janma_nakshatra?: string;
    overall_transit_shield?: string;
    sbc_composite_score?: number;
    nadi_afflictions?: Record<
      string,
      {
        nakshatra?: string;
        status?: string;
      }
    >;
  };
  arudha_padas?: {
    AL?: { house: number; rashi: string; name: string };
    UL?: { house: number; rashi: string; name: string };
    A10?: { house: number; rashi: string; name: string };
  };
  decision_timeline?: Array<{
    window_start: string;
    window_end: string;
    mahadasha: string;
    antardasha: string;
    probability?: number;
    decision_tier: string;
    verdict?: string;
    explanation_hi?: string;
    explanation_en?: string;
    sav_10th_bindus?: number;
    double_transit?: boolean;
    is_bhavottama_active?: boolean;
    scd_annual_house?: number;
    confluence_level?: string;
    chara_dasha_rashi?: string;
    confluence_synthesis_hi?: string;
    confluence_synthesis_en?: string;
    empirical_match?: {
      is_matched?: boolean;
      evidence_badge?: string;
      sample_size?: number;
      lift_ratio?: number;
      confidence_percentage?: number;
      pattern_description?: string;
    };
  }>;
  executive_story?: {
    headline?: string;
    act_1_blueprint?: string;
    act_2_current_phase?: string;
    act_3_golden_roadmap?: string;
    dos?: string[];
    donts?: string[];
    empirical_validation_summary?: string;
  };
  triple_dasha_confluence?: {
    confluence_level?: string;
    confluence_score?: number;
    is_infallible_landmark?: boolean;
    vimshottari_md?: string;
    vimshottari_ad?: string;
    scd_active_house?: number;
    chara_dasha_rashi?: string;
    synthesis_hi?: string;
    synthesis_en?: string;
  };
}

function escapeHtml(value: string | number | undefined | null): string {
  if (value === undefined || value === null) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function buildConsultationDossierHtml(
  data: ConsultationPdfData,
  lang: "hi" | "en" = "en"
): string {
  const isHi = lang === "hi";
  const timeline = data.decision_timeline || [];

  const pratyakshaCount =
    data.timeline_summary?.pratyaksha_events_count ??
    timeline.filter((w) => w.decision_tier === "PRATYAKSHA_PHALA").length;
  const sushuptaCount =
    data.timeline_summary?.latent_potential_count ??
    timeline.filter((w) => w.decision_tier === "SUSHUPTA_BEEJA").length;
  const alpaCount =
    data.timeline_summary?.transient_triggers_count ??
    timeline.filter((w) => w.decision_tier === "ALPA_PHALA").length;

  const transitShield =
    data.sarvato_bhadra_chakra?.overall_transit_shield || "BALANCED";

  const timelineRows = timeline
    .map((win) => {
      const isPratyaksha = win.decision_tier === "PRATYAKSHA_PHALA";
      const isSushupta = win.decision_tier === "SUSHUPTA_BEEJA";
      const isAlpa = win.decision_tier === "ALPA_PHALA";

      const badgeColor = isPratyaksha
        ? "#059669"
        : isSushupta
        ? "#2563eb"
        : isAlpa
        ? "#d97706"
        : "#64748b";

      const tierLabel = isPratyaksha
        ? isHi
          ? "प्रत्यक्ष फल (Landmark)"
          : "Pratyaksha Phala"
        : isSushupta
        ? isHi
          ? "सुषुप्त बीज (Latent Seed)"
          : "Sushupta Beeja"
        : isAlpa
        ? isHi
          ? "अल्प फल (Minor Trigger)"
          : "Alpa Phala"
        : isHi
        ? "सामान्य काल"
        : "Samanya Kal";

      const probPercent =
        typeof win.probability === "number"
          ? win.probability <= 1.0
            ? Math.round(win.probability * 100)
            : Math.round(win.probability)
          : 75;

      const verdictText = win.explanation_en || win.explanation_hi || win.verdict || "Conducive period";

      const winStart = win.window_start ? win.window_start.slice(0, 10) : "";
      const winEnd = win.window_end ? win.window_end.slice(0, 10) : "";

      return `
      <tr style="border-bottom: 1px solid #e2e8f0; page-break-inside: avoid;">
        <td style="padding: 10px 8px; vertical-align: top; width: 22%;">
          <div style="font-weight: 700; font-size: 12px; color: #0f172a;">${escapeHtml(win.mahadasha)} &rarr; ${escapeHtml(win.antardasha)}</div>
          <div style="font-size: 10px; color: #64748b; margin-top: 2px;">${escapeHtml(winStart)} to ${escapeHtml(winEnd)}</div>
          <div style="font-size: 9px; color: #0284c7; margin-top: 2px; font-weight: 600;">10H SAV: ${win.sav_10th_bindus ?? 28} | ${win.double_transit ? "✓ Double Transit" : "—"}</div>
        </td>
        <td style="padding: 10px 8px; vertical-align: top; width: 22%;">
          <span style="display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; color: #fff; background-color: ${badgeColor};">
            ${tierLabel}
          </span>
          <div style="font-size: 11px; font-weight: 700; color: #0f172a; margin-top: 4px;">
            ${probPercent}% Probability
          </div>
          ${win.is_bhavottama_active ? `<span style="display: inline-block; font-size: 9px; background: #fef3c7; color: #92400e; padding: 1px 4px; border-radius: 3px; font-weight: 700; margin-top: 2px;">⭐ Bhāvottama</span>` : ""}
        </td>
        <td style="padding: 10px 8px; vertical-align: top; width: 56%; font-size: 11px; line-height: 1.5; color: #334155;">
          ${escapeHtml(verdictText)}
        </td>
      </tr>
      `;
    })
    .join("");

  const domainScoresHtml = data.varga_fusion?.fused_domain_scores
    ? Object.entries(data.varga_fusion.fused_domain_scores)
        .map(([dom, sc]) => {
          const scoreNum = typeof sc === "number" ? sc : 0;
          return `
          <div style="flex: 1; min-width: 100px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px; text-align: center;">
            <div style="font-size: 10px; text-transform: uppercase; font-weight: 700; color: #64748b;">${escapeHtml(dom)}</div>
            <div style="font-size: 14px; font-weight: 800; color: ${scoreNum >= 0 ? "#059669" : "#dc2626"}; margin-top: 2px;">
              ${scoreNum >= 0 ? `+${scoreNum.toFixed(2)}` : scoreNum.toFixed(2)}
            </div>
          </div>
          `;
        })
        .join("")
    : "";

  return `<!DOCTYPE html>
<html lang="${lang}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AstroOS Shastric Consultation Report — ${escapeHtml(data.native_name || "Native")}</title>
  <style>
    @page {
      size: A4;
      margin: 12mm 15mm 12mm 15mm;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: #0f172a;
      background: #ffffff;
      margin: 0;
      padding: 20px;
      font-size: 11px;
      line-height: 1.4;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
      max-width: 800px;
      margin: 0 auto;
    }
    .no-print-toolbar {
      background: #0f172a;
      color: #f8fafc;
      padding: 10px 16px;
      border-radius: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .print-btn {
      background: #f59e0b;
      color: #0f172a;
      border: none;
      padding: 8px 16px;
      font-weight: 800;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12px;
      transition: all 0.2s ease;
    }
    .print-btn:hover {
      background: #d97706;
      transform: scale(1.02);
    }
    .header-box {
      border-bottom: 2px solid #0f172a;
      padding-bottom: 12px;
      margin-bottom: 16px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }
    .title {
      font-size: 20px;
      font-weight: 900;
      color: #0f172a;
      letter-spacing: -0.5px;
      margin: 0;
    }
    .subtitle {
      font-size: 10px;
      color: #64748b;
      margin-top: 3px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-weight: 600;
    }
    .section-title {
      font-size: 12px;
      font-weight: 800;
      color: #0f172a;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 1.5px solid #cbd5e1;
      padding-bottom: 4px;
      margin-top: 18px;
      margin-bottom: 10px;
    }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin-bottom: 14px;
    }
    .summary-card {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 8px;
      text-align: center;
    }
    .summary-label {
      font-size: 9px;
      font-weight: 700;
      color: #64748b;
      text-transform: uppercase;
    }
    .summary-val {
      font-size: 16px;
      font-weight: 900;
      color: #0f172a;
      margin-top: 2px;
    }
    table.data-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
    }
    table.data-table th {
      background: #f1f5f9;
      color: #334155;
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      text-align: left;
      padding: 8px;
      border-bottom: 1.5px solid #cbd5e1;
    }
    .footer-box {
      margin-top: 24px;
      border-top: 1px solid #e2e8f0;
      padding-top: 8px;
      display: flex;
      justify-content: space-between;
      font-size: 9px;
      color: #94a3b8;
    }
    @media print {
      .no-print-toolbar {
        display: none !important;
      }
      body {
        padding: 0;
      }
    }
  </style>
  <script>
    window.addEventListener("DOMContentLoaded", function() {
      // Auto-focus and trigger print dialog
      setTimeout(function() {
        window.focus();
        window.print();
      }, 400);
    });
  </script>
</head>
<body>

  <!-- Floating Print Bar for Browsers -->
  <div class="no-print-toolbar">
    <div>
      <strong>AstroOS Scholar Dossier</strong> — Click "Save as PDF" in the print dialog.
    </div>
    <button class="print-btn" onclick="window.print()">
      🖨️ Print / Save as PDF
    </button>
  </div>

  <!-- Header -->
  <div class="header-box">
    <div>
      <h1 class="title">Shastric Life Consultation Report</h1>
      <div class="subtitle">AstroOS Classical Autonomous Engine &bull; Horizon: ${escapeHtml(data.scan_horizon || "Life Horizon")}</div>
    </div>
    <div style="text-align: right;">
      <div style="font-size: 14px; font-weight: 800; color: #0f172a;">${escapeHtml(data.native_name || "Native Profile")}</div>
      <div style="font-size: 10px; color: #64748b;">Domain: ${escapeHtml(data.domain || "career").toUpperCase()}</div>
    </div>
  </div>

  <!-- Summary Cards -->
  <div class="summary-grid">
    <div class="summary-card" style="border-left: 3px solid #059669;">
      <div class="summary-label" style="color: #059669;">Pratyaksha Phala</div>
      <div class="summary-val">${pratyakshaCount}</div>
    </div>
    <div class="summary-card" style="border-left: 3px solid #2563eb;">
      <div class="summary-label" style="color: #2563eb;">Sushupta Beeja</div>
      <div class="summary-val">${sushuptaCount}</div>
    </div>
    <div class="summary-card" style="border-left: 3px solid #d97706;">
      <div class="summary-label" style="color: #d97706;">Alpa Phala</div>
      <div class="summary-val">${alpaCount}</div>
    </div>
    <div class="summary-card" style="border-left: 3px solid #0284c7;">
      <div class="summary-label" style="color: #0284c7;">SBC Transit Shield</div>
      <div class="summary-val" style="font-size: 12px; margin-top: 4px;">${escapeHtml(transitShield)}</div>
    </div>
  </div>

  <!-- Executive Life Story Section (Grounded Plain English Narrative) -->
  ${
    data.executive_story
      ? `
  <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px 14px; margin-bottom: 14px; page-break-inside: avoid;">
    <div style="font-size: 12px; font-weight: 800; color: #0f172a; margin-bottom: 4px;">
      📖 ${escapeHtml(data.executive_story.headline || "Executive Life Story & Strategic Roadmap")}
    </div>
    <div style="font-size: 9.5px; color: #334155; line-height: 1.45; margin-bottom: 6px;">
      <strong>Act I (Blueprint):</strong> ${escapeHtml(data.executive_story.act_1_blueprint)}
    </div>
    <div style="font-size: 9.5px; color: #334155; line-height: 1.45; margin-bottom: 6px;">
      <strong>Act II (Current Reality):</strong> ${escapeHtml(data.executive_story.act_2_current_phase)}
    </div>
    <div style="font-size: 9.5px; color: #1e293b; line-height: 1.45;">
      <strong>Act III (Golden Milestone):</strong> ${escapeHtml(data.executive_story.act_3_golden_roadmap)}
    </div>

    <!-- Practical Action Playbook in PDF -->
    ${
      (data.executive_story.dos && data.executive_story.dos.length > 0) ||
      (data.executive_story.donts && data.executive_story.donts.length > 0)
        ? `
    <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #cbd5e1; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
      <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 6px 8px;">
        <div style="font-size: 9px; font-weight: 800; color: #166534; margin-bottom: 3px;">🟢 Recommended Strategic Actions (Do's):</div>
        <ul style="margin: 0; padding-left: 12px; font-size: 8px; color: #14532d; line-height: 1.35;">
          ${(data.executive_story.dos || []).map((d) => `<li>${escapeHtml(d)}</li>`).join("")}
        </ul>
      </div>
      <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 6px 8px;">
        <div style="font-size: 9px; font-weight: 800; color: #991b1b; margin-bottom: 3px;">🔴 Critical Pitfalls to Avoid (Don'ts):</div>
        <ul style="margin: 0; padding-left: 12px; font-size: 8px; color: #7f1d1d; line-height: 1.35;">
          ${(data.executive_story.donts || []).map((d) => `<li>${escapeHtml(d)}</li>`).join("")}
        </ul>
      </div>
    </div>
    `
        : ""
    }

    <div style="font-size: 8.5px; color: #059669; margin-top: 6px; font-style: italic;">
      ${escapeHtml(data.executive_story.empirical_validation_summary)}
    </div>
  </div>
  `
      : ""
  }

  <!-- Triple Dasha Confluence Synthesis Banner -->
  ${
    data.triple_dasha_confluence
      ? `
  <div style="background: #fdf4ff; border: 1px solid #f0abfc; border-radius: 6px; padding: 8px 12px; margin-bottom: 12px; page-break-inside: avoid;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
      <div style="font-size: 11px; font-weight: 800; color: #86198f;">
        🌟 Triple-Dasha Confluence (Triveni Sangam)
      </div>
      <span style="font-size: 9px; font-weight: 800; background: #e879f9; color: #4a044e; padding: 2px 6px; border-radius: 4px;">
        ${escapeHtml(data.triple_dasha_confluence.confluence_level || "CONFLUENCE")}
      </span>
    </div>
    <div style="font-size: 10px; color: #4c1d95; line-height: 1.4;">
      ${escapeHtml(data.triple_dasha_confluence.synthesis_en || data.triple_dasha_confluence.synthesis_hi)}
    </div>
  </div>
  `
      : ""
  }

  <!-- Tri-Lagna Sudarshana & Varga Fusion Section -->
  <div style="display: flex; gap: 12px; margin-bottom: 12px; page-break-inside: avoid;">
    <!-- Sudarshana Box -->
    ${
      data.sudarshana_chakra
        ? `
    <div style="flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px;">
      <div style="font-size: 11px; font-weight: 800; color: #0f172a; margin-bottom: 6px;">
        ☸️ Sudarshana Chakra Tri-Lagna
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 10px; margin-bottom: 4px;">
        <span>Lagna (LK): <strong>${escapeHtml(data.sudarshana_chakra.lagna_rashi || "Aries")}</strong></span>
        <span>Chandra (CK): <strong>${escapeHtml(data.sudarshana_chakra.moon_rashi || "Taurus")}</strong></span>
        <span>Surya (SK): <strong>${escapeHtml(data.sudarshana_chakra.sun_rashi || "Leo")}</strong></span>
      </div>
      ${
        data.sudarshana_chakra.current_scd
          ? `
      <div style="font-size: 10px; color: #0369a1; background: #e0f2fe; padding: 4px 6px; border-radius: 4px; font-weight: 600;">
        Active SCD: House ${data.sudarshana_chakra.current_scd.active_house} (Age ${data.sudarshana_chakra.current_scd.age_years} yrs) — ${escapeHtml(data.sudarshana_chakra.current_scd.primary_theme)}
      </div>`
          : ""
      }
    </div>
    `
        : ""
    }

    <!-- Bhrigu Bindu Box -->
    ${
      data.bhrigu_bindu
        ? `
    <div style="flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px;">
      <div style="font-size: 11px; font-weight: 800; color: #0f172a; margin-bottom: 6px;">
        ⚡ Bhrigu Bindu (Destiny Trigger)
      </div>
      <div style="font-size: 10px; margin-bottom: 2px;">
        Point: <strong>${escapeHtml(data.bhrigu_bindu.rashi)} ${data.bhrigu_bindu.rashi_degree ?? 0}&deg;</strong> (${escapeHtml(data.bhrigu_bindu.nakshatra || "Ashwini")} P${data.bhrigu_bindu.pada ?? 1}) &bull; Bhava H${data.bhrigu_bindu.house_from_lagna ?? 1}
      </div>
      <div style="font-size: 10px; color: #059669; font-weight: 700;">
        Status: ${escapeHtml(data.bhrigu_bindu.activation_status || "Active")}
      </div>
    </div>
    `
        : ""
    }
  </div>

  <!-- Varga Fused Domain Scores -->
  ${
    domainScoresHtml
      ? `
  <div style="margin-bottom: 14px; page-break-inside: avoid;">
    <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 6px;">
      ${isHi ? "वर्ग-समन्वित क्षेत्र फलादेश (D1+D9+D10+D60 Signed Scores)" : "Fused Dimensional Varga Scores"}
    </div>
    <div style="display: flex; gap: 8px;">
      ${domainScoresHtml}
    </div>
  </div>
  `
      : ""
  }

  <!-- 4-Tier Life Decision Timeline Table -->
  <div class="section-title">
    ${isHi ? "4-स्तरीय शास्त्रीय निर्णय टाइमलाइन (Life Decision Timeline)" : "4-Tier Supervisory Life Decision Timeline"}
  </div>

  <table class="data-table">
    <thead>
      <tr>
        <th>${isHi ? "दशा एवं कालखंड" : "Dasha Period"}</th>
        <th>${isHi ? "निर्णय स्तर एवं संभावना" : "Decision Tier & Probability"}</th>
        <th>${isHi ? "शास्त्रीय फलादेश एवं विश्लेषण" : "Shastric Actionable Verdict"}</th>
      </tr>
    </thead>
    <tbody>
      ${timelineRows}
    </tbody>
  </table>

  <!-- Footer -->
  <div class="footer-box">
    <div>AstroOS Canonical Engine &bull; Pure Mathematical Determinism</div>
    <div>Generated on ${new Date().toISOString().slice(0, 10)}</div>
  </div>

</body>
</html>`;
}

export function exportConsultationDossierPdf(
  data: ConsultationPdfData,
  lang: "hi" | "en" = "en"
): void {
  try {
    const html = buildConsultationDossierHtml(data, lang);
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const blobUrl = URL.createObjectURL(blob);

    const printWindow = window.open(blobUrl, "_blank");
    if (!printWindow) {
      alert("Please allow pop-ups for this site to view and download the PDF report.");
      return;
    }
  } catch (err) {
    console.error("Failed to generate PDF dossier:", err);
    alert("Could not generate PDF report. Please try again.");
  }
}
