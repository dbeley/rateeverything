#!/usr/bin/env bash
# Start just the backend
cd /home/david/workspace/projects/rateeverything/backend
source .venv/bin/activate
export DATABASE_URL="postgresql+asyncpg://rateeverything@/rateeverything?host=/tmp&port=5433"
export LD_LIBRARY_PATH="/nix/store/chqq8mpmpyfi9kgsngya71akv5xicn03-gcc-15.2.0-lib/lib"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
