#!/bin/bash -e

# Use gnaukraine user
HOME=$(/usr/bin/realpath ~gnaukraine)
export HOME

YESTERDAY=$(date --date="yesterday" +"%Y-%m-%d")
WHEN=${1:-$YESTERDAY}

cd "$(/usr/bin/dirname "$0")"
/usr/local/bin/poetry run ./manage.py show_changes "$WHEN" | /usr/bin/mail \
  -s "KeepUkraineConnected changes of $WHEN" \
  -a "From: GNA web server <noreply@nogalliance.org>" \
  ukraine@nogalliance.org
