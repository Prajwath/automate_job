#!/usr/bin/env bash
# Daily job run (installed by setup_daily.sh, runs at 10:00):
#   1. apply phone actions   2. discover matching roles
#   3. fill and submit applications   4. publish only when explicitly enabled
set -u
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
echo "===== $(date) ====="
# Update source code separately. Pulling here can overwrite the private tracker
# and leave an unattended rebase in the application workspace.
$PY phone_actions.py
$PY discover_jobs.py
$PY auto_apply.py --unattended --junior-only
$PY linkedin_apply.py --scheduled --max 10 || echo "LinkedIn stopped; check auto_apply.log for details"
$PY -c "from notify_replies import push_csv_to_github; push_csv_to_github()"
