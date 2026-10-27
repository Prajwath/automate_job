#!/usr/bin/env python3
"""
🔔 Job Application Reply Monitor with Desktop Notifications
Periodically scans Gmail for replies from applied companies.
Sends desktop notifications for POSITIVE responses (Interview, Assessment, Shortlisted).
Updates job_applications.csv and logs all activity.

Usage:
    python3 notify_replies.py              # Single scan
    python3 notify_replies.py --watch      # Continuous monitoring (every 15 min)
    python3 notify_replies.py --test-push  # Send a test phone push (needs NTFY_TOPIC)
    python3 notify_replies.py --dry-run    # Scan without updating CSV
"""

import os
import sys
import csv
import imaplib
import email
import json
import subprocess
import urllib.request
import time
import signal
from email.header import decode_header
from datetime import datetime, timedelta

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(ROOT_DIR, "job_applications.csv")
ENV_FILE = os.path.join(ROOT_DIR, ".env")
LOG_FILE = os.path.join(ROOT_DIR, "reply_notifications.log")
SEEN_FILE = os.path.join(ROOT_DIR, ".seen_email_ids.json")

# How often to scan in --watch mode (seconds)
SCAN_INTERVAL = 15 * 60  # 15 minutes

# --- POSITIVE response keywords (triggers notification) ---
POSITIVE_KEYWORDS = [
    "interview", "screening", "speak with you", "schedule a call",
    "invitation to interview", "round 1", "technical round",
    "chat with the team", "next steps", "move forward",
    "assessment", "hackerrank", "codility", "test link",
    "coding challenge", "take-home", "assignment",
    "shortlisted", "profile shortlisted", "selected for",
    "congratulations", "pleased to inform", "offer letter",
    "we'd like to", "we would like to", "excited to",
    "joining date", "compensation", "offer details"
]

# --- NEGATIVE response keywords ---
NEGATIVE_KEYWORDS = [
    "unfortunately", "not moving forward", "pursuing other candidates",
    "regret to inform", "other applicants", "not been selected",
    "unable to proceed", "position has been filled", "decided not to",
    "wish you the best", "not a match"
]

# --- NEUTRAL keywords (auto-acknowledgements) ---
NEUTRAL_KEYWORDS = [
    "application received", "reviewing your application",
    "received your resume", "thank you for applying",
    "auto-reply", "do-not-reply", "noreply"
]


