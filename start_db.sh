#!/usr/bin/env bash
# Start just PostgreSQL
cd /home/david/workspace/projects/rateeverything
if ! pg_isready -p 5433 -h /tmp -q 2>/dev/null; then
  exec pg_ctl -D pgdata -l pgdata/logfile start -o '-p 5433 -k /tmp'
  echo "PostgreSQL started on port 5433"
else
  echo "PostgreSQL already running on port 5433"
fi
