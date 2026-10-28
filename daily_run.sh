#!/usr/bin/env bash
# Daily job run (installed by setup_daily.sh, runs at 10:00):
#   1. pull the latest tracker   2. apply phone "Mark applied"/"Skip" taps
#   3. find new 1-4 yr hybrid Bangalore roles   4. fill and submit applications
#   5. push the updated tracker so the dashboard updates
set -u
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
echo "===== $(date) ====="
git pull --rebase --autostash -q || echo "git pull failed, continuing with local copy"
$PY phone_actions.py
$PY discover_jobs.py
$PY auto_apply.py --unattended --junior-only
$PY -c "from notify_replies import push_csv_to_github; push_csv_to_github()"
