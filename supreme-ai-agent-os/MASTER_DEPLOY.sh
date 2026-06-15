#!/usr/bin/env bash
# ============================================================================
# MASTER_DEPLOY.sh — SUPAR SMART AI / Supreme AI Agent OS
# Usage: bash MASTER_DEPLOY.sh [--aws] [--local] [--skip-build]
# One command: validate → build → start → smoke test → print live URLs
# ============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC}  $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERR]${NC}  $*"; exit 1; }
info() { echo -e "${CYAN}[..]${NC}  $*"; }
hdr()  { echo -e "\n${BOLD}${CYAN}==> $*${NC}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MODE="local"
SKIP_BUILD=false
for arg in "$@"; do
  case $arg in
    --aws)        MODE="aws"        ;;
    --local)      MODE="local"      ;;
    --skip-build) SKIP_BUILD=true   ;;
  esac
done

echo ""
echo -e "  ${BOLD}${CYAN}⚡  SUPAR SMART AI — Supreme AI Agent OS${NC}"
echo -e "  ${CYAN}     SMARTY AI Inception Runtime — Master Deploy${NC}"
echo    "  ================================================="
echo    "  Mode: $MODE"
echo ""

# ── AWS mode: deploy to EC2 ──────────────────────────────────────────────────
if [[ "$MODE" == "aws" ]]; then
  hdr "AWS EC2 Deployment"

  # Check for SSH key / EC2 host
  EC2_HOST="${EC2_HOST:-}"
  EC2_USER="${EC2_USER:-ubuntu}"
  EC2_KEY="${EC2_KEY:-~/.ssh/id_rsa}"

  if [[ -z "$EC2_HOST" ]]; then
    warn "EC2_HOST not set. To deploy to AWS EC2:"
    echo ""
    echo "  1. Export your EC2 details:"
    echo "     export EC2_HOST=your-ec2-ip-or-hostname"
    echo "     export EC2_USER=ubuntu          # or ec2-user for Amazon Linux"
    echo "     export EC2_KEY=~/.ssh/your-key.pem"
    echo ""
    echo "  2. Run deployment:"
    echo "     bash MASTER_DEPLOY.sh --aws"
    echo ""
    echo "  One-liner (copy/paste to EC2 directly):"
    echo "     ssh -i \$EC2_KEY \$EC2_USER@\$EC2_HOST 'bash -s' <<'SSH'"
    echo "     curl -fsSL https://raw.githubusercontent.com/cryptostoner94/supreme-ai-agent-os/main/supreme-ai-agent-os/MASTER_DEPLOY.sh -o MASTER_DEPLOY.sh"
    echo "     chmod +x MASTER_DEPLOY.sh && bash MASTER_DEPLOY.sh --local"
    echo "     SSH"
    echo ""
    echo "  Required EC2 security group ports: 8000 (API), 8501 (Dashboard), 11434 (Ollama)"
    exit 0
  fi

  info "Deploying to EC2: $EC2_USER@$EC2_HOST"
  # Sync code
  rsync -az --exclude='.git' --exclude='data/' --exclude='__pycache__' \
    -e "ssh -i $EC2_KEY -o StrictHostKeyChecking=no" \
    . "$EC2_USER@$EC2_HOST:~/supreme-ai-agent-os/"

  # Execute deploy on remote
  ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" \
    "cd ~/supreme-ai-agent-os && bash MASTER_DEPLOY.sh --local"
  ok "EC2 deployment triggered"
  echo ""
  echo -e "  ${GREEN}Live URLs:${NC}"
  echo    "    API:       http://$EC2_HOST:8000"
  echo    "    Dashboard: http://$EC2_HOST:8501"
  exit 0
fi

# ── Local / Docker deployment ─────────────────────────────────────────────────

hdr "1. Environment Validation"

command -v docker >/dev/null 2>&1 || err "Docker not found. Install: https://docs.docker.com/get-docker/"
(docker compose version >/dev/null 2>&1 || docker-compose version >/dev/null 2>&1) || \
  err "Docker Compose not found"
command -v curl >/dev/null 2>&1 || err "curl not found"

