# 🚀 Automate Job — Application & Outreach Intelligence Suite

An end-to-end automated job application pipeline, resume tailoring engine, interactive tracking dashboard, and real-time response monitoring service.

---

## 🌟 Key Features

1. **Job Tracker (`job_applications.csv`)**
   - 50 real hybrid Bangalore postings (`add_50_hybrid_bangalore.py`), each with a link and a fit note (Strong fit / Good fit / Stretch / Weak fit).
   - New roles start as **To Apply**; set Status to `Applied` and fill `Date_Applied` once you submit.

2. **Resume Tailoring Engine (`tailor_resume.py`)**
   - Extracts job descriptions and aligns specific technical competencies (FinBERT, RAG pipelines, OCR, multi-agent AI, Python/FastAPI microservices).
   - Generates tailored application notes and keywords per submission.

3. **Self-Contained Live Dashboard (`dashboard.html` & `serve_dashboard.py`)**
   - High-performance, zero-external-dependency local web dashboard.
   - Search, filter by category/role/status, CTC metrics, and real-time application status.
   - Served on port 5050.

4. **24/7 Response Monitor & Linux Desktop Alerts (`notify_replies.py`)**
   - Connects to Gmail via IMAP with smart sentiment classification.
   - Filters out promotional/marketing emails to eliminate false positives.
   - Detects positive interview, assessment, and offer signals.
   - Fires native desktop notifications via `notify-send` with sound and auto-updates `job_applications.csv`.
   - Runs continuously as a systemd user daemon.

---

## 📂 Project Architecture

```
├── job_applications.csv                  # Master CSV of tracked roles
├── candidate_profile.json                # Structured candidate profile & skills data
├── dashboard.html                        # Self-contained web tracker dashboard
├── serve_dashboard.py                    # Local HTTP server (port 5050)
├── auto_apply.py                         # Fills Greenhouse/Lever/Ashby forms from applicant.txt
├── email_otp.py                          # Reads emailed verification codes from Gmail and enters them
├── discover_jobs.py                      # Finds new 1-4 yr hybrid Bangalore roles from companies.txt
├── phone_actions.py                      # Phone hand-off: ntfy buttons to open, mark applied or skip
├── daily_run.sh / setup_daily.sh         # Daily 10:00 autopilot and its installer
├── form_agent.py                         # AI agent (Gemini or Claude) that answers every remaining form question
├── tailor_resume.py                      # Resume keyword & JD tailoring engine
├── add_50_hybrid_bangalore.py            # Adds 50 real hybrid Bangalore postings as To Apply
├── email_sender.py                       # Automated email application sender
├── check_replies.py                      # One-shot IMAP inbox reply scanner
├── notify_replies.py                     # Real-time daemon with desktop alerts
├── tracker.py                            # CLI management utility
├── sync_trackers.py                      # Synchronization engine
├── context.md                            # Comprehensive workflow and design context
└── .env.example                          # Environment template
```

---

## 🛠️ Quick Start

### 1. Configure Credentials
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your Gmail credentials and 16-character Google App Password:
```env
GMAIL_USER="your-email@gmail.com"
GMAIL_APP_PASSWORD="your-16-char-app-password"
```

