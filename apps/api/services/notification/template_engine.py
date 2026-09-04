"""
AstroOS — Transactional Email Template Engine (Phase 7)

Renders branded responsive HTML and clean plain-text bodies for all system notifications.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class RenderedEmail:
    subject: str
    html_body: str
    text_body: str


class TemplateEngine:
    """Renders transactional email templates into HTML and plain-text formats."""

    # ── Base Layouts ─────────────────────────────────────────────────────────

    @classmethod
    def _wrap_html_layout(cls, title: str, content_html: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #0d1117;
      color: #c9d1d9;
      margin: 0;
      padding: 0;
    }}
    .wrapper {{
      max-width: 600px;
      margin: 20px auto;
      background-color: #161b22;
      border: 1px solid #30363d;
      border-radius: 8px;
      overflow: hidden;
    }}
    .header {{
      background: linear-gradient(135deg, #1f2937, #111827);
      padding: 24px;
      text-align: center;
      border-bottom: 1px solid #30363d;
    }}
    .header h1 {{
      margin: 0;
      color: #58a6ff;
      font-size: 24px;
      letter-spacing: 0.5px;
    }}
    .content {{
      padding: 32px 24px;
      line-height: 1.6;
    }}
    .btn {{
      display: inline-block;
      background-color: #238636;
      color: #ffffff !important;
      text-decoration: none;
      padding: 12px 24px;
      border-radius: 6px;
      font-weight: 600;
      margin: 20px 0;
    }}
    .box {{
      background-color: #21262d;
      border: 1px solid #30363d;
      border-radius: 6px;
      padding: 16px;
      margin: 20px 0;
    }}
    .footer {{
      padding: 20px;
      text-align: center;
      font-size: 12px;
      color: #8b949e;
      border-top: 1px solid #30363d;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h1>AstroOS</h1>
    </div>
    <div class="content">
      {content_html}
    </div>
    <div class="footer">
      <p>This is a system transactional email from AstroOS.</p>
      <p>&copy; 2026 AstroOS Platform. All rights reserved.</p>
    </div>
  </div>
</body>
</html>"""

    # ── Template Renderers ───────────────────────────────────────────────────

    @classmethod
    def render(cls, template_name: str, context: Mapping[str, Any]) -> RenderedEmail:
        name = template_name.lower().strip()
        method_name = f"_render_{name}"
        renderer = getattr(cls, method_name, None)
        if renderer is None:
            raise ValueError(f"Unknown email template: '{template_name}'")
        return renderer(context)

    # 1. Payment Success
    @classmethod
    def _render_payment_success(cls, ctx: Mapping[str, Any]) -> RenderedEmail:
        amount_formatted = ctx.get("amount_formatted") or f"${(ctx.get('amount', 0) / 100):.2f}"
        plan = ctx.get("plan_name", "PRO")
        tx_id = ctx.get("transaction_id", "N/A")
        receipt_url = ctx.get("receipt_url", "#")

        subject = f"Payment Receipt: AstroOS {plan} Plan"
        html = f"""
        <h2>Payment Received</h2>
        <p>Thank you for your payment. Your subscription to <strong>AstroOS {plan}</strong> has been processed successfully.</p>
        <div class="box">
          <p><strong>Amount:</strong> {amount_formatted} {ctx.get('currency', 'USD')}</p>
          <p><strong>Plan:</strong> {plan}</p>
          <p><strong>Transaction ID:</strong> {tx_id}</p>
          <p><strong>Billing Cycle:</strong> {ctx.get('billing_cycle', 'Monthly').capitalize()}</p>
        </div>
        <p><a href="{receipt_url}" class="btn">View Receipt / Dashboard</a></p>
        """
        text = (
            f"Payment Received\n\n"
            f"Thank you for your payment. Your subscription to AstroOS {plan} has been processed successfully.\n\n"
            f"Amount: {amount_formatted} {ctx.get('currency', 'USD')}\n"
            f"Plan: {plan}\n"
            f"Transaction ID: {tx_id}\n"
            f"Receipt: {receipt_url}\n"
        )
        return RenderedEmail(subject=subject, html_body=cls._wrap_html_layout(subject, html), text_body=text)

    # 2. Payment Failed
    @classmethod
    def _render_payment_failed(cls, ctx: Mapping[str, Any]) -> RenderedEmail:
        error = ctx.get("error_message", "Card declined or insufficient funds")
        portal_url = ctx.get("portal_url", "http://localhost:3000/settings/billing")

        subject = "Payment Failed: Action Required for AstroOS Subscription"
        html = f"""
        <h2 style="color: #f85149;">Payment Unsuccessful</h2>
        <p>We were unable to process your recent subscription renewal payment for AstroOS.</p>
        <div class="box">
          <p><strong>Reason:</strong> {error}</p>
          <p><strong>Grace Period:</strong> Premium access remains active for 3 days.</p>
        </div>
        <p>Please update your billing details to avoid interruption of service:</p>
        <p><a href="{portal_url}" class="btn" style="background-color: #da3633;">Update Payment Method</a></p>
        """
        text = (
            f"Payment Unsuccessful\n\n"
            f"We were unable to process your recent subscription renewal payment for AstroOS.\n"
            f"Reason: {error}\n"
            f"Grace Period: Premium access remains active for 3 days.\n\n"
            f"Update your payment method: {portal_url}\n"
        )
        return RenderedEmail(subject=subject, html_body=cls._wrap_html_layout(subject, html), text_body=text)

    # 3. Subscription Activated
    @classmethod
    def _render_subscription_activated(cls, ctx: Mapping[str, Any]) -> RenderedEmail:
        plan = ctx.get("plan_name", "PRO")
        horoscope_limit = ctx.get("saved_horoscopes_limit", 50)
        research_limit = ctx.get("research_limit", 1)

        subject = f"Welcome to AstroOS {plan}!"
        html = f"""
        <h2>Your {plan} Subscription is Active</h2>
        <p>Welcome to AstroOS {plan}! Your premium research platform features have been unlocked.</p>
        <div class="box">
          <p><strong>Plan:</strong> AstroOS {plan}</p>
          <p><strong>Saved Horoscopes Quota:</strong> {horoscope_limit}</p>
          <p><strong>Monthly Research Runs:</strong> {research_limit}</p>
          <p><strong>Features:</strong> Full charts, Dasha analysis, transit confluence, and research workspace.</p>
        </div>
        <p><a href="http://localhost:3000" class="btn">Launch Workspace</a></p>
        """
        text = (
            f"Welcome to AstroOS {plan}!\n\n"
            f"Your premium research platform features have been unlocked.\n"
            f"Plan: {plan}\n"
            f"Saved Horoscopes: {horoscope_limit}\n"
            f"Monthly Research Runs: {research_limit}\n"
        )
        return RenderedEmail(subject=subject, html_body=cls._wrap_html_layout(subject, html), text_body=text)

    # 4. Subscription Renewed
    @classmethod
    def _render_subscription_renewed(cls, ctx: Mapping[str, Any]) -> RenderedEmail:
        plan = ctx.get("plan_name", "PRO")
        next_billing = ctx.get("next_billing_date", "in 30 days")

        subject = f"Subscription Renewed: AstroOS {plan}"
        html = f"""
        <h2>Subscription Extended</h2>
        <p>Your subscription to <strong>AstroOS {plan}</strong> has renewed successfully.</p>
        <div class="box">
          <p><strong>Next Renewal Date:</strong> {next_billing}</p>
          <p><strong>Status:</strong> Active</p>
        </div>
        """
        text = f"Subscription Extended\n\nYour subscription to AstroOS {plan} has renewed successfully.\nNext Renewal Date: {next_billing}\n"
        return RenderedEmail(subject=subject, html_body=cls._wrap_html_layout(subject, html), text_body=text)

    # 5. Subscription Cancelled
    @classmethod
    def _render_subscription_cancelled(cls, ctx: Mapping[str, Any]) -> RenderedEmail:
        plan = ctx.get("plan_name", "PRO")
        end_date = ctx.get("period_end_date", "the end of your current period")

        subject = f"Cancellation Confirmation: AstroOS {plan}"
        html = f"""
        <h2>Subscription Cancelled</h2>
        <p>Your <strong>AstroOS {plan}</strong> subscription has been cancelled.</p>
        <p>You will continue to have full premium access until <strong>{end_date}</strong>. After that date, your account will transition to the FREE plan.</p>
        <p><a href="http://localhost:3000/settings/billing" class="btn">Manage Subscription</a></p>
        """
        text = (
            f"Subscription Cancelled\n\n"
            f"Your AstroOS {plan} subscription has been cancelled.\n"
            f"You will have full premium access until {end_date}.\n"
        )
        return RenderedEmail(subject=subject, html_body=cls._wrap_html_layout(subject, html), text_body=text)

    # 6. Subscription Expired
    @classmethod
    def _render_subscription_expired(cls, ctx: Mapping[str, Any]) -> RenderedEmail:
        subject = "AstroOS Subscription Lapsed"
        html = """
        <h2>Your Subscription Has Expired</h2>
        <p>Your premium access period and grace window have ended. Your account is now operating on the <strong>FREE</strong> plan.</p>
        <div class="box">
          <p>Your existing research and charts are safely saved in read-only mode according to FREE limits.</p>
        </div>
        <p><a href="http://localhost:3000/settings/billing" class="btn">Reactivate Premium</a></p>
        """
        text = "Your AstroOS subscription has expired. Your account has transitioned to the FREE plan.\n"
        return RenderedEmail(subject=subject, html_body=cls._wrap_html_layout(subject, html), text_body=text)

    # 7. Quota Warning
    @classmethod
    def _render_quota_warning(cls, ctx: Mapping[str, Any]) -> RenderedEmail:
        metric = ctx.get("metric_name", "saved horoscopes")
        used = ctx.get("used", 0)
        limit = ctx.get("limit", 0)
        percentage = ctx.get("percentage", 80)

        subject = f"Quota Notice: {percentage}% of {metric} used"
        html = f"""
        <h2>Usage Quota Alert</h2>
        <p>You have used <strong>{percentage}%</strong> of your {metric} quota.</p>
        <div class="box">
          <p><strong>Current Usage:</strong> {used} / {limit} {metric}</p>
        </div>
        <p>Need more capacity? You can upgrade your plan at any time:</p>
        <p><a href="http://localhost:3000/settings/billing" class="btn">View Plans & Limits</a></p>
        """
        text = f"Usage Quota Alert\n\nYou have used {percentage}% of your {metric} quota ({used}/{limit}).\n"
        return RenderedEmail(subject=subject, html_body=cls._wrap_html_layout(subject, html), text_body=text)

    # 8. Password Reset
    @classmethod
    def _render_password_reset(cls, ctx: Mapping[str, Any]) -> RenderedEmail:
        link = ctx.get("reset_link", "#")
        ttl = ctx.get("ttl_minutes", 30)

        subject = "Reset your AstroOS password"
        html = f"""
        <h2>Reset Your Password</h2>
        <p>We received a request to reset your AstroOS account password.</p>
        <p><a href="{link}" class="btn">Reset Password</a></p>
        <p>This link expires in {ttl} minutes. If you did not request this change, you can safely ignore this email.</p>
        """
        text = f"Reset your AstroOS password\n\nClick the link below to reset your password:\n{link}\n\nThis link expires in {ttl} minutes.\n"
        return RenderedEmail(subject=subject, html_body=cls._wrap_html_layout(subject, html), text_body=text)

    # 9. Security Alert
    @classmethod
    def _render_security_alert(cls, ctx: Mapping[str, Any]) -> RenderedEmail:
        action = ctx.get("action", "Account Login / Key Changed")
        time_str = ctx.get("timestamp", "Recently")
        ip = ctx.get("ip_address", "Unknown IP")

        subject = f"Security Alert: {action}"
        html = f"""
        <h2 style="color: #f85149;">Security Notification</h2>
        <p>A sensitive security action was performed on your AstroOS account:</p>
        <div class="box">
          <p><strong>Action:</strong> {action}</p>
          <p><strong>Time:</strong> {time_str}</p>
          <p><strong>IP / Location:</strong> {ip}</p>
        </div>
        <p>If this was not you, please secure your account immediately.</p>
        """
        text = f"Security Alert: {action}\n\nTime: {time_str}\nIP: {ip}\nIf this was not you, please secure your account.\n"
        return RenderedEmail(subject=subject, html_body=cls._wrap_html_layout(subject, html), text_body=text)
