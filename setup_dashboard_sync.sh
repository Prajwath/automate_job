#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
key="$root/.dashboard-sync/id_ed25519"
if [[ ! -f "$key" || ! -f "$root/.dashboard-sync/known_hosts" ]]; then
  echo 'Configure a repository write deploy key and verified GitHub known_hosts in .dashboard-sync first.' >&2
  exit 1
fi
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/job-dashboard-publish.service" <<EOF
[Unit]
Description=Publish minimized job dashboard updates
After=network-online.target

[Service]
Type=simple
WorkingDirectory=$root
Environment="GIT_SSH_COMMAND=ssh -i '$key' -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile='$root/.dashboard-sync/known_hosts'"
ExecStart=/usr/bin/python3 "$root/publish_dashboard.py" --watch
Restart=on-failure
RestartSec=15

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now job-dashboard-publish.service
