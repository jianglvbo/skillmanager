#!/bin/bash
# server-ops: 本机 vault → 服务器同步（md 内容，排除附件/插件数据）
# 用法: 本机执行 scripts/vault_sync.sh [--dry-run]
set -e

VAULT="/Users/jianglb/Library/Mobile Documents/iCloud~md~obsidian/Documents/投资知识库"
HOST="${SERVER_HOST:-106.55.14.116}"
USER="${SERVER_USER:-jianglb}"
DEST="/home/jianglb/vault"

EXCLUDES=(
  --exclude ".obsidian"
  --exclude ".trash"
  --exclude ".plugin_data"
  --exclude ".space"
  --exclude ".DS_Store"
  --exclude "附件"
  --exclude "__visit_history"
)

EXTRA=()
[ "$1" = "--dry-run" ] && EXTRA=(--dry-run)

echo "▶ 同步 vault → ${USER}@${HOST}:${DEST}"
rsync -az "${EXTRA[@]}" "${EXCLUDES[@]}" \
  -e "ssh -o ConnectTimeout=10 -p 22" \
  "$VAULT/" "${USER}@${HOST}:${DEST}/"

if [ "$1" != "--dry-run" ]; then
  echo "▶ 刷新看板索引（重启 investment-console 强制重建）"
  ssh -o ConnectTimeout=10 "$USER@$HOST" "sudo systemctl restart investment-console && sleep 3 && curl -s -o /dev/null -w 'investment(8698): %{http_code}\n' http://127.0.0.1:8698/"
  echo "✅ 同步完成"
fi
