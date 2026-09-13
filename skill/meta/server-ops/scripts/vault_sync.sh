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
  # 2026-09-12：服务器版投资看板已删（投资看板现仅本机运行：launchd com.investment-console + 127.0.0.1:8698）。
  # 原此处 `systemctl restart investment-console` 会去重启一个**已不存在的服务**——已移除；
  # 服务器上只剩 fitness-console(8699) / 「问」(8700) / MySQL，需要刷新它们时用各自的部署命令。
  echo "✅ vault 已同步到 ${USER}@${HOST}:${DEST}（服务器已无投资看板服务，无需重启）"
fi
