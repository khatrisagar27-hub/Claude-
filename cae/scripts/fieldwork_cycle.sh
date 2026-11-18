#!/usr/bin/env bash
# Run one unattended audit-fieldwork cycle per client (see docs/fieldwork-agents.md).
#
# Run it on the machine that hosts the CAE stack, because it talks to
# localhost:8080. Example crontab entry (06:40, Monday to Saturday):
#
#   40 6 * * 1-6  /path/to/repo/cae/scripts/fieldwork_cycle.sh >> /path/to/repo/cae/fieldwork/cron.log 2>&1
#
# Credentials come from cae/fieldwork/.env, which git ignores and you create:
#   CAE_EMAIL=...  CAE_PASSWORD=...  [CAE_URL=...]  [CAE_SMTP_HOST=... CAE_SMTP_PORT=587
#   CAE_SMTP_USER=... CAE_SMTP_PASSWORD=... CAE_MAIL_FROM=...]
#
# Usage: fieldwork_cycle.sh [client ...]   (no arguments runs every client folder)
set -euo pipefail

cd "$(dirname "$0")/../.."   # repository root: the agents call cae/scripts/caectl.py
ENV_FILE="cae/fieldwork/.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a; source "$ENV_FILE"; set +a
fi
: "${CAE_EMAIL:?set CAE_EMAIL in $ENV_FILE}"
: "${CAE_PASSWORD:?set CAE_PASSWORD in $ENV_FILE}"

clients=("$@")
if [[ ${#clients[@]} -eq 0 ]]; then
  for f in cae/fieldwork/*/engagement.json; do
    [[ -e "$f" ]] && clients+=("$(basename "$(dirname "$f")")")
  done
fi
if [[ ${#clients[@]} -eq 0 ]]; then
  echo "no clients: create cae/fieldwork/<client>/engagement.json (run /fieldwork setup <client>)" >&2
  exit 1
fi

# The only tools an unattended run gets: caectl, reading files, writing inside
# cae/fieldwork/, and spawning the fw-* subagents. Everything else is denied.
ALLOWED='Bash(python3 cae/scripts/caectl.py:*),Read,Glob,Grep,Edit(cae/fieldwork/**),Write(cae/fieldwork/**),Agent'

status=0
for client in "${clients[@]}"; do
  echo "=== $(date '+%F %T') fieldwork: $client"
  if ! claude -p "/fieldwork run $client" --allowedTools "$ALLOWED"; then
    echo "!!! fieldwork run failed for $client" >&2
    status=1
  fi
done
exit $status
