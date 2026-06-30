"""
Transactional email via Resend. Fail-soft: if RESEND_API_KEY is unset (or a send fails), we log
and move on — email is never on the critical path of a request. (Stripe sends its own payment
receipts, so we only handle welcome + password reset here.)
"""
import logging

import requests
from django.conf import settings

log = logging.getLogger(__name__)
API = "https://api.resend.com/emails"


def configured() -> bool:
    return bool(settings.RESEND_API_KEY)


def send_email(to, subject, html) -> dict:
    if not configured():
        log.info("email skipped (Resend not configured): %r -> %s", subject, to)
        return {"ok": False, "error": "email_not_configured"}
    try:
        r = requests.post(
            API, headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
            json={"from": settings.EMAIL_FROM, "to": [to], "subject": subject, "html": html},
            timeout=15)
        if r.status_code >= 300:
            log.warning("Resend send failed %s: %s", r.status_code, r.text[:200])
            return {"ok": False, "error": "send_failed"}
        return {"ok": True}
    except requests.RequestException as e:
        log.warning("Resend send error: %s", e)
        return {"ok": False, "error": "send_error"}


def _shell(title, body_html):
    return (f'<div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;'
            f'background:#14171d;color:#eef1f6;padding:32px;border-radius:12px;max-width:520px">'
            f'<h1 style="margin:0 0 8px;font-size:22px">EBE·TV</h1>'
            f'<h2 style="margin:0 0 16px;font-weight:600;color:#cdd6e2">{title}</h2>'
            f'{body_html}</div>')


def _button(href, label):
    return (f'<a href="{href}" style="display:inline-block;background:#56697f;color:#fff;'
            f'padding:12px 20px;border-radius:8px;font-weight:700;text-decoration:none">{label}</a>')


def send_welcome(user):
    html = _shell("Welcome aboard",
                  f'<p>Hi {user.display_name or "there"}, your EBE·TV account is ready. '
                  f'Browse originals and live events any time.</p>'
                  f'<p>{_button(settings.FRONTEND_BASE_URL, "Start watching")}</p>')
    return send_email(user.email, "Welcome to EBE·TV", html)


def send_password_reset(user, link):
    html = _shell("Reset your password",
                  f'<p>We got a request to reset your EBE·TV password. This link expires soon — '
                  f'if you didn’t ask for it, you can ignore this email.</p>'
                  f'<p>{_button(link, "Reset password")}</p>'
                  f'<p style="color:#98a2b3;font-size:13px">Or paste this URL: {link}</p>')
    return send_email(user.email, "Reset your EBE·TV password", html)
