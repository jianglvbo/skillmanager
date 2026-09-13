#!/bin/bash
# server-ops: 查服务器各站 + MySQL 状态（只读）
# 用法: scripts/status.sh [--json]
# 2026-09-03: investment-console 服务器版已下线（仅本地运行），从状态检查移除
# 2026-09-13: 数据快检改用现役表（files 表已退役）；服务列表补 redis-investment
set -e
HOST="${SERVER_HOST:-106.55.14.116}"
USER="${SERVER_USER:-jianglb}"

if [ "$1" = "--json" ]; then
  ssh -o ConnectTimeout=10 "$USER@$HOST" bash -s <<'REMOTE'
echo "{"
echo "  \"fitness\": \"$(sudo systemctl is-active fitness-console)\","
echo "  \"qa\": \"$(sudo systemctl is-active qa)\","
echo "  \"mysql\": \"$(sudo systemctl is-active mysql)\","
echo "  \"redis\": \"$(sudo systemctl is-active redis-investment)\","
echo "  \"fitness_http\": \"$(curl -s -o /dev/null -w %{http_code} http://127.0.0.1:8699/)\","
echo "  \"qa_http\": \"$(curl -s -o /dev/null -w %{http_code} http://127.0.0.1:8700/)\","
cnt=$(sudo mysql -N -e "SELECT CONCAT('bloggers=',(SELECT COUNT(*) FROM investment_kb.bloggers),' statements=',(SELECT COUNT(*) FROM investment_kb.statements),' post_history=',(SELECT COUNT(*) FROM investment_kb.post_history),' stocks=',(SELECT COUNT(*) FROM investment_kb.stocks))")
echo "  \"investment_kb_counts\": \"$cnt\""
echo "}"
REMOTE
else
  ssh -o ConnectTimeout=10 "$USER@$HOST" bash -s <<'REMOTE'
echo "== 服务状态 =="
for s in fitness-console qa mysql redis-investment; do
  printf "%-22s %s\n" "$s" "$(sudo systemctl is-active $s)"
done
echo "== HTTP =="
curl -s -o /dev/null -w "fitness(8699): %{http_code}\n" http://127.0.0.1:8699/
curl -s -o /dev/null -w "qa(8700): %{http_code}\n" http://127.0.0.1:8700/
echo "== investment_kb 行数快检 =="
sudo mysql -N -e "SELECT CONCAT('bloggers=', (SELECT COUNT(*) FROM investment_kb.bloggers), ' statements=', (SELECT COUNT(*) FROM investment_kb.statements), ' post_history=', (SELECT COUNT(*) FROM investment_kb.post_history), ' stocks=', (SELECT COUNT(*) FROM investment_kb.stocks))"
REMOTE
fi
