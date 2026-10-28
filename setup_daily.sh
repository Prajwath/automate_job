#!/usr/bin/env bash
# Installs a systemd user timer that runs daily_run.sh every day at 10:00.
# If the computer is off at 10:00, it runs as soon as it's back on.
#   bash setup_daily.sh            # install / update
#   bash setup_daily.sh --remove   # uninstall
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
if [ "${1:-}" = "--remove" ]; then
  systemctl --user disable --now job-daily.timer 2>/dev/null || true
  rm -f "$UNIT_DIR/job-daily.service" "$UNIT_DIR/job-daily.timer"
  systemctl --user daemon-reload
  echo "Daily job run removed."; exit 0
fi
chmod +x "$DIR/daily_run.sh"
mkdir -p "$UNIT_DIR"
cat > "$UNIT_DIR/job-daily.service" <<UNIT
[Unit]
Description=Daily job discovery and applications
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$DIR
Environment=PYTHON=$(command -v python3)
ExecStart=/bin/bash $DIR/daily_run.sh
StandardOutput=append:$DIR/daily_run.log
StandardError=append:$DIR/daily_run.log
TimeoutStartSec=3h
UNIT
cat > "$UNIT_DIR/job-daily.timer" <<UNIT
[Unit]
Description=Run the job applications every day at 10:00

[Timer]
OnCalendar=*-*-* 10:00:00
Persistent=true

[Install]
WantedBy=timers.target
UNIT
systemctl --user daemon-reload
systemctl --user enable --now job-daily.timer
echo "Installed. Next run:"
systemctl --user list-timers job-daily.timer --no-pager
echo "Run it now with: systemctl --user start job-daily.service   (log: $DIR/daily_run.log)"
