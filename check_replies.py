#!/usr/bin/env python3
"""
Automated Reply & Revert Scanner for Prajwath Gowda (prajwathg@gmail.com)
Connects to Gmail via IMAP, matches emails against applied companies,
and automatically updates job_applications.csv and the live dashboard.
"""

import os
import sys
import csv
import imaplib
import email
from email.header import decode_header
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(ROOT_DIR, "job_applications.csv")
ENV_FILE = os.path.join(ROOT_DIR, ".env")

def get_env_var(key, default=""):
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(key, default)

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

def classify_email(subject, body):
    text = (subject + " " + body).lower()
    
    # Interview / Next round signals
    if any(w in text for w in ["interview", "screening", "speak with you", "schedule a call", "invitation to interview", "round 1", "technical round", "chat with the team"]):
        return "Interview", "Interview / Screening invitation received"
    
    # Coding assessment signals
    if any(w in text for w in ["assessment", "hackerrank", "codility", "test link", "coding challenge", "take-home"]):
        return "Assessment", "Technical assessment / coding challenge received"
    
    # Rejection signals
    if any(w in text for w in ["unfortunately", "not moving forward", "pursuing other candidates", "regret to inform", "other applicants"]):
        return "Rejected", "Application closed / not selected"
    
    # Under review / HR outreach
    if any(w in text for w in ["application received", "reviewing your application", "received your resume", "profile shortlisted"]):
        return "Under Review", "Application received & under review"

    return "Contacted", "Company responded via email"

def scan_inbox(dry_run=False):
    email_user = "prajwathg@gmail.com"
    app_password = get_env_var("GMAIL_APP_PASSWORD")

    if not app_password:
        print("\n[NOTE] Gmail App Password not found in .env")
        print("To enable automatic inbox reply detection:")
        print("1. Go to your Google Account -> Security -> 2-Step Verification -> App Passwords")
        print("2. Create an App Password for 'Career Ops'")
        print(f"3. Add it to {ENV_FILE}:")
        print('   GMAIL_APP_PASSWORD="your-16-char-password"\n')
        print("Until then, you can record reverts manually via:")
        print("   python3 tracker.py respond --id <ID> --status <Status> --notes <Notes>\n")
        return

    print(f"Connecting to imap.gmail.com for {email_user}...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(email_user, app_password)
        mail.select("INBOX")
    except Exception as e:
        print(f"Failed to connect to Gmail: {e}")
        return

    # Load all tracked companies
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys() if reader else []

    tracked_companies = {r["Company"].lower(): r for r in reader}

    print(f"Scanning inbox for replies from {len(tracked_companies)} tracked companies...")
    
    # Search recent emails (last 14 days)
    today = datetime.now().strftime("%Y-%m-%d")
    status, messages = mail.search(None, 'ALL')
    if status != 'OK':
        print("No messages found.")
        return

    mail_ids = messages[0].split()
    # Check the last 50 emails
    recent_ids = mail_ids[-50:] if len(mail_ids) > 50 else mail_ids
    recent_ids.reverse()

    reverts_found = 0

    for m_id in recent_ids:
        res, msg_data = mail.fetch(m_id, "(RFC822)")
        if res != 'OK':
            continue

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        sender = decode_mime_header(msg.get("From", ""))
        subject = decode_mime_header(msg.get("Subject", ""))
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

        # Check if sender or subject matches any of our 105 tracked companies
        searchable_text = f"{sender} {subject} {body[:500]}".lower()

        for comp_name, app_row in tracked_companies.items():
            if comp_name in searchable_text:
                status_cat, note_text = classify_email(subject, body[:500])
                print(f"\n[MATCH FOUND] Company: {app_row['Company']} (#{app_row['Application_ID']})")
                print(f"  Sender:  {sender}")
                print(f"  Subject: {subject}")
                print(f"  Outcome: {status_cat} ({note_text})")

                if not dry_run:
                    app_row["Status"] = status_cat
                    app_row["Reverted_Back"] = "Yes"
                    app_row["Response_Date"] = today
                    app_row["Notes"] = f"{note_text} | Subject: {subject[:40]}"
                    reverts_found += 1
                break

    mail.close()
    mail.logout()

    if reverts_found > 0 and not dry_run:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(reader)
        print(f"\nUpdated {reverts_found} applications in {CSV_FILE} with company responses!")
    else:
        print("\nScan completed. No new incoming company responses found.")

def main():
    dry_run = "--dry-run" in sys.argv
    scan_inbox(dry_run=dry_run)

if __name__ == "__main__":
    main()