def log(msg):
    """Log to both console and file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_env_var(key, default=""):
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(key, default)


def load_seen_ids():
    """Load previously seen email message IDs to avoid duplicate notifications."""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen_ids(seen_ids):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_ids), f)


def decode_mime_header(header_value):
    if not header_value:
        return ""
    decoded_fragments = decode_header(header_value)
    result = ""
    for frag, enc in decoded_fragments:
        if isinstance(frag, bytes):
            result += frag.decode(enc or "utf-8", errors="replace")
        else:
            result += str(frag)
    return result


def send_desktop_notification(title, body, urgency="critical"):
    """Send a Linux desktop notification via notify-send."""
    try:
        # Set DISPLAY and DBUS for cron/background compatibility
        env = os.environ.copy()
        env.setdefault("DISPLAY", ":0")
        # Try to find the DBUS session address
        dbus_file = f"/run/user/{os.getuid()}/bus"
        if os.path.exists(dbus_file):
            env.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path={dbus_file}")

        subprocess.run([
            "notify-send",
            "--urgency", urgency,
            "--icon", "mail-reply-sender",
            "--app-name", "Job Tracker 🎯",
            "-t", "30000",  # 30 seconds display
            title,
            body
        ], env=env, timeout=10)
        log(f"🔔 Desktop notification sent: {title}")
    except Exception as e:
        log(f"⚠️  Failed to send desktop notification: {e}")


def send_phone_push(title, body):
    """Optional phone push via ntfy. Enabled only when NTFY_TOPIC is set in .env."""
    topic = get_env_var("NTFY_TOPIC")
    if not topic:
        return False
    server = get_env_var("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
    try:
        req = urllib.request.Request(
            f"{server}/{topic}",
            data=body.encode("utf-8"),
            headers={"Title": title.encode("utf-8").decode("latin-1", "ignore"), "Priority": "high", "Tags": "tada"},
        )
        urllib.request.urlopen(req, timeout=10)
        log(f"📱 Phone push sent: {title}")
        return True
    except Exception as e:
        log(f"⚠️  Failed to send phone push: {e}")
        return False


def play_sound():
    """Play a notification sound if available."""
    try:
        sound_paths = [
            "/usr/share/sounds/freedesktop/stereo/message-new-instant.oga",
            "/usr/share/sounds/gnome/default/alerts/glass.ogg",
            "/usr/share/sounds/ubuntu/stereo/message-new-instant.ogg",
        ]
        for sound in sound_paths:
            if os.path.exists(sound):
                subprocess.Popen(
                    ["paplay", sound],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                break
    except Exception:
        pass


def classify_email(subject, body):
    """Classify email as Positive, Negative, or Neutral."""
    text = (subject + " " + body).lower()

    # Check positive signals first
    for kw in POSITIVE_KEYWORDS:
        if kw in text:
            if any(neg in text for neg in NEGATIVE_KEYWORDS):
                # Mixed signals — could be "unfortunately we cannot interview"
                return "Rejected", False, "Mixed signals — likely rejection"
            if "interview" in kw or "screening" in kw or "speak" in kw or "schedule" in kw or "chat" in kw or "round" in kw:
                return "Interview", True, "🎉 Interview / Screening invitation!"
            if "assessment" in kw or "hackerrank" in kw or "codility" in kw or "challenge" in kw or "take-home" in kw or "assignment" in kw:
                return "Assessment", True, "📝 Technical assessment received!"
            if "shortlisted" in kw or "selected" in kw:
                return "Shortlisted", True, "⭐ Profile shortlisted!"
            if "congratulations" in kw or "offer" in kw or "pleased" in kw or "joining" in kw or "compensation" in kw:
                return "Offer", True, "🏆 OFFER RECEIVED!"
            return "Positive Response", True, "✅ Positive response from company!"

    # Check negative signals
    for kw in NEGATIVE_KEYWORDS:
        if kw in text:
            return "Rejected", False, "Application not selected"

    # Check neutral (auto-replies)
    for kw in NEUTRAL_KEYWORDS:
        if kw in text:
            return "Under Review", False, "Auto-acknowledgement received"

    return "Contacted", False, "Company responded (unclassified)"


def scan_inbox(dry_run=False):
    """Scan Gmail inbox for replies from tracked companies."""
    email_user = "prajwathg@gmail.com"
    app_password = get_env_var("GMAIL_APP_PASSWORD")

    if not app_password:
        log("❌ Gmail App Password not found!")
        log("To enable reply monitoring:")
        log("1. Go to Google Account → Security → 2-Step Verification → App Passwords")
        log("2. Create an App Password for 'Career Ops'")
        log(f"3. Add to {ENV_FILE}:")
        log('   GMAIL_APP_PASSWORD="your-16-char-password"')
        log("")
        log("Sending test notification instead...")
        send_desktop_notification(
            "⚠️ Job Tracker — Setup Needed",
            "Gmail App Password not configured.\nAdd GMAIL_APP_PASSWORD to .env file to enable reply monitoring."
        )
        return []

    log(f"📬 Connecting to imap.gmail.com for {email_user}...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(email_user, app_password)
        mail.select("INBOX")
    except Exception as e:
        log(f"❌ Failed to connect to Gmail: {e}")
        send_desktop_notification(
            "❌ Job Tracker — Gmail Error",
            f"Could not connect to Gmail:\n{str(e)[:100]}"
        )
        return []

    # Load tracked companies
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        fieldnames = list(reader[0].keys()) if reader else []

    tracked_companies = {}
    for r in reader:
        comp_lower = r["Company"].lower()
        if comp_lower not in tracked_companies:
            tracked_companies[comp_lower] = r

    # Load previously seen email IDs
    seen_ids = load_seen_ids()

    log(f"🔍 Scanning inbox for replies from {len(tracked_companies)} tracked companies...")

    # Search emails from the last 7 days
    since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
    status, messages = mail.search(None, f'(SINCE {since_date})')
    if status != "OK":
        log("No messages found.")
        mail.close()
        mail.logout()
        return []

    mail_ids = messages[0].split()
    log(f"📩 Found {len(mail_ids)} emails in last 7 days")

    new_responses = []
    reverts_found = 0

    for m_id in reversed(mail_ids):
        m_id_str = m_id.decode() if isinstance(m_id, bytes) else str(m_id)

        # Skip already-seen emails
        if m_id_str in seen_ids:
            continue

        try:
            res, msg_data = mail.fetch(m_id, "(RFC822)")
            if res != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            sender = decode_mime_header(msg.get("From", ""))
            subject = decode_mime_header(msg.get("Subject", ""))
            msg_id = msg.get("Message-ID", m_id_str)
            body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                        except Exception:
                            pass
                        break
            else:
                try:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
                except Exception:
                    pass

            # Only match company name against the SENDER (not subject/body)
            # This avoids false positives from promo emails mentioning company names
            sender_lower = sender.lower()

            # Skip marketing / noreply / transactional senders
            BLOCKLIST_SENDERS = [
                "no-reply@", "noreply@", "no_reply@", "donotreply@",
                "newsletter@", "marketing@", "promo@", "deals@",
                "notifications@", "info@", "support@", "billing@",
                "alert@", "updates@", "mailer@", "campaign@",
                "shop@", "store@", "order@", "transaction@",
                "rmp.", "email.", "mail.", "bulk.", "edm."
            ]
            if any(blocked in sender_lower for blocked in BLOCKLIST_SENDERS):
                seen_ids.add(m_id_str)
                continue

            # Recruitment-related keywords that must appear in subject or body
            # to confirm this is a hiring-related email, not a promo
            RECRUITMENT_SIGNALS = [
                "interview", "screening call", "speak with you", "schedule a call",
                "your application", "your resume", "your candidat", "your profile",
                "position of", "role of", "hiring for", "recruit",
                "job opening", "opportunit", "shortlist",
                "assessment", "hackerrank", "codility", "take-home test", "coding assignment",
                "offer letter", "compensation package", "joining date", "onboard",
                "talent acquisition", "human resource", "next step", "move forward",
                "selected for", "congratulations on", "regret to inform",
                "not moving forward", "pursuing other candidates",
                "review your profile", "reviewed your application",
                "technical round", "round 1", "round 2", "panel interview"
            ]

            email_text = f"{subject} {body[:1000]}".lower()
            is_recruitment_email = any(kw in email_text for kw in RECRUITMENT_SIGNALS)

            for comp_name, app_row in tracked_companies.items():
                # Match company name ONLY in sender field (at least 3 chars)
                if len(comp_name) >= 3 and comp_name in sender_lower and is_recruitment_email:
                    status_cat, is_positive, note_text = classify_email(subject, body[:1000])

                    response_info = {
                        "company": app_row["Company"],
                        "app_id": app_row["Application_ID"],
                        "sender": sender,
                        "subject": subject[:80],
                        "status": status_cat,
                        "is_positive": is_positive,
                        "note": note_text
                    }
                    new_responses.append(response_info)

                    log(f"\n{'🟢' if is_positive else '🔴' if status_cat == 'Rejected' else '🟡'} "
                        f"[MATCH] {app_row['Company']} (#{app_row['Application_ID']})")
                    log(f"   From:    {sender[:60]}")
                    log(f"   Subject: {subject[:80]}")
                    log(f"   Status:  {status_cat} — {note_text}")

                    # Send desktop notification for POSITIVE responses
                    if is_positive:
                        send_desktop_notification(
                            f"{note_text}",
                            f"Company: {app_row['Company']}\n"
                            f"Role: {app_row['Job_Title']}\n"
                            f"Subject: {subject[:60]}\n"
                            f"From: {sender[:50]}",
                            urgency="critical"
                        )
                        send_phone_push(
                            f"Positive reply: {app_row['Company']}",
                            f"{note_text}\nRole: {app_row['Job_Title']}\nSubject: {subject[:60]}"
                        )
                        play_sound()

                    # Update CSV row
                    if not dry_run:
                        app_row["Status"] = status_cat
                        app_row["Reverted_Back"] = "Yes"
                        app_row["Response_Date"] = datetime.now().strftime("%Y-%m-%d")
                        app_row["Notes"] = f"{note_text} | {subject[:40]}"
                        reverts_found += 1

                    seen_ids.add(m_id_str)
                    break

        except Exception as e:
            log(f"⚠️  Error processing email {m_id_str}: {e}")
            continue

    mail.close()
    mail.logout()

    # Save seen IDs
    save_seen_ids(seen_ids)

    # Write updated CSV
    if reverts_found > 0 and not dry_run:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(reader)
        log(f"\n✅ Updated {reverts_found} applications in CSV!")

    # Summary notification
    positive_count = sum(1 for r in new_responses if r["is_positive"])
    if positive_count > 0:
        companies = ", ".join(r["company"] for r in new_responses if r["is_positive"])
        send_desktop_notification(
            f"🎯 {positive_count} Positive Response(s)!",
            f"Companies: {companies}\nCheck dashboard for details.",
            urgency="critical"
        )
    elif len(new_responses) > 0:
        log(f"\n📊 {len(new_responses)} responses found, but none positive (rejections/auto-replies)")
    else:
        log("\n📭 No new company responses found.")

    return new_responses


def watch_mode():
    """Continuously scan inbox at regular intervals."""
    log("=" * 60)
    log("🔔 REPLY MONITOR STARTED — Watching for company responses")
    log(f"   Scanning every {SCAN_INTERVAL // 60} minutes")
    log(f"   Tracking 205 companies from {CSV_FILE}")
    log(f"   Notifications: Desktop (notify-send)")
    log(f"   Log file: {LOG_FILE}")
    log("=" * 60)

    send_desktop_notification(
        "🔔 Job Reply Monitor Active",
        "Watching your inbox for company responses.\n"
        f"Checking every {SCAN_INTERVAL // 60} minutes.\n"
        "You'll get a notification for any positive response!",
        urgency="normal"
    )

    def handle_sigint(sig, frame):
        log("\n🛑 Reply monitor stopped by user.")
        send_desktop_notification(
            "🛑 Job Reply Monitor Stopped",
            "No longer watching for company responses.",
            urgency="low"
        )
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    scan_count = 0
    while True:
        scan_count += 1
        log(f"\n--- Scan #{scan_count} ---")
        try:
            scan_inbox(dry_run=False)
        except Exception as e:
            log(f"❌ Scan failed: {e}")

        next_scan = datetime.now() + timedelta(seconds=SCAN_INTERVAL)
        log(f"💤 Next scan at {next_scan.strftime('%H:%M:%S')}")
        time.sleep(SCAN_INTERVAL)


def main():
    if "--test-push" in sys.argv:
        if not get_env_var("NTFY_TOPIC"):
            print("NTFY_TOPIC is not set in .env")
            sys.exit(1)
        ok = send_phone_push("Job tracker test", "Phone push is working. You will get a push for each positive reply.")
        sys.exit(0 if ok else 1)

    if "--watch" in sys.argv:
        watch_mode()
    else:
        dry_run = "--dry-run" in sys.argv
        results = scan_inbox(dry_run=dry_run)
        if results:
            print(f"\n📊 Summary: {len(results)} responses found")
            for r in results:
                icon = "🟢" if r["is_positive"] else "🔴" if r["status"] == "Rejected" else "🟡"
                print(f"  {icon} {r['company']} — {r['status']} — {r['note']}")


if __name__ == "__main__":
    main()
