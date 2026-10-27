#!/usr/bin/env python3
"""
Email verification codes for auto_apply.py.

Some application forms (for example Greenhouse's "enter the security code we
emailed you" step) send a one-time code to your email after you click Submit.
This module spots the code box on the page, reads the newest verification
email from your Gmail over IMAP (same GMAIL_APP_PASSWORD as notify_replies.py),
and types the code in.

Only codes sent to your own email are handled. SMS codes and captchas are not:
those still need you.
"""

import re
import time
import email
import imaplib
from email.header import decode_header
from datetime import datetime, timedelta

OTP_FIELD_JS = r"""() => {
  const clean = s => (s || '').replace(/\s+/g, ' ').toLowerCase();
  const visible = e => !!(e.offsetParent || e.getClientRects().length);
  const inputs = [...document.querySelectorAll('input')].filter(e => visible(e) && !e.disabled && !e.value &&
      ['text', 'tel', 'number', 'password', ''].includes((e.getAttribute('type') || '').toLowerCase()));
  const hint = /(verification|security|one[- ]time|confirmation|access) code|\botp\b|passcode|enter the code|code (we|that was) (sent|emailed)/;
  const single = inputs.filter(e => e.getAttribute('autocomplete') === 'one-time-code' ||
      hint.test(clean([e.name, e.id, e.placeholder, e.getAttribute('aria-label'),
                       e.labels && e.labels[0] && e.labels[0].innerText].join(' '))));
  // Split boxes: several 1-character inputs side by side
  const boxes = inputs.filter(e => e.maxLength === 1);
  const pageAsks = hint.test(clean(document.body.innerText.slice(0, 20000)));
  if (boxes.length >= 4 && pageAsks) {
    boxes.forEach((b, i) => b.setAttribute('data-aa-otp', String(i)));
    return { kind: 'boxes', count: boxes.length };
  }
  if (single.length) { single[0].setAttribute('data-aa-otp', '0'); return { kind: 'single', count: 1 }; }
  if (pageAsks && inputs.length === 1) { inputs[0].setAttribute('data-aa-otp', '0'); return { kind: 'single', count: 1 }; }
  return null;
}"""

CODE_NEAR_WORD = re.compile(r"(?:code|otp|passcode)\b[^A-Za-z0-9]{0,40}?(?:is|:)?\s*([A-Za-z0-9]{4,10})\b", re.I)
CODE_ON_OWN_LINE = re.compile(r"^\s*([A-Za-z0-9]{4,10})\s*$", re.M)
NOT_CODES = {"verification", "security", "password", "please", "thanks", "thank", "hello", "application", "greenhouse", "expires", "minutes"}


def find_otp_field(page):
    return page.evaluate(OTP_FIELD_JS)


def _decode(value):
    out = ""
    for part, enc in decode_header(value or ""):
        out += part.decode(enc or "utf-8", errors="replace") if isinstance(part, bytes) else part
    return out


def _body_text(msg):
    parts = msg.walk() if msg.is_multipart() else [msg]
    text, html = "", ""
    for part in parts:
        ctype = part.get_content_type()
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        decoded = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        if ctype == "text/plain":
            text += decoded
        elif ctype == "text/html":
            html += decoded
    if not text and html:
        text = re.sub(r"<br\s*/?>|</p>|</div>|</td>|</h\d>", "\n", html, flags=re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&nbsp;", " ", text)
    return text


def extract_code(subject, body, length=None):
    """Pull the verification code out of an email. Prefers a code that sits on its own line."""
    def ok(c):
        looks_like_code = any(ch.isdigit() for ch in c) or (c.isupper() and len(c) >= 6)
        return c.lower() not in NOT_CODES and looks_like_code and (not length or len(c) == length)
    for pattern in (CODE_ON_OWN_LINE, CODE_NEAR_WORD):
        for source in (body, subject):
            for c in pattern.findall(source or ""):
                if ok(c):
                    return c
    return None


def fetch_code(user, app_password, since, company="", length=None, timeout=120, poll=6, log=print):
    """Poll Gmail for a verification email received after `since` and return its code."""
    deadline = time.time() + timeout
    seen = set()
    while time.time() < deadline:
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            mail.login(user, app_password)
            mail.select("inbox")
            day = (since - timedelta(days=1)).strftime("%d-%b-%Y")
            _, data = mail.search(None, f'(SINCE {day})')
            ids = data[0].split()[-25:]
            for mid in reversed(ids):
                if mid in seen:
                    continue
                seen.add(mid)
                _, msg_data = mail.fetch(mid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                try:
                    received = email.utils.parsedate_to_datetime(msg["Date"]).astimezone().replace(tzinfo=None)
                except Exception:
                    continue
                if received < since - timedelta(seconds=30):
                    continue
                subject = _decode(msg["Subject"])
                sender = _decode(msg["From"]).lower()
                body = _body_text(msg)
                blob = f"{subject} {body[:3000]}".lower()
                if not re.search(r"code|verify|verification|otp|passcode", blob):
                    continue
                if company and not any(w in sender + blob for w in (company.lower().split()[0], "greenhouse", "lever", "ashby")):
                    continue
                code = extract_code(subject, body, length)
                if code:
                    mail.logout()
                    log(f"   📧 verification code found in email from {sender[:50]}")
                    return code
            mail.logout()
        except imaplib.IMAP4.error as e:
            log(f"   could not read Gmail for the code: {e}")
            return None
        except Exception as e:
            log(f"   waiting for verification email ({e})")
        time.sleep(poll)
    return None


def handle_otp(page, user, app_password, since, company="", log=print):
    """If the page asks for an emailed code, fetch it and type it in. Returns True if a code was entered."""
    field = find_otp_field(page)
    if not field:
        return False
    if not app_password:
        log("   page asks for an email code, but GMAIL_APP_PASSWORD isn't set in .env")
        return False
    log("   📧 page asks for a verification code — checking your Gmail")
    length = field["count"] if field["kind"] == "boxes" else None
    code = fetch_code(user, app_password, since, company, length, log=log)
    if not code:
        log("   no verification code arrived in time")
        return False
    if field["kind"] == "boxes":
        for i, ch in enumerate(code[: field["count"]]):
            page.locator(f'[data-aa-otp="{i}"]').fill(ch)
    else:
        page.locator('[data-aa-otp="0"]').fill(code)
    return True
