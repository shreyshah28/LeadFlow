import os
import logging
import html
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError
import httpx

import models

logger = logging.getLogger("leadflow.email")

# Fallback fixed offset for Asia/Kolkata (UTC +05:30)
KOLKATA_FALLBACK_TZ = timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")

# Resend HTTPS API endpoint
RESEND_API_URL = "https://api.resend.com/emails"

def get_email_config() -> Dict[str, Any]:
    """
    Loads email configuration safely from environment variables for Resend API delivery.
    """
    enabled_raw = os.environ.get("DAILY_FOLLOWUP_EMAIL_ENABLED", "false").strip().lower()
    is_enabled = enabled_raw in ("true", "1", "yes", "on")

    return {
        "api_key": os.environ.get("RESEND_API_KEY", "").strip(),
        "email_from": os.environ.get("EMAIL_FROM", "").strip() or "LeadFlow CRM <onboarding@resend.dev>",
        "email_to": os.environ.get("FOLLOWUP_EMAIL_TO", "").strip(),
        "enabled": is_enabled,
        "timezone": os.environ.get("DAILY_FOLLOWUP_TIMEZONE", "Asia/Kolkata").strip() or "Asia/Kolkata",
        "cron_secret": os.environ.get("CRON_SECRET", "").strip()
    }

def is_email_configured() -> bool:
    """
    Checks whether all essential Resend credentials and recipient are configured.
    """
    cfg = get_email_config()
    return bool(cfg["api_key"] and cfg["email_to"])

def mask_email(email_str: str) -> str:
    """
    Safely masks an email address for public/frontend status display.
    e.g. alex.morgan@example.com -> a***n@example.com
    """
    if not email_str or "@" not in email_str:
        return ""
    parts = email_str.split("@")
    user, domain = parts[0], parts[1]
    if len(user) <= 2:
        masked_user = user[0] + "***"
    else:
        masked_user = user[0] + "***" + user[-1]
    return f"{masked_user}@{domain}"

def get_safe_email_status() -> Dict[str, Any]:
    """
    Returns public/safe status for frontend Settings modal without exposing credentials,
    secrets, or the raw recipient email address.
    """
    cfg = get_email_config()
    configured = is_email_configured()
    masked = mask_email(cfg["email_to"]) if cfg["email_to"] else "Not configured"
    return {
        "enabled": cfg["enabled"],
        "configured": configured,
        "provider": "Resend HTTPS API",
        "recipient": masked,
        "recipient_masked": masked,
        "sender": cfg["email_from"],
        "timezone": cfg["timezone"],
        "scheduled_time": "8:00 AM Asia/Kolkata",
        "duplicate_prevention": "Enabled (1 per calendar day)",
        "api_endpoint": RESEND_API_URL
    }

def get_current_time_in_tz(tz_name: str = "Asia/Kolkata") -> datetime:
    """
    Returns the current datetime in the specified timezone with robust fallbacks.
    """
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(tz_name)
        return datetime.now(tz)
    except Exception:
        if tz_name in ("Asia/Kolkata", "Asia/Calcutta", "IST"):
            return datetime.now(KOLKATA_FALLBACK_TZ)
        return datetime.now(timezone.utc)

def get_current_date_strings(tz_name: str = "Asia/Kolkata") -> Tuple[str, str]:
    """
    Returns (iso_date 'YYYY-MM-DD', display_date 'Monday, Nov 23, 2026')
    for the configured timezone.
    """
    dt = get_current_time_in_tz(tz_name)
    iso_date = dt.strftime("%Y-%m-%d")
    display_date = dt.strftime("%A, %B %d, %Y")
    return iso_date, display_date

def sanitize_error_string(err_str: str) -> str:
    """
    Strips API keys and sensitive secrets from error strings before logging or returning to API clients.
    """
    if not err_str:
        return ""
    cfg = get_email_config()
    secrets_to_redact = []
    if cfg["api_key"]:
        secrets_to_redact.append(cfg["api_key"])
    if cfg["cron_secret"]:
        secrets_to_redact.append(cfg["cron_secret"])

    cleaned = str(err_str)
    for s in secrets_to_redact:
        if s and len(s) >= 3:
            cleaned = cleaned.replace(s, "[REDACTED]")

    return cleaned

