#!/usr/bin/env python3
"""
Phone hand-off for the daily run, using ntfy (NTFY_TOPIC in .env).

When a form needs you (captcha, a question the AI couldn't answer, a Workday
login), the daily run marks the row "Needs You" and sends a push with three
buttons:
  Open form     -> opens the application in your phone's browser to finish it
  Mark applied  -> records it as Applied
  Skip          -> records it as Skipped

Button taps are posted to a second ntfy topic (<NTFY_TOPIC>-actions). They are
applied to job_applications.csv by `python3 phone_actions.py`, which the daily
run and the reply monitor both call.
"""

import os
import csv
import json
import urllib.request
from datetime import datetime

from notify_replies import get_env_var, log

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(ROOT_DIR, "job_applications.csv")
STATE_FILE = os.path.join(ROOT_DIR, ".phone_actions_state.json")


def _server_topic():
    topic = get_env_var("NTFY_TOPIC")
    server = get_env_var("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
    return server, topic


def _post(url, body, headers):
    req = urllib.request.Request(url, data=body.encode("utf-8"), headers=headers)
    urllib.request.urlopen(req, timeout=10)


def _ascii(text):
    # ntfy headers must be latin-1; emoji go in the body instead
    return text.encode("latin-1", "ignore").decode("latin-1")


def send_needs_you(row, reason):
    """Push a 'finish this on your phone' notification with action buttons."""
    server, topic = _server_topic()
    if not topic:
        return False
    actions_url = f"{server}/{topic}-actions"
    app_id = row["Application_ID"]
    actions = "; ".join([
        f"view, Open form, {row['Job_URL']}",
        f"http, Mark applied, {actions_url}, method=POST, body=applied {app_id}, clear=true",
        f"http, Skip, {actions_url}, method=POST, body=skip {app_id}, clear=true",
    ])
    try:
        _post(f"{server}/{topic}",
              f"{row['Company']} — {row['Job_Title']}\nNeeds you: {reason}\nOpen the form, finish it, then tap Mark applied.",
              {"Title": _ascii(f"Finish application #{app_id}: {row['Company']}"), "Tags": "memo", "Actions": _ascii(actions)})
        return True
    except Exception as e:
        log(f"⚠️  Failed to send phone hand-off: {e}")
        return False


def send_summary(text):
    server, topic = _server_topic()
    if not topic:
        return
    try:
        _post(f"{server}/{topic}", text, {"Title": "Daily job run", "Tags": "briefcase"})
    except Exception as e:
        log(f"⚠️  Failed to send daily summary: {e}")


def _load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def fetch_actions():
    """Button taps since the last check, oldest first, as (action, app_id) pairs."""
    server, topic = _server_topic()
    if not topic:
        return []
    state = _load_state()
    since = state.get("last_id") or "48h"
    req = urllib.request.Request(f"{server}/{topic}-actions/json?poll=1&since={since}")
    with urllib.request.urlopen(req, timeout=20) as r:
        lines = r.read().decode("utf-8").splitlines()
    out, last_id = [], state.get("last_id")
    for line in lines:
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if msg.get("event") != "message":
            continue
        last_id = msg.get("id", last_id)
        parts = (msg.get("message") or "").split()
        if len(parts) == 2 and parts[0] in ("applied", "skip") and parts[1].isdigit():
            out.append((parts[0], parts[1]))
    if last_id:
        with open(STATE_FILE, "w") as f:
            json.dump({"last_id": last_id}, f)
    return out


def apply_actions(actions):
    """Write button taps into the CSV. Returns how many rows changed."""
    if not actions:
        return 0
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames, rows = reader.fieldnames, list(reader)
    by_id = {r["Application_ID"]: r for r in rows}
    email = get_env_var("GMAIL_USER") or "prajwathg@gmail.com"
    changed = 0
    for action, app_id in actions:
        r = by_id.get(app_id)
        if not r or r["Status"] in ("Applied", "Skipped"):
            continue
        if action == "applied":
            r["Status"], r["Date_Applied"], r["Sender_Email"] = "Applied", datetime.now().strftime("%Y-%m-%d"), email
        else:
            r["Status"] = "Skipped"
        changed += 1
        log(f"📱 #{app_id} {r['Company']}: marked {r['Status']} from your phone")
    if changed:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    return changed


def process_phone_actions():
    try:
        return apply_actions(fetch_actions())
    except Exception as e:
        log(f"⚠️  Could not read phone actions: {e}")
        return 0


if __name__ == "__main__":
    print(f"{process_phone_actions()} row(s) updated from phone")
