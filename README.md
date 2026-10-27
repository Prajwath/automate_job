# 🚀 Automate Job — Application & Outreach Intelligence Suite

An end-to-end automated job application pipeline, resume tailoring engine, interactive tracking dashboard, and real-time response monitoring service.

---

## 🌟 Key Features

1. **Targeted Job Application Pipeline (205 Applications Tracked)**
   - **Cohort 1:** 50 Top Bangalore Tech & Product Companies (Anthropic, Mistral AI, Cohere, PhonePe, Infosys BPM, etc.)
   - **Cohort 2:** 50 Growing Mid-Size Tech Firms (Zeta, Observe.AI, Yellow.ai, Innovaccer, MoEngage, etc.)
   - **Cohort 3:** 50 High-Growth Funded Startups (Portkey.ai, TrueFoundry, Composio.ai, Sarvam AI, Krutrim, etc.)
   - **Cohort 4:** 50 Tier-1 Goodies & High-Perk Companies (Google, Microsoft, Apple, Meta, Flipkart, Swiggy, CRED, Razorpay, etc.)

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
├── job_applications.csv                  # Master CSV tracking all 205 applications
├── candidate_profile.json                # Structured candidate profile & skills data
├── dashboard.html                        # Self-contained web tracker dashboard
├── serve_dashboard.py                    # Local HTTP server (port 5050)
├── tailor_resume.py                      # Resume keyword & JD tailoring engine
├── generate_50_bangalore_applications.py # Batch 1 generator: Bangalore tech
├── expand_to_100_applications.py         # Batch 2 generator: Mid-size firms
├── add_50_startups.py                    # Batch 3 generator: Funded startups
├── add_50_goodies_companies.py           # Batch 4 generator: High-perk companies
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

### 6. Enable Background Service (Systemd)
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

| Cohort | Application IDs | Count | Focus |
|---|---|---|---|
| Bangalore Established Tech | 1–50 | 50 | Product & Enterprise |
| Mid-Size Growing Tech | 51–100 | 50 | SaaS, Platform & FinTech |
| Additional Direct Additions | 101–105 | 5 | Targeted High-LPA Roles |
| Funded AI & Tech Startups | 106–155 | 50 | LLM, GenAI, MLOps, Backend |
| Joining Goodies & High Perks | 156–205 | 50 | MacBooks, Devices, Top Perks |
| **Total** | | **205** | **Target CTC: ₹12–15 LPA** |