def safe_html(val: Optional[Any], default: str = "") -> str:
    """
    Escapes all special characters in untrusted user-controlled input for HTML inclusion.
    """
    if val is None:
        return default
    return html.escape(str(val), quote=True)

def safe_mailto_link(raw_email: Optional[str]) -> str:
    """
    Constructs a safe mailto link preventing HTML attribute injection and XSS.
    """
    if not raw_email or not str(raw_email).strip():
        return "—"
    clean_email = str(raw_email).strip()
    escaped_display = html.escape(clean_email)
    escaped_attr = html.escape(clean_email, quote=True)
    return f'<a href="mailto:{escaped_attr}" style="color: #12A879; text-decoration: none;">{escaped_display}</a>'

def render_followup_email(
    display_date: str,
    due_today_leads: List[models.Lead],
    overdue_leads: List[models.Lead]
) -> Tuple[str, str]:
    """
    Renders responsive HTML and readable plain-text email bodies matching LeadFlow branding.
    All user-controlled lead data inserted into HTML is strictly escaped with html.escape.
    """
    today_count = len(due_today_leads)
    overdue_count = len(overdue_leads)

    # -------------------------------------------------------------------------
    # 1. Plain Text Alternative (Readable, unescaped raw data)
    # -------------------------------------------------------------------------
    text_lines = [
        "============================================================",
        f" LEADFLOW - DAILY FOLLOW-UP SUMMARY",
        f" Date: {display_date}",
        "============================================================",
        "",
        f"SUMMARY:",
        f"  - Follow-ups Due Today: {today_count}",
        f"  - Overdue Follow-ups:   {overdue_count}",
        ""
    ]

    text_lines.append("------------------------------------------------------------")
    text_lines.append(f"FOLLOW-UPS DUE TODAY ({today_count})")
    text_lines.append("------------------------------------------------------------")

    if today_count == 0:
        text_lines.append("  No follow-ups scheduled for today.")
    else:
        for idx, lead in enumerate(due_today_leads, 1):
            text_lines.append(f"{idx}. {lead.contact_person or 'N/A'} | {lead.company_name}")
            text_lines.append(f"   Email:  {lead.email or 'N/A'}")
            text_lines.append(f"   Phone:  {lead.phone or 'N/A'}")
            text_lines.append(f"   Status: {lead.status} | Value: ${lead.deal_value:,.2f}")
            if lead.notes:
                text_lines.append(f"   Notes:  {lead.notes}")
            text_lines.append("")

    if overdue_count > 0:
        text_lines.append("------------------------------------------------------------")
        text_lines.append(f"OVERDUE FOLLOW-UPS ({overdue_count})")
        text_lines.append("------------------------------------------------------------")
        for idx, lead in enumerate(overdue_leads, 1):
            text_lines.append(f"{idx}. {lead.contact_person or 'N/A'} | {lead.company_name}")
            text_lines.append(f"   Due Date: {lead.follow_up_date} (OVERDUE)")
            text_lines.append(f"   Email:    {lead.email or 'N/A'} | Phone: {lead.phone or 'N/A'}")
            text_lines.append(f"   Status:   {lead.status}")
            if lead.notes:
                text_lines.append(f"   Notes:    {lead.notes}")
            text_lines.append("")

    text_lines.extend([
        "------------------------------------------------------------",
        "LeadFlow CRM & Pipeline Tracker",
        "Automatic Daily Follow-up Notification Service",
        "============================================================"
    ])
    text_body = "\n".join(text_lines)

    # -------------------------------------------------------------------------
    # 2. HTML Email Body (Escaped inputs, inline CSS for universal email clients)
    # -------------------------------------------------------------------------
    def status_badge_color(status_str: str) -> Tuple[str, str, str]:
        s = (status_str or "").lower()
        if s == "new":
            return ("#E0F2FE", "#0369A1", "#BAE6FD")
        elif s == "contacted":
            return ("#FEF3C7", "#B45309", "#FDE68A")
        elif s == "meeting":
            return ("#F5F3FF", "#6D28D9", "#DDD6FE")
        elif s == "won":
            return ("#DDF5EA", "#0D9168", "#A9DEC8")
        elif s == "lost":
            return ("#FFE4E6", "#BE123C", "#FECDD3")
        return ("#EEF5F0", "#3D5C49", "#D9E5DE")

    def build_table_rows(leads: List[models.Lead], is_overdue: bool = False) -> str:
        rows = []
        for lead in leads:
            bg, text_c, border_c = status_badge_color(lead.status)

            safe_contact = safe_html(lead.contact_person, default="—")
            safe_company = safe_html(lead.company_name, default="—")
            safe_email_link = safe_mailto_link(lead.email)
            safe_phone = safe_html(lead.phone, default="—")
            safe_status = safe_html(lead.status, default="New")
            safe_date = safe_html(lead.follow_up_date, default="—")

            if lead.notes:
                safe_notes = safe_html(lead.notes)
                notes_html = f"<div style='margin-top:4px; font-size:12px; color:#71867C; font-style:italic;'>{safe_notes}</div>"
            else:
                notes_html = ""

            if is_overdue:
                date_col = f"<span style='color:#B91C1C; font-weight:700;'>{safe_date}</span>"
            else:
                date_col = safe_date

            row_html = f"""
            <tr style="border-bottom: 1px solid #E2EBE5;">
              <td style="padding: 12px 14px; font-size: 13px; color: #0B2B1F; vertical-align: top;">
                <strong>{safe_contact}</strong>
                {notes_html}
              </td>
              <td style="padding: 12px 14px; font-size: 13px; color: #0B2B1F; font-weight: 600; vertical-align: top;">
                {safe_company}
              </td>
              <td style="padding: 12px 14px; font-size: 13px; color: #3D5C49; vertical-align: top;">
                {safe_email_link}<br>
                <span style="font-size: 12px; color: #71867C;">{safe_phone}</span>
              </td>
              <td style="padding: 12px 14px; font-size: 13px; vertical-align: top; white-space: nowrap;">
                {date_col}
              </td>
              <td style="padding: 12px 14px; font-size: 12px; vertical-align: top;">
                <span style="display:inline-block; padding: 2px 8px; border-radius: 9999px; background-color:{bg}; color:{text_c}; border: 1px solid {border_c}; font-weight: 600;">
                  {safe_status}
                </span>
              </td>
            </tr>
            """
            rows.append(row_html)
        return "".join(rows)

    today_rows_html = build_table_rows(due_today_leads, is_overdue=False)
    overdue_rows_html = build_table_rows(overdue_leads, is_overdue=True)

    today_section_content = f"""
      <table style="width: 100%; border-collapse: collapse; background-color: #FFFFFF; border-radius: 8px; overflow: hidden; border: 1px solid #E2EBE5;">
        <thead>
          <tr style="background-color: #EEF5F0; border-bottom: 2px solid #A9DEC8; text-align: left;">
            <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; color: #3D5C49; text-transform: uppercase; letter-spacing: 0.05em;">Lead / Contact</th>
            <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; color: #3D5C49; text-transform: uppercase; letter-spacing: 0.05em;">Company</th>
            <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; color: #3D5C49; text-transform: uppercase; letter-spacing: 0.05em;">Contact Info</th>
            <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; color: #3D5C49; text-transform: uppercase; letter-spacing: 0.05em;">Date</th>
            <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; color: #3D5C49; text-transform: uppercase; letter-spacing: 0.05em;">Status</th>
          </tr>
        </thead>
        <tbody>
          {today_rows_html}
        </tbody>
      </table>
    """ if today_count > 0 else """
      <div style="padding: 24px 20px; background-color: #FFFFFF; border: 1px dashed #A9DEC8; border-radius: 8px; text-align: center; color: #3D5C49;">
        <span style="display: inline-block; font-size: 24px; margin-bottom: 6px;">🎉</span>
        <p style="margin: 0; font-size: 14px; font-weight: 600; color: #0B2B1F;">No follow-ups scheduled for today.</p>
        <p style="margin: 4px 0 0; font-size: 12px; color: #71867C;">All your opportunities are up to date.</p>
      </div>
    """

    overdue_section_html = f"""
      <div style="margin-top: 32px;">
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
          <h3 style="margin: 0; font-size: 15px; font-weight: 700; color: #B91C1C;">⚠️ Action Required: Overdue Follow-ups ({overdue_count})</h3>
        </div>
        <table style="width: 100%; border-collapse: collapse; background-color: #FFFFFF; border-radius: 8px; overflow: hidden; border: 1px solid #FECACA;">
          <thead>
            <tr style="background-color: #FEF2F2; border-bottom: 2px solid #FECACA; text-align: left;">
              <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; color: #B91C1C; text-transform: uppercase; letter-spacing: 0.05em;">Lead / Contact</th>
              <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; color: #B91C1C; text-transform: uppercase; letter-spacing: 0.05em;">Company</th>
              <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; color: #B91C1C; text-transform: uppercase; letter-spacing: 0.05em;">Contact Info</th>
              <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; color: #B91C1C; text-transform: uppercase; letter-spacing: 0.05em;">Due Date</th>
              <th style="padding: 10px 14px; font-size: 11px; font-weight: 700; color: #B91C1C; text-transform: uppercase; letter-spacing: 0.05em;">Status</th>
            </tr>
          </thead>
          <tbody>
            {overdue_rows_html}
          </tbody>
        </table>
      </div>
    """ if overdue_count > 0 else ""

    safe_display_date = safe_html(display_date)

    html_body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>LeadFlow Daily Follow-up Summary</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #F4F8F5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #0B2B1F; -webkit-font-smoothing: antialiased;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #F4F8F5; padding: 24px 12px;">
        <tr>
          <td align="center">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 680px; background-color: #FFFFFF; border-radius: 12px; border: 1px solid #D9E5DE; box-shadow: 0 4px 12px rgba(11, 43, 31, 0.05); overflow: hidden;">
              <!-- Brand Header -->
              <tr>
                <td style="background: linear-gradient(135deg, #12A879 0%, #059669 100%); padding: 24px 28px; text-align: left;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td>
                        <span style="font-size: 22px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.02em;">LeadFlow</span>
                        <span style="font-size: 12px; color: #DDF5EA; margin-left: 8px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;">CRM & Follow-up Tracker</span>
                        <h1 style="margin: 6px 0 0; font-size: 18px; font-weight: 700; color: #FFFFFF;">Daily Follow-up Summary</h1>
                        <p style="margin: 4px 0 0; font-size: 13px; color: #E7F5EE;">{safe_display_date} • 8:00 AM IST</p>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Metric Cards Row -->
              <tr>
                <td style="padding: 24px 28px 12px;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td width="48%" style="background-color: #EEF5F0; border: 1px solid #A9DEC8; border-radius: 8px; padding: 14px 18px; text-align: left;">
                        <span style="font-size: 11px; font-weight: 700; color: #3D5C49; text-transform: uppercase; letter-spacing: 0.05em;">Due Today</span>
                        <div style="font-size: 26px; font-weight: 800; color: #12A879; margin-top: 2px;">{today_count}</div>
                        <span style="font-size: 11px; color: #71867C;">Follow-ups scheduled for today</span>
                      </td>
                      <td width="4%"></td>
                      <td width="48%" style="background-color: {'#FEF2F2' if overdue_count > 0 else '#EEF5F0'}; border: 1px solid {'#FECACA' if overdue_count > 0 else '#D9E5DE'}; border-radius: 8px; padding: 14px 18px; text-align: left;">
                        <span style="font-size: 11px; font-weight: 700; color: {'#B91C1C' if overdue_count > 0 else '#3D5C49'}; text-transform: uppercase; letter-spacing: 0.05em;">Overdue</span>
                        <div style="font-size: 26px; font-weight: 800; color: {'#EF4444' if overdue_count > 0 else '#059669'}; margin-top: 2px;">{overdue_count}</div>
                        <span style="font-size: 11px; color: #71867C;">Pending past follow-up date</span>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Today's Follow-up Table Section -->
              <tr>
                <td style="padding: 12px 28px 24px;">
                  <h2 style="margin: 0 0 12px; font-size: 15px; font-weight: 700; color: #0B2B1F;">📅 Follow-ups Due Today ({today_count})</h2>
                  {today_section_content}
                  {overdue_section_html}
                </td>
              </tr>

              <!-- Footer -->
              <tr>
                <td style="background-color: #F4F8F5; border-top: 1px solid #E2EBE5; padding: 18px 28px; text-align: center;">
                  <p style="margin: 0; font-size: 12px; color: #71867C;">
                    Sent automatically by <strong>LeadFlow</strong> Follow-up Automation via Resend HTTPS API.
                  </p>
                  <p style="margin: 4px 0 0; font-size: 11px; color: #8FA499;">
                    Configured for <strong>Asia/Kolkata (IST)</strong> delivery at 8:00 AM.
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    return html_body, text_body

