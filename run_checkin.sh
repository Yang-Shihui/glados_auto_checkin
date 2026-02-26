#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
PYTHON=$(command -v python3 || echo /usr/bin/python3)
LOGFILE="$(pwd)/daily_checkin.log"
echo "======== $(date -Iseconds) ========" >> "$LOGFILE"
"${PYTHON}" auto_checkin.py -c config.json --debug >> "$LOGFILE" 2>&1 || echo "checkin exit $?: $(date -Iseconds)" >> "$LOGFILE"
