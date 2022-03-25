#!/bin/bash -e

YESTERDAY=$(date --date="yesterday" +"%Y-%m-%d")
WHEN=${1:-$YESTERDAY}

cd "$(dirname "$0")"
poetry run ./manage.py show_changes "$WHEN" | mail \
  -s "KeepUkraineConnected changes of $WHEN" \
  -a "From: GNA web server <noreply@nogalliance.org>" \
  ukraine@nogalliance.org
