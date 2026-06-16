#!/usr/bin/env bash
# Full platform smoke test. Run from repo root with the backend running.
set -e

API="${SUPREME_API_URL:-http://localhost:8000}"
FRONTEND="${FRONTEND_URL:-http://localhost:3000}"
PASS=0; FAIL=0

ok()  { echo "✅ $1"; ((PASS++)); }
err() { echo "❌ $1"; ((FAIL++)); }

check_http() {
  local label="$1" url="$2" expected="${3:-200}"
  code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
  [ "$code" = "$expected" ] && ok "$label (HTTP $code)" || err "$label (got $code, expected $expected)"
}

check_json() {
  local label="$1" url="$2" key="$3" want="$4"
  val=$(curl -s "$url" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d$key)" 2>/dev/null)
  [ "$val" = "$want" ] && ok "$label ($val)" || err "$label (got '$val', want '$want')"
}

echo ""
echo "Supreme AI Agent OS — Platform Test"
echo "Backend: $API"
echo "Frontend: $FRONTEND"
echo "---"

# Backend
check_json  "Health status"          "$API/health"          "['status']"  "ok"
check_http  "Ready endpoint"         "$API/ready"
check_http  "Live endpoint"          "$API/live"
check_http  "Agents list"            "$API/agents"
check_http  "Skills list"            "$API/skills"
check_http  "Rewards/opportunities"  "$API/rewards"
check_http  "Bounty platforms"       "$API/bounty-platforms"
check_http  "Connectors"             "$API/connectors"
check_http  "All connectors"         "$API/api/connectors/all"
check_http  "Startup diagnostics"    "$API/startup"
check_http  "Logs"                   "$API/logs"
check_http  "Browser status"         "$API/browser/status"

# Task creation
TASK=$(curl -s -X POST "$API/tasks" -H 'Content-Type: application/json' \
  -d '{"prompt":"smoke test task","agent_id":"executive"}' 2>/dev/null)
TID=$(echo "$TASK" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id','?'))" 2>/dev/null)
[ "$TID" != "?" ] && ok "Task creation (id=$TID)" || err "Task creation failed"

# Bounty plan
PLAN=$(curl -s -X POST "$API/bounty/plan" -H 'Content-Type: application/json' \
  -d '{"program":"SmokeTest","scope":"*.smoke.test"}' 2>/dev/null)
CHECKS=$(echo "$PLAN" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('checks',[])))" 2>/dev/null)
[ "$CHECKS" -gt 0 ] && ok "Bounty plan ($CHECKS OWASP checks)" || err "Bounty plan creation failed"

# Connector modules
MODS=$(python3 -c "
import sys; sys.path.insert(0, '.')
from backend.app.connectors.registry import all_connectors
c = all_connectors()
print(sum(1 for x in c if x['module_present']))
" 2>/dev/null || echo "0")
[ "$MODS" = "6" ] && ok "All 6 connector modules present" || err "Connector modules: $MODS/6"

# Frontend
if [ -n "$FRONTEND" ]; then
  for page in "" agents tasks bounties browser terminal connectors logs revenue payments settings approvals; do
    check_http "Frontend /$page" "$FRONTEND/$page"
  done
fi

echo ""
echo "---"
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && echo "🎉 All tests passed!" && exit 0 || echo "⚠ Some tests failed." && exit 1