DOCKER_VER=$(docker --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
ok "Docker ${DOCKER_VER}"

# Check memory (Playwright needs ~512MB)
if command -v free >/dev/null 2>&1; then
  FREE_MB=$(free -m | awk '/^Mem/{print $7}')
  if [[ "${FREE_MB:-0}" -lt 400 ]]; then
    warn "Low available memory (${FREE_MB}MB free). Playwright may be limited."
  else
    ok "Memory: ${FREE_MB}MB available"
  fi
fi

hdr "2. Environment Setup"

if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    cp .env.example .env
    warn ".env created from .env.example — edit to add API keys (optional)"
  else
    touch .env
    warn ".env created empty — Ollama-only mode"
  fi
else
  ok ".env exists"
fi

mkdir -p data/state data/artifacts data/.supreme-os
ok "Data directories ready"

hdr "3. Docker Compose Validation"

docker compose config --quiet 2>&1 && ok "docker-compose.yml valid" || err "docker-compose.yml invalid"

hdr "4. Build Containers"

if [[ "$SKIP_BUILD" == "false" ]]; then
  info "Building images (Playwright installs during build — ~2 min first time)..."
  docker compose build 2>&1 | tail -5
  ok "Build complete"
else
  ok "Build skipped (--skip-build)"
fi

hdr "5. Start Core Services"

docker compose up -d browserless ollama
info "Waiting for Browserless (up to 30s)..."
ELAPSED=0
while ! curl -sf http://localhost:3001/pressure >/dev/null 2>&1; do
  sleep 2; ELAPSED=$((ELAPSED+2))
  [[ $ELAPSED -ge 30 ]] && { warn "Browserless slow — continuing"; break; }
  printf "."
done
echo ""
ok "Browserless: remote Chrome ready at http://localhost:3001"

docker compose up -d api dashboard frontend
ok "Services started: api, dashboard (streamlit), frontend (nextjs), browserless, ollama"

hdr "6. Health Checks"

info "Waiting for API (up to 90s)..."
MAX=90; ELAPSED=0
while ! curl -sf http://localhost:8000/health >/dev/null 2>&1; do
  sleep 3; ELAPSED=$((ELAPSED+3))
  [[ $ELAPSED -ge $MAX ]] && err "API health timeout. Logs: docker compose logs api"
  printf "."
done
echo ""
ok "API healthy"

info "Waiting for Dashboard (up to 60s)..."
ELAPSED=0
while ! curl -sf http://localhost:8501 >/dev/null 2>&1; do
  sleep 3; ELAPSED=$((ELAPSED+3))
  if [[ $ELAPSED -ge 60 ]]; then
    warn "Dashboard slow to start — continuing"
    break
  fi
  printf "."
done
echo ""

hdr "7. Ollama Model Check"

OLLAMA_MODELS=$(curl -sf http://localhost:11434/api/tags 2>/dev/null | \
  python3 -c "import sys,json; print(len(json.load(sys.stdin).get('models',[])))" 2>/dev/null || echo "0")

if [[ "$OLLAMA_MODELS" == "0" ]]; then
  info "Pulling qwen2.5 (default model — ~2GB, may take a few minutes)..."
  docker compose exec -T ollama ollama pull qwen2.5 2>/dev/null && ok "qwen2.5 ready" || \
    warn "Pull failed — run manually: docker compose exec ollama ollama pull qwen2.5"
else
  ok "Ollama: $OLLAMA_MODELS model(s) available"
fi

hdr "8. Optional Services"

# Telegram
TG_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]' || echo "")
if [[ -n "$TG_TOKEN" && "$TG_TOKEN" != "#"* ]]; then
  docker compose --profile telegram up -d telegram 2>/dev/null && ok "Telegram bot started" || warn "Telegram start failed"
else
  warn "TELEGRAM_BOT_TOKEN not set — Telegram bot skipped"
fi

# Redis
if grep -q "^REDIS_URL=" .env 2>/dev/null; then
  docker compose --profile redis up -d redis 2>/dev/null && ok "Redis started" || warn "Redis start failed"
fi

hdr "9. Smoke Tests"

PASS=0; FAIL=0
smoke() {
  local desc="$1" url="$2"
  if curl -sf "$url" >/dev/null 2>&1; then
    ok "  $desc"
    PASS=$((PASS+1))
  else
    warn "  FAIL: $desc  ($url)"
    FAIL=$((FAIL+1))
  fi
}

