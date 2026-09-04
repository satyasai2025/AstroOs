"""
AstroOS — Responsive HTML & Text Transit Digest Email Template
==============================================================
Generates pixel-perfect, mobile-friendly HTML emails for personalized
Vedic transit updates, classical remedies, and Shastric insights.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def render_transit_digest_html(
    *,
    user_name: str,
    planet: str,
    nakshatra: str,
    rashi: str,
    rashi_dignity: str,
    date_range: str,
    ruling_planet: str,
    deity: str,
    house_number: Optional[int],
    lagna_rashi: Optional[str],
    transit_prediction: str,
    scripture_title: str,
    scripture_text: str,
    primary_mantra_sanskrit: str,
    primary_mantra_iast: str,
    mantra_instructions: str,
    symbol_insight: str,
    wisdom_warning: str,
    base_url: str = "https://astroos.internal",
    unsubscribe_url: str = "#",
) -> str:
    """Render a responsive HTML email matching the AstroOS/Cosmic Insights transit digest format."""

    house_heading = (
        f"Jupiter in your {house_number}th House ({lagna_rashi} Lagna)"
        if house_number and lagna_rashi
        else f"{planet} in {rashi} Transit Insight"
    )

    app_url = f"{base_url}/charts/transit"
    remedies_url = f"{base_url}/phalita"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{planet} in {nakshatra} Nakshatra — Your Transit Guidance</title>
  <style>
    body {{
      margin: 0;
      padding: 0;
      background-color: #f4f6fa;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: #2d3748;
      -webkit-font-smoothing: antialiased;
    }}
    .email-container {{
      max-width: 600px;
      margin: 20px auto;
      background: #ffffff;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
      border: 1px solid #e2e8f0;
    }}
    .header {{
      background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
      padding: 28px 32px;
      text-align: center;
      border-bottom: 3px solid #29b8d4;
    }}
    .brand-title {{
      color: #ffffff;
      font-size: 20px;
      font-weight: 800;
      letter-spacing: 1px;
      margin: 0;
    }}
    .brand-subtitle {{
      color: #29b8d4;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      margin-top: 4px;
      font-weight: 600;
    }}
    .content {{
      padding: 32px;
      line-height: 1.65;
      font-size: 15px;
    }}
    .salutation {{
      font-size: 18px;
      font-weight: 700;
      color: #0f172a;
      margin-bottom: 16px;
    }}
    .transit-badge {{
      display: inline-block;
      background: #ecfeff;
      border: 1px solid #a5f3fc;
      color: #0891b2;
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 16px;
    }}
    .lead-paragraph {{
      color: #334155;
      font-size: 15px;
      margin-bottom: 20px;
    }}
    .cta-btn {{
      display: inline-block;
      background: #f59e0b;
      color: #0f172a !important;
      font-weight: 700;
      font-size: 13px;
      text-decoration: none;
      padding: 10px 20px;
      border-radius: 10px;
      margin: 12px 0 24px 0;
    }}
    .section-box {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 20px;
      margin: 24px 0;
    }}
    .section-title {{
      font-size: 16px;
      font-weight: 700;
      color: #0f172a;
      margin-top: 0;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .mantra-box {{
      background: #ffffff;
      border-left: 4px solid #f59e0b;
      padding: 12px 16px;
      border-radius: 0 8px 8px 0;
      margin: 12px 0;
    }}
    .mantra-sanskrit {{
      font-size: 18px;
      font-weight: 700;
      color: #b45309;
      margin: 0 0 4px 0;
      font-family: 'Noto Serif Devanagari', Georgia, serif;
    }}
    .mantra-iast {{
      font-size: 13px;
      color: #64748b;
      font-style: italic;
      margin: 0;
    }}
    .footer {{
      background: #090d16;
      color: #94a3b8;
      padding: 36px 32px;
      text-align: center;
      font-size: 12px;
    }}
    .sign-off {{
      font-size: 14px;
      color: #f8fafc;
      margin-bottom: 24px;
    }}
    .app-cards {{
      display: flex;
      justify-content: center;
      gap: 16px;
      margin-bottom: 24px;
    }}
    .app-card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 12px 16px;
      text-align: center;
      width: 120px;
      text-decoration: none;
      color: #ffffff;
    }}
    .app-icon {{
      font-size: 20px;
      margin-bottom: 4px;
    }}
    .app-name {{
      font-size: 11px;
      font-weight: 700;
      color: #f8fafc;
    }}
    .app-desc {{
      font-size: 9px;
      color: #94a3b8;
    }}
    .footer-links {{
      margin: 20px 0;
    }}
    .footer-links a {{
      color: #cbd5e1;
      text-decoration: none;
      margin: 0 8px;
      font-size: 12px;
    }}
    .footer-links a:hover {{
      color: #29b8d4;
    }}
    .unsubscribe-link {{
      color: #64748b;
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <div class="email-container">
    <!-- Header -->
    <div class="header">
      <h1 class="brand-title">ॐ ASTROOS</h1>
      <div class="brand-subtitle">Vedic Ephemeris & Transit Dispatch</div>
    </div>

    <!-- Content -->
    <div class="content">
      <div class="salutation">Dear {user_name},</div>

      <div class="transit-badge">
        ✦ {planet} in {nakshatra} ({rashi}) · {date_range}
      </div>

      <p class="lead-paragraph">
        <strong>{planet}</strong> is currently in transit through <strong>{nakshatra} Nakshatra</strong> ({date_range}) in the sign of <strong>{rashi}</strong> ({rashi_dignity}). {nakshatra} is ruled by <strong>{ruling_planet}</strong> and the presiding deities are the <strong>{deity}</strong>.
      </p>

      <div style="text-align: left;">
        <a href="{app_url}" class="cta-btn">View Your Predictions →</a>
      </div>

      <!-- House Specific Prediction -->
      <div class="section-box">
        <h2 class="section-title">🔮 {house_heading}</h2>
        <p style="margin: 0; color: #475569; font-size: 14px;">
          {transit_prediction}
        </p>
      </div>

      <!-- Classical Remedies -->
      <div class="section-box" style="border-left: 4px solid #29b8d4;">
        <h2 class="section-title">🪔 Remedies for {planet} in {nakshatra} Nakshatra</h2>
        
        <div style="margin-bottom: 16px;">
          <strong style="color: #0f172a; font-size: 14px;">1. {scripture_title}</strong>
          <p style="margin: 4px 0 0 0; color: #475569; font-size: 13px;">
            {scripture_text}
          </p>
        </div>

        <div>
          <strong style="color: #0f172a; font-size: 14px;">2. Chant “{primary_mantra_iast}”</strong>
          <div class="mantra-box">
            <p class="mantra-sanskrit">{primary_mantra_sanskrit}</p>
            <p class="mantra-iast">{primary_mantra_iast}</p>
          </div>
          <p style="margin: 4px 0 0 0; color: #475569; font-size: 13px;">
            {mantra_instructions}
          </p>
        </div>
      </div>

      <!-- Sacred Symbol & Caution -->
      <div style="margin: 20px 0; font-size: 14px; color: #334155;">
        <p>{symbol_insight}</p>
        <p style="background: #fffbeb; border: 1px solid #fef3c7; padding: 12px 16px; border-radius: 8px; color: #92400e;">
          💡 <strong>Wisdom Guidance:</strong> {wisdom_warning}
        </p>
      </div>

      <div style="text-align: left;">
        <a href="{remedies_url}" class="cta-btn" style="background: #0f172a; color: #ffffff !important;">Your Full Remedies in AstroOS →</a>
      </div>
    </div>

    <!-- Footer -->
    <div class="footer">
      <div class="sign-off">
        Love and light,<br>
        <strong>The AstroOS Research Team 💛</strong>
      </div>

      <!-- Ecosystem Apps -->
      <table align="center" style="margin: 0 auto 20px auto;" cellpadding="0" cellspacing="8">
        <tr>
          <td align="center" style="background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 10px 14px; width: 110px;">
            <div style="font-size: 18px;">ॐ</div>
            <div style="font-size: 11px; font-weight: bold; color: #f8fafc; margin-top: 4px;">AstroOS</div>
            <div style="font-size: 9px; color: #94a3b8;">Vedic Workstation</div>
          </td>
          <td align="center" style="background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 10px 14px; width: 110px;">
            <div style="font-size: 18px;">📜</div>
            <div style="font-size: 11px; font-weight: bold; color: #f8fafc; margin-top: 4px;">Scholar</div>
            <div style="font-size: 9px; color: #94a3b8;">Empirical Journal</div>
          </td>
          <td align="center" style="background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 10px 14px; width: 110px;">
            <div style="font-size: 18px;">🧠</div>
            <div style="font-size: 11px; font-weight: bold; color: #f8fafc; margin-top: 4px;">Phalita MoE</div>
            <div style="font-size: 9px; color: #94a3b8;">Governed AI Engine</div>
          </td>
        </tr>
      </table>

      <!-- Navigation Links -->
      <div class="footer-links">
        <a href="{base_url}/research/projects">Research</a> ·
        <a href="{base_url}/phalita">Consultations</a> ·
        <a href="{base_url}/reports/pdf">Reports</a> ·
        <a href="{base_url}/help">Documentation</a>
      </div>

      <p style="margin: 16px 0 8px 0; color: #64748b; font-size: 11px;">
        Copyright © 2026 AstroOS Computational Platform. All rights reserved.<br>
        Built with Swiss Ephemeris v2.10 & 100% Siddhantic Integrity.
      </p>

      <p style="margin: 0; font-size: 11px;">
        To no longer receive these personalized transit emails, <a href="{unsubscribe_url}" class="unsubscribe-link">unsubscribe here</a>.
      </p>
    </div>
  </div>
</body>
</html>
"""
