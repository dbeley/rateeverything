#!/usr/bin/env bash
# Start just the frontend
cd /home/david/workspace/projects/rateeverything/frontend
exec nix-shell -p nodejs_22 pnpm --command "pnpm dev --port 3000 2>&1"
