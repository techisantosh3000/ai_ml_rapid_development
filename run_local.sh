#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

INSTALL_DEPS=false
SKIP_TESTS=false

for arg in "$@"; do
  case $arg in
    --install-deps) INSTALL_DEPS=true ;;
    --skip-tests) SKIP_TESTS=true ;;
  esac
done

echo "================================================================="
echo " Hybrid AI/ML Bootcamp & Multi-Domain Triage Launcher (Bash)"
echo "================================================================="

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "[1/5] Created .env from .env.example"
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
echo "[2/5] Activated .venv ($(python --version))"

if [ "$INSTALL_DEPS" = true ]; then
  echo "[3/5] Installing dependencies from requirements.txt..."
  python -m pip install --upgrade pip
  pip install -r requirements.txt
fi

if [ "$SKIP_TESTS" = false ] && [ -f "tests/test_all_domains.py" ]; then
  echo "[4/5] Running pytest regression suite..."
  pytest -q
fi

echo "[5/5] Starting Arize Phoenix (6008) & FastAPI/Gradio (8000)..."
PHOENIX_PORT=6008 PHOENIX_GRPC_PORT=14317 phoenix serve >/tmp/phoenix.log 2>&1 &
PHOENIX_PID=$!
trap "kill $PHOENIX_PID 2>/dev/null || true" EXIT

sleep 2
echo "Gradio UI: http://127.0.0.1:8000/ui | Phoenix UI: http://127.0.0.1:6008"
uvicorn app.main:app --host 127.0.0.1 --port 8000