def send_email(subject: str, html_body: str, text_body: str, to_email: str) -> Dict[str, Any]:
    """
    Sends multi-part email using Resend HTTPS REST API.
    Never transmits API keys or secrets in unencrypted or raw error logs.
    """
    cfg = get_email_config()
    if not is_email_configured():
        err_msg = "Resend configuration is incomplete. Missing RESEND_API_KEY or FOLLOWUP_EMAIL_TO."
        logger.warning(err_msg)
        return {"success": False, "error": err_msg}

    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
        "User-Agent": "LeadFlow-CRM/1.0"
    }

    payload = {
        "from": cfg["email_from"],
        "to": [to_email],
        "subject": subject,
        "html": html_body,
        "text": text_body
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(RESEND_API_URL, headers=headers, json=payload)

        if response.status_code in (200, 201):
            res_data = response.json()
            email_id = res_data.get("id", "unknown")
            logger.info(f"Email successfully dispatched via Resend to {to_email}. Resend ID: {email_id}")
            return {"success": True, "recipient": to_email, "id": email_id}
        else:
            try:
                err_json = response.json()
                raw_err = err_json.get("message") or err_json.get("error") or response.text
            except Exception:
                raw_err = response.text or f"HTTP status {response.status_code}"

            safe_err = sanitize_error_string(f"Resend API error ({response.status_code}): {raw_err}")
            logger.error(f"Failed to send email via Resend to {to_email}: {safe_err}")
            return {"success": False, "error": safe_err, "status_code": response.status_code}

    except (httpx.TimeoutException, TimeoutError):
        err_str = "Resend API connection timed out after 15 seconds."
        logger.error(err_str)
        return {"success": False, "error": err_str}
    except Exception as e:
        safe_exc = sanitize_error_string(f"{type(e).__name__}: {str(e)}")
        err_str = f"Failed to send email via Resend API: {safe_exc}"
        logger.error(err_str)
        return {"success": False, "error": err_str}

def send_daily_followup_email(db: Session, force_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Main routine executed daily to gather follow-ups, prevent duplicate delivery via
    atomic database claim locking, and dispatch the summary email via Resend HTTPS API.
    Preserves retries for failed deliveries and prevents concurrent duplicate execution.
    """
    cfg = get_email_config()

    if not cfg["enabled"]:
        logger.info("Daily follow-up email is disabled in configuration (DAILY_FOLLOWUP_EMAIL_ENABLED=false).")
        return {
            "status": "disabled",
            "message": "Daily follow-up email is currently disabled. Enable with DAILY_FOLLOWUP_EMAIL_ENABLED=true."
        }

    if not is_email_configured():
        logger.warning("Daily follow-up email triggered but Resend configuration is incomplete.")
        return {
            "status": "unconfigured",
            "message": "Resend configuration is incomplete. Check RESEND_API_KEY and FOLLOWUP_EMAIL_TO."
        }

    # 1. Determine date in target timezone
    tz_name = cfg["timezone"]
    computed_iso, display_date = get_current_date_strings(tz_name)
    iso_date = force_date if force_date else computed_iso
    recipient = cfg["email_to"]
    now_utc = datetime.utcnow()
    stale_threshold = now_utc - timedelta(minutes=5)

    # 2. Check existing delivery records
    existing_log = db.query(models.DailyEmailLog).filter(models.DailyEmailLog.delivery_date == iso_date).first()
    if existing_log and existing_log.status == "SUCCESS":
        logger.info(f"Daily follow-up email for {iso_date} has already been sent successfully at {existing_log.sent_at}.")
        return {
            "status": "already_sent",
            "date": iso_date,
            "delivery_date": iso_date,
            "sent_at": existing_log.sent_at.isoformat() if existing_log.sent_at else None,
            "message": f"Daily follow-up email for {iso_date} has already been successfully delivered."
        }

    # 3. Atomic Claim Strategy
    # If existing_log exists, execute an atomic conditional UPDATE:
    # Only succeeds (rowcount == 1) if status == 'FAILED' OR (status == 'PENDING' and sent_at < stale_threshold).
    claim_log = None
    if existing_log:
        rows_updated = db.query(models.DailyEmailLog).filter(
            models.DailyEmailLog.delivery_date == iso_date,
            or_(
                models.DailyEmailLog.status == "FAILED",
                and_(
                    models.DailyEmailLog.status == "PENDING",
                    or_(
                        models.DailyEmailLog.sent_at.is_(None),
                        models.DailyEmailLog.sent_at < stale_threshold
                    )
                )
            )
        ).update(
            {
                models.DailyEmailLog.status: "PENDING",
                models.DailyEmailLog.sent_at: now_utc,
                models.DailyEmailLog.recipient: recipient,
                models.DailyEmailLog.error_message: None
            },
            synchronize_session=False
        )
        db.commit()

        if rows_updated == 1:
            # Atomic update succeeded: this request acquired the exclusive claim!
            claim_log = db.query(models.DailyEmailLog).filter(
                models.DailyEmailLog.delivery_date == iso_date
            ).first()
        else:
            # 0 rows updated: another worker holds the claim or it has already been sent
            recheck = db.query(models.DailyEmailLog).filter(
                models.DailyEmailLog.delivery_date == iso_date
            ).first()
            if recheck and recheck.status == "SUCCESS":
                return {
                    "status": "already_sent",
                    "date": iso_date,
                    "delivery_date": iso_date,
                    "sent_at": recheck.sent_at.isoformat() if recheck.sent_at else None,
                    "message": f"Daily follow-up email for {iso_date} has already been successfully delivered."
                }
            return {
                "status": "in_progress",
                "date": iso_date,
                "delivery_date": iso_date,
                "message": f"Daily follow-up email for {iso_date} is currently being processed by another worker."
            }
    else:
        # No existing record: attempt atomic INSERT protected by UNIQUE(delivery_date)
        new_log = models.DailyEmailLog(
            delivery_date=iso_date,
            recipient=recipient,
            status="PENDING",
            due_today_count=0,
            overdue_count=0,
            sent_at=now_utc
        )
        db.add(new_log)
        try:
            db.commit()
            claim_log = new_log
        except IntegrityError:
            # Race condition: another concurrent worker created the record first!
            db.rollback()
            # Attempt atomic conditional update on the newly created record
            rows_updated = db.query(models.DailyEmailLog).filter(
                models.DailyEmailLog.delivery_date == iso_date,
                or_(
                    models.DailyEmailLog.status == "FAILED",
                    and_(
                        models.DailyEmailLog.status == "PENDING",
                        or_(
                            models.DailyEmailLog.sent_at.is_(None),
                            models.DailyEmailLog.sent_at < stale_threshold
                        )
                    )
                )
            ).update(
                {
                    models.DailyEmailLog.status: "PENDING",
                    models.DailyEmailLog.sent_at: now_utc,
                    models.DailyEmailLog.recipient: recipient,
                    models.DailyEmailLog.error_message: None
                },
                synchronize_session=False
            )
            db.commit()

            if rows_updated == 1:
                claim_log = db.query(models.DailyEmailLog).filter(
                    models.DailyEmailLog.delivery_date == iso_date
                ).first()
            else:
                recheck = db.query(models.DailyEmailLog).filter(
                    models.DailyEmailLog.delivery_date == iso_date
                ).first()
                if recheck and recheck.status == "SUCCESS":
                    return {
                        "status": "already_sent",
                        "date": iso_date,
                        "delivery_date": iso_date,
                        "sent_at": recheck.sent_at.isoformat() if recheck.sent_at else None,
                        "message": f"Daily follow-up email for {iso_date} has already been successfully delivered."
                    }
                return {
                    "status": "in_progress",
                    "date": iso_date,
                    "delivery_date": iso_date,
                    "message": f"Daily follow-up email for {iso_date} is currently being processed by another worker."
                }

    # 4. Gather leads and execute delivery under exclusive claim
    try:
        # Follow-ups due today: follow_up_date == iso_date AND status NOT in ('Won', 'Lost')
        due_today_leads = db.query(models.Lead).filter(
            models.Lead.follow_up_date == iso_date,
            models.Lead.status != "Won",
            models.Lead.status != "Lost"
        ).order_by(models.Lead.company_name.asc()).all()

        # Overdue follow-ups: follow_up_date < iso_date AND status NOT in ('Won', 'Lost')
        overdue_leads = db.query(models.Lead).filter(
            models.Lead.follow_up_date < iso_date,
            models.Lead.status != "Won",
            models.Lead.status != "Lost"
        ).order_by(models.Lead.follow_up_date.asc(), models.Lead.company_name.asc()).all()

        subject = f"LeadFlow – Daily Follow-up Summary – {display_date}"
        html_body, text_body = render_followup_email(display_date, due_today_leads, overdue_leads)

        # 5. Send Email via Resend
        result = send_email(subject, html_body, text_body, recipient)

        if result["success"]:
            claim_log.status = "SUCCESS"
            claim_log.recipient = recipient
            claim_log.due_today_count = len(due_today_leads)
            claim_log.overdue_count = len(overdue_leads)
            claim_log.sent_at = datetime.utcnow()
            claim_log.error_message = None
            db.commit()

            return {
                "status": "success",
                "success": True,
                "date": iso_date,
                "delivery_date": iso_date,
                "due_today_count": len(due_today_leads),
                "overdue_count": len(overdue_leads),
                "recipient": recipient,
                "message": f"Successfully sent daily follow-up email for {iso_date} to {recipient} via Resend."
            }
        else:
            safe_err = sanitize_error_string(result.get("error", "Unknown Resend API error"))
            claim_log.status = "FAILED"
            claim_log.recipient = recipient
            claim_log.due_today_count = len(due_today_leads)
            claim_log.overdue_count = len(overdue_leads)
            claim_log.sent_at = datetime.utcnow()
            claim_log.error_message = safe_err
            db.commit()

            return {
                "status": "failed",
                "success": False,
                "date": iso_date,
                "delivery_date": iso_date,
                "error": safe_err,
                "message": f"Failed to deliver daily follow-up email: {safe_err}"
            }
    except Exception as e:
        safe_err = sanitize_error_string(str(e))
        logger.error(f"Unexpected error during daily email processing for {iso_date}: {safe_err}")
        try:
            claim_log.status = "FAILED"
            claim_log.error_message = safe_err
            db.commit()
        except Exception:
            db.rollback()

        return {
            "status": "failed",
            "success": False,
            "date": iso_date,
            "delivery_date": iso_date,
            "error": safe_err,
            "message": f"Failed to deliver daily follow-up email: {safe_err}"
        }

def send_test_email() -> Dict[str, Any]:
    """
    Sends a test verification email to FOLLOWUP_EMAIL_TO via Resend HTTPS API.
    Does NOT mark daily email delivery as complete in daily_email_logs.
    All user-controlled dynamic fields are escaped.
    """
    cfg = get_email_config()
    if not is_email_configured():
        return {
            "status": "failed",
            "success": False,
            "error": "Cannot send test email: Resend settings (RESEND_API_KEY, FOLLOWUP_EMAIL_TO) are incomplete."
        }

    recipient = cfg["email_to"]
    display_dt = get_current_time_in_tz(cfg["timezone"]).strftime("%A, %B %d, %Y %I:%M %p %Z")

    subject = "LeadFlow – Test Email Notification"

    text_body = f"""============================================================
LEADFLOW - EMAIL CONFIGURATION TEST
============================================================

LeadFlow test email – Email configuration is working correctly.

This test confirms that your Resend HTTPS API configuration is properly
set up and able to deliver emails from LeadFlow.

Details:
  - Timestamp: {display_dt}
  - Provider: Resend HTTPS API
  - Sender: {cfg['email_from']}
  - Recipient: {recipient}
  - Note: This test email does not mark your daily follow-up as sent.

============================================================
LeadFlow CRM & Pipeline Tracker
"""

    safe_recipient = safe_html(recipient)
    safe_sender = safe_html(cfg['email_from'])
    safe_display_dt = safe_html(display_dt)

    html_body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>LeadFlow Test Email</title>
    </head>
    <body style="margin: 0; padding: 24px 12px; background-color: #F4F8F5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #0B2B1F;">
      <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 560px; margin: 0 auto; background-color: #FFFFFF; border-radius: 12px; border: 1px solid #D9E5DE; box-shadow: 0 4px 12px rgba(11, 43, 31, 0.05); overflow: hidden;">
        <tr>
          <td style="background: linear-gradient(135deg, #12A879 0%, #059669 100%); padding: 24px; text-align: left;">
            <span style="font-size: 20px; font-weight: 800; color: #FFFFFF;">LeadFlow</span>
            <span style="font-size: 12px; color: #DDF5EA; margin-left: 8px; font-weight: 500;">CRM & Follow-up Tracker</span>
            <h1 style="margin: 6px 0 0; font-size: 18px; font-weight: 700; color: #FFFFFF;">Test Email Notification</h1>
          </td>
        </tr>
        <tr>
          <td style="padding: 24px;">
            <div style="background-color: #DDF5EA; border: 1px solid #A9DEC8; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
              <p style="margin: 0; font-size: 14px; font-weight: 700; color: #0D9168;">
                ✓ LeadFlow test email – Email configuration is working correctly.
              </p>
            </div>
            <p style="margin: 0 0 16px; font-size: 13px; line-height: 1.5; color: #3D5C49;">
              This email was triggered manually from your LeadFlow Settings modal. Your Resend API key and recipient settings have been verified.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #EEF5F0; border-radius: 6px; padding: 12px 14px; font-size: 12px; color: #3D5C49;">
              <tr>
                <td style="padding: 4px 0;"><strong>Timestamp:</strong></td>
                <td style="padding: 4px 0; color: #0B2B1F;">{safe_display_dt}</td>
              </tr>
              <tr>
                <td style="padding: 4px 0;"><strong>Provider:</strong></td>
                <td style="padding: 4px 0; color: #0B2B1F;">Resend HTTPS API</td>
              </tr>
              <tr>
                <td style="padding: 4px 0;"><strong>Sender:</strong></td>
                <td style="padding: 4px 0; color: #0B2B1F;">{safe_sender}</td>
              </tr>
              <tr>
                <td style="padding: 4px 0;"><strong>Recipient:</strong></td>
                <td style="padding: 4px 0; color: #0B2B1F;">{safe_recipient}</td>
              </tr>
              <tr>
                <td style="padding: 4px 0;"><strong>Status:</strong></td>
                <td style="padding: 4px 0; color: #12A879; font-weight: 700;">Verified Active</td>
              </tr>
            </table>
            <p style="margin: 16px 0 0; font-size: 11px; color: #71867C;">
              Note: This test email does not mark your daily follow-up as sent. Daily follow-ups will continue to trigger as scheduled.
            </p>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    res = send_email(subject, html_body, text_body, recipient)
    if res["success"]:
        return {
            "status": "success",
            "success": True,
            "recipient": recipient,
            "message": f"LeadFlow test email – Email configuration is working correctly. Delivered to {recipient}."
        }
    return {
        "status": "failed",
        "success": False,
        "recipient": recipient,
        "error": res.get("error", "Failed to send test email."),
        "message": f"Failed to send test email: {res.get('error', 'Unknown Resend API error')}"
    }
