#!/usr/bin/env bash
# RateEverything — Démarrage sur NixOS
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export DATABASE_URL="postgresql+asyncpg://rateeverything@/rateeverything?host=/tmp&port=5433"
export LD_LIBRARY_PATH="/nix/store/chqq8mpmpyfi9kgsngya71akv5xicn03-gcc-15.2.0-lib/lib"

echo "🚀 RateEverything — Déploiement local"
echo ""

# 1. PostgreSQL
echo "📦 PostgreSQL..."
cd "$SCRIPT_DIR"
if ! pg_isready -p 5433 -h /tmp -q 2>/dev/null; then
  pg_ctl -D pgdata -l pgdata/logfile start -o '-p 5433 -k /tmp' 2>/dev/null
  echo "   ✅ PostgreSQL démarré (port 5433)"
else
  echo "   ✅ PostgreSQL déjà en marche"
fi

# Wait for PG
sleep 1

# 2. Backend
echo "🔧 Backend..."
cd "$SCRIPT_DIR/backend"
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "   ✅ Backend démarré (PID $BACKEND_PID, port 8000)"

# 3. Frontend
echo "🎨 Frontend..."
cd "$SCRIPT_DIR/frontend"
pnpm dev --port 3000 &
FRONTEND_PID=$!
echo "   ✅ Frontend démarré (PID $FRONTEND_PID, port 3000)"

# Wait for backend
sleep 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ RateEverything en ligne !"
echo "  🌐 Frontend : http://localhost:3000"
echo "  🔌 API      : http://localhost:8000/api"
echo "  🗄️  PostgreSQL: port 5433"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter."

# Wait for either process
wait $BACKEND_PID $FRONTEND_PID
