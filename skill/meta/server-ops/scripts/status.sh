#!/bin/bash
# server-ops: 查两站 + MySQL 状态（只读）
# 用法: scripts/status.sh [--json]
set -e
HOST="${SERVER_HOST:-106.55.14.116}"
USER="${SERVER_USER:-jianglb}"

if [ "$1" = "--json" ]; then
  ssh -o ConnectTimeout=10 "$USER@$HOST" bash -s <<'REMOTE'
echo "{"
echo "  \"investment\": \"$(sudo systemctl is-active investment-console)\","
echo "  \"fitness\": \"$(sudo systemctl is-active fitness-console)\","
echo "  \"mysql\": \"$(sudo systemctl is-active mysql)\","
echo "  \"investment_http\": \"$(curl -s -o /dev/null -w %{http_code} http://127.0.0.1:8698/)\","
echo "  \"fitness_http\": \"$(curl -s -o /dev/null -w %{http_code} http://127.0.0.1:8699/)\""
echo "}"
REMOTE
else
  ssh -o ConnectTimeout=10 "$USER@$HOST" bash -s <<'REMOTE'
echo "== 服务状态 =="
for s in investment-console fitness-console mysql; do
  printf "%-22s %s\n" "$s" "$(sudo systemctl is-active $s)"
done
echo "== HTTP =="
curl -s -o /dev/null -w "investment(8698): %{http_code}\n" http://127.0.0.1:8698/
curl -s -o /dev/null -w "fitness(8699): %{http_code}\n" http://127.0.0.1:8699/
echo "== 看板数据 =="
curl -s http://127.0.0.1:8698/api/dashboard/overview | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print('wikiTotal:', d['wikiTotal'], '| bloggerCount:', d['bloggerCount'], '| starCount:', d['starCount'])"
REMOTE
fi