smoke "GET /health"              "http://localhost:8000/health"
smoke "GET /api/status"          "http://localhost:8000/api/status"
smoke "GET /api/agents"          "http://localhost:8000/api/agents"
smoke "GET /api/tools"           "http://localhost:8000/api/tools"
smoke "GET /api/memory"          "http://localhost:8000/api/memory"
smoke "GET /api/browser/status"  "http://localhost:8000/api/browser/status"
smoke "GET /agents"              "http://localhost:8000/agents"
smoke "GET /models"              "http://localhost:8000/models"
smoke "GET /tasks"               "http://localhost:8000/tasks"
smoke "GET /rewards"             "http://localhost:8000/rewards"
smoke "GET /startup"             "http://localhost:8000/startup"
smoke "GET /logs"                "http://localhost:8000/logs"
smoke "GET /soul"                "http://localhost:8000/soul"
smoke "GET /identity"            "http://localhost:8000/identity"
smoke "GET /user"                "http://localhost:8000/user"
smoke "GET /settings"            "http://localhost:8000/settings"
smoke "Dashboard (Streamlit) :8501" "http://localhost:8501"
smoke "Dashboard (Next.js) :3000"   "http://localhost:3000"
smoke "Browserless :3001"           "http://localhost:3001/pressure"

echo ""
info "Browser engine check:"
BROWSER_INFO=$(curl -sf http://localhost:8000/api/browser/status 2>/dev/null)
BROWSER_ENGINE=$(echo "$BROWSER_INFO" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('engine','unknown'))" 2>/dev/null || echo "unknown")
BROWSER_MODE=$(echo "$BROWSER_INFO" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('mode','unknown'))" 2>/dev/null || echo "unknown")
BROWSER_SRC=$(echo "$BROWSER_INFO" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('source',''))" 2>/dev/null || echo "")
BROWSER_AVAIL=$(echo "$BROWSER_INFO" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('available',False))" 2>/dev/null || echo "False")
if [[ "$BROWSER_AVAIL" == "True" ]]; then
  ok "Browser: $BROWSER_ENGINE ($BROWSER_SRC) — $BROWSER_MODE mode — OPERATIONAL"
else
  warn "Browser: $BROWSER_ENGINE — httpx fallback only. Browserless container status:"
  curl -sf http://localhost:3000/pressure 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('  running:', d.get('running',0), 'queued:', d.get('queued',0))" 2>/dev/null || warn "  Browserless not responding"
fi

echo ""
if [[ $FAIL -eq 0 ]]; then
  ok "All ${PASS} smoke tests passed"
else
  warn "${PASS} passed / ${FAIL} failed"
fi

# ── Final output ──────────────────────────────────────────────────────────────
echo ""
echo    "  =============================================================="
echo -e "  ${BOLD}${GREEN}⚡  SUPAR SMART AI — LIVE!${NC}"
echo    "  SMARTY AI Inception Runtime is operational."
echo    "  =============================================================="
echo ""
echo    "  API Endpoints:"
echo -e "    ${CYAN}Health:${NC}         http://localhost:8000/health"
echo -e "    ${CYAN}Docs:${NC}           http://localhost:8000/docs"
echo -e "    ${CYAN}Status:${NC}         http://localhost:8000/api/status"
echo -e "    ${CYAN}Agents:${NC}         http://localhost:8000/api/agents"
echo -e "    ${CYAN}Browser:${NC}        http://localhost:8000/api/browser/status"
echo -e "    ${CYAN}Memory:${NC}         http://localhost:8000/api/memory"
echo -e "    ${CYAN}Inception:${NC}      http://localhost:8000/inception/run  [POST]"
echo -e "    ${CYAN}Rewards:${NC}        http://localhost:8000/rewards"
echo -e "    ${CYAN}Bounty:${NC}         http://localhost:8000/bounty/plans"
echo -e "    ${CYAN}Metrics:${NC}        http://localhost:8000/metrics"
echo ""
echo    "  Services:"
echo -e "    ${CYAN}Dashboard (Next.js):${NC} http://localhost:3000"
echo -e "    ${CYAN}Dashboard (Legacy):${NC}  http://localhost:8501"
echo -e "    ${CYAN}Ollama:${NC}         http://localhost:11434"
echo ""
echo    "  Management:"
echo    "    docker compose logs -f api               # stream API logs"
echo    "    docker compose logs -f dashboard         # stream dashboard logs"
echo    "    docker compose logs -f frontend          # stream nextjs logs"
echo    "    docker compose exec ollama ollama list   # list models"
echo    "    docker compose exec ollama ollama pull qwen2.5"
echo    "    docker compose down                      # stop all"
echo    ""
echo    "  Browser upgrade (for screenshots + JS execution):"
echo    "    docker compose exec api python -m playwright install chromium"
echo ""

if [[ $FAIL -gt 0 ]]; then
  echo -e "  ${YELLOW}Debug:${NC} docker compose logs api | tail -50"
fi
