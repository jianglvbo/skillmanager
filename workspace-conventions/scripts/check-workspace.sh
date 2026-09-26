#!/usr/bin/env bash
# 工作区协作规范自检：纯只读，不改任何文件。有 FAIL 则退出码 1。
# 用法：check-workspace.sh [工作区根目录]     （缺省＝当前目录）
# 名单可用环境变量覆盖：WORKSPACE_AGENT_DIRS="qoder-cn zcode claude"
set -u

ROOT="${1:-$(pwd)}"
cd "$ROOT" 2>/dev/null || { echo "FAIL root_not_found $ROOT"; exit 1; }

AGENT_DIRS="${WORKSPACE_AGENT_DIRS:-qoder-cn zcode qwenworkcn claude}"
fails=0
warns=0

pass() { echo "PASS $1"; }
fail() { echo "FAIL $1"; fails=$((fails + 1)); }
warn() { echo "WARN $1"; warns=$((warns + 1)); }

# --- 1. 三份文档分工 ---
[ -f AGENTS.md ] && pass agents_md_present || fail agents_md_missing
[ -f README.md ] && pass readme_present || warn readme_missing_agent_facing_docs

if [ -f AGENTS.md ]; then
  grep -q "开工与收工" AGENTS.md && pass sec_handoff || fail sec_handoff_missing
  grep -q "一处一义" AGENTS.md && pass sec_ownership || fail sec_ownership_missing
  grep -q "产物落点" AGENTS.md && pass sec_artifacts || fail sec_artifacts_missing
fi

# --- 2. .gitignore：产物与 skill 镜像层不进 git ---
if [ -f .gitignore ]; then
  grep -qE '^/?out/?$' .gitignore && pass gitignore_out || fail gitignore_out_missing
  grep -qE '^\.agents/?$' .gitignore && pass gitignore_agents || fail gitignore_agents_missing
else
  fail gitignore_missing
fi

# --- 3. 账实相符：被忽略的东西不能同时在 git 索引里 ---
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  tracked=$(git ls-files -- out .agents 2>/dev/null | head -5)
  if [ -z "$tracked" ]; then
    pass not_tracked
  else
    echo "$tracked" | while IFS= read -r f; do echo "FAIL tracked_in_git $f"; done
    fail tracked_in_git_see_lines_above
  fi
else
  warn git_repo_absent_skipped_tracked_check
fi

# --- 4. out/ 分格命名 ---
if [ -d out ]; then
  found=0
  for d in out/*/; do
    [ -d "$d" ] || continue
    found=1
    name=$(basename "$d")
    ok=0
    for a in $AGENT_DIRS; do
      [ "$name" = "$a" ] && ok=1
    done
    [ "$ok" = 1 ] && pass "out_cell_known $name" || fail "out_cell_unlisted $name"
  done
  [ "$found" = 0 ] && warn out_dir_empty
else
  warn out_dir_absent_create_on_first_artifact
fi

# --- 5. 悬空软链：静默失效，必须显式测 ---
check_links() {
  layer="$1"
  [ -d "$layer" ] || return 0
  dead=$(find "$layer" -maxdepth 1 -type l ! -exec test -e {} \; -print 2>/dev/null)
  if [ -z "$dead" ]; then
    pass "links_ok $layer"
  else
    echo "$dead" | while IFS= read -r l; do echo "WARN dangling_link $l"; done
    warns=$((warns + 1))
  fi
}
check_links ".agents/skills"
check_links "$HOME/.agents/skills"

echo "SUMMARY fails=$fails warns=$warns"
[ "$fails" -eq 0 ] || exit 1
exit 0