### 2. Launch the Application Tracker Dashboard
```bash
python3 serve_dashboard.py
```
Open [http://localhost:5050/dashboard.html](http://localhost:5050/dashboard.html) in your browser.

### 3. Run the Reply Monitor
Run a single scan:
```bash
python3 notify_replies.py
```
Run continuously in watch mode (every 15 minutes):
```bash
python3 notify_replies.py --watch
```

### 4. Phone Alerts for Positive Replies (optional)
Get a push on your phone when a positive reply arrives, using [ntfy](https://ntfy.sh):
1. Install the ntfy app and subscribe to a long, random topic name.
2. Add it to `.env`: `NTFY_TOPIC="your-random-topic"` (topics have no password, so don't use a guessable name).
3. Test it: `python3 notify_replies.py --test-push`

The dashboard also has a **🔔 Alerts** button that shows a browser notification for new positive replies while the page is open. The By batch / By channel analysis panels are hidden; add `?analysis=1` to the dashboard URL to show them.

### 5. Keep the Live Dashboard Updated
After each scan, `notify_replies.py` commits and pushes `job_applications.csv` to GitHub when replies were found, so the GitHub Pages / Vercel dashboard updates automatically. The project folder must be a git clone that can push without a password prompt (SSH key or saved credentials). If a push fails, it is retried on the next scan. The repo is public, so reply statuses become public; set `AUTO_PUSH="false"` in `.env` to turn this off.

### 6. Fill Applications Automatically (Greenhouse, Lever, Ashby)
```bash
pip install playwright && python3 -m playwright install chromium
cp applicant.example.txt applicant.txt   # fill in your details (git-ignored)
python3 auto_apply.py --dry-run          # see which roles it will open
python3 auto_apply.py                    # fills each form; you check it and click Submit
```
It uploads your resume, answers standard questions and writes a short tailored "why this company" answer.

**AI form agent (`form_agent.py`):** with `pip install google-genai` and `GEMINI_API_KEY` in `.env` (Gemini 2.5 Flash), or `pip install anthropic` and `ANTHROPIC_API_KEY` (Claude), the AI reads your resume PDF and `applicant.txt` and answers every remaining question — dropdowns, radio buttons, checkbox groups, searchable dropdowns, consent boxes and custom free-text questions — using only facts from your resume. Fields matching "Never auto-fill" are never sent to Claude. Use `--no-ai` to turn it off.

**Email verification codes (`email_otp.py`):** in `--auto-submit` mode, if a form asks for a code emailed to you after Submit, the script reads it from your Gmail (needs `GMAIL_APP_PASSWORD` in `.env`, same as the reply monitor), types it in and submits again. SMS codes and captchas still need you. If both keys are set, choose with `AI_PROVIDER="gemini"` or `"claude"`. Questions it can't answer and captchas are left for you. `--auto-submit` submits by itself when every required field is filled and there is no captcha. Successful applications are marked `Applied` and the CSV is pushed. Stretch / weak-fit roles are skipped unless you pass `--include-stretch`. Workday, company sites and aggregators are skipped — apply to those by hand.

### 7. Daily Autopilot at 10:00 (with phone hand-off)
```bash
bash setup_daily.sh          # installs a systemd timer; runs daily at 10:00 (or at next boot if missed)
systemctl --user start job-daily.service   # run once now; log in daily_run.log
```
Each day `daily_run.sh`:
1. applies your phone taps (**Mark applied** / **Skip**),
2. finds new hybrid Bangalore roles needing 1–4 years on the boards in `companies.txt` (`discover_jobs.py`),
3. fills and submits applications in the background (`auto_apply.py --unattended --junior-only`), including emailed verification codes,
4. pushes the tracker so the dashboard updates, and sends a summary to your phone.

Anything that needs you — a captcha, a question the AI couldn't answer, Workday or other sites — is marked **Needs You** and sent to your phone (ntfy) with **Open form**, **Mark applied** and **Skip** buttons. Finish the form in your phone's browser, then tap **Mark applied**. Taps are picked up by the reply monitor within 15 minutes, or by the next daily run. Add or remove companies in `companies.txt`. Remove the schedule with `bash setup_daily.sh --remove`.

### 8. Enable Background Service (Systemd)
To run the reply monitor 24/7 in the background across reboots:
```bash
mkdir -p ~/.config/systemd/user
cat << 'EOF' > ~/.config/systemd/user/job-reply-monitor.service
[Unit]
Description=Job Application Reply Monitor — Desktop Notifications
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/notify_replies.py --watch
WorkingDirectory=/path/to/automate_job
Restart=on-failure
RestartSec=60
Environment=DISPLAY=:0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now job-reply-monitor.service
```

---

## 📊 Summary of Tracked Applications

| Group | Application IDs | Count | Status |
|---|---|---|---|
| Hybrid Bangalore (real postings) | 1–50 | 50 | To Apply — found via web search, Oct 2026 |
| **Total** | | **50** | **Target CTC: ₹12–15 LPA** |
