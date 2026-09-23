#!/bin/bash
# macOS Storage Analyzer — scans disk usage, caches, orphaned app data, and common junk locations
# Output: plain text with labeled sections for AI parsing

set -uo pipefail
# 2026-09-12：**去掉 -e**。原 `set -euo pipefail` 下，展示用管道（`du ... | sort | head -N`）
# 因 head 提前退出触发 SIGPIPE → 整脚本在第 2 段后直接终止（实测只输出 34 行就退出，
# ORPHAN_CHECK / SPECIAL_CHECKS 永远跑不到）。关键命令改为显式判错，展示管道加 `|| true`。


HOME_DIR="$HOME"
LIB="$HOME_DIR/Library"
APP_SUPPORT="$LIB/Application Support"
CACHES="$LIB/Caches"
CONTAINERS="$LIB/Containers"
GROUP_CONTAINERS="$LIB/Group Containers"

echo "=== APFS_CONTAINER ==="
diskutil apfs list 2>/dev/null | grep -E "Size|Capacity|Free|Volume disk|Name:" | head -30 || true

echo ""
echo "=== TIMEMACHINE_SNAPSHOTS ==="
tmutil listlocalsnapshots / 2>/dev/null || echo "No local snapshots"

echo ""
echo "=== TOP_DIRS ==="
# Top-level home subdirectories (depth 1, skip hidden)
for d in "$HOME_DIR"/*/; do
    if [ -d "$d" ]; then
        du -sh "$d" 2>/dev/null
    fi
done | sort -rh | head -15 || true

echo ""
echo "=== APP_SUPPORT_TOP ==="
# Largest Application Support directories
if [ -d "$APP_SUPPORT" ]; then
    du -d 1 -h "$APP_SUPPORT" 2>/dev/null | sort -rh | head -20 || true
fi

echo ""
echo "=== CACHES_TOP ==="
# Largest cache directories
if [ -d "$CACHES" ]; then
    du -d 1 -h "$CACHES" 2>/dev/null | sort -rh | head -20 || true
fi

echo ""
echo "=== CONTAINERS_TOP ==="
if [ -d "$CONTAINERS" ]; then
    du -d 1 -h "$CONTAINERS" 2>/dev/null | sort -rh | head -15 || true
fi

echo ""
echo "=== ORPHAN_CHECK ==="
# Check for data of uninstalled apps
# 2026-09-12：原来用 `declare -A KNOWN_ORPHANS=([bundle.id]=名称)` 关联数组——**macOS 自带 bash 3.2
# 不支持关联数组**（`declare -A` 静默退化），实测报 `com.netease.mumu: syntax error: invalid arithmetic
# operator`，整段 ORPHAN 检查形同废纸。改为「bundle|名称」纯文本列表 + while 读取，零依赖。
KNOWN_ORPHANS='com.netease.mumu|网易 MuMu 模拟器
com.docker.docker|Docker Desktop
com.valvesoftware.steam|Steam
com.tencent.qqmusic|QQ音乐
com.tencent.qq|QQ
com.tencent.xinWeChat|微信
com.google.Chrome|Google Chrome
com.microsoft.edgemac|Microsoft Edge
com.apple.dt.Xcode|Xcode
com.riotgames.leagueoflegends|英雄联盟
com.blizzard.battle.net|Battle.net
com.epicgames.launcher|Epic Games'

# ── 应用是否已安装：按 bundle id 精确判定（2026-09-12 修复）────────────────────
# 旧实现用 `find /Applications -iname "*${bundle_id##*.}*"`，取的是 bundle id 最后一段
# （com.tencent.xinWeChat → "xinWeChat"），而真实 app 叫 WeChat.app —— 必然匹配不到，
# 于是把**已安装**的微信/Edge/英雄联盟全判成 ORPHANED，而 SKILL.md 写着「ORPHANED 可直接清理」，
# 有误删真实数据（含聊天记录）的风险。现改为：① mdfind 精确查 ② 常见目录按「显示名.app」查
# ③ 都查不到 → UNKNOWN（需人工确认），绝不直接判 ORPHANED。
is_app_installed() {  # $1=bundle id, $2=显示名
    local bid="$1" name="$2" hit=""
    if command -v mdfind >/dev/null 2>&1; then
        hit=$(mdfind "kMDItemCFBundleIdentifier == '$bid'" 2>/dev/null | head -1)
        [ -n "$hit" ] && return 0
    fi
    if [ -n "$name" ]; then
        for p in "/Applications/$name.app" "/Applications/$name" "$HOME/Applications/$name.app" "/Applications/Utilities/$name.app"; do
            [ -d "$p" ] && return 0
        done
    fi
    return 1
}

printf '%s\n' "$KNOWN_ORPHANS" | while IFS='|' read -r bundle_prefix app_name; do
    [ -n "$bundle_prefix" ] || continue

    # Check for leftover data
    data_size=""
    for base in "$APP_SUPPORT" "$CACHES" "$CONTAINERS" "$GROUP_CONTAINERS"; do
        for d in "$base"/"$bundle_prefix"*; do
            if [ -d "$d" ]; then
                sz=$(du -sh "$d" 2>/dev/null | cut -f1)
                data_size="$data_size $d($sz)"
            fi
        done
    done

    if [ -n "$data_size" ]; then
        if is_app_installed "$bundle_prefix" "$app_name"; then
            echo "ACTIVE|${app_name}|${data_size}"
        else
            echo "UNKNOWN|${app_name}|${data_size}|未在标准位置找到该应用，需人工确认是否已卸载"
        fi
    fi
done

echo ""
echo "=== SPECIAL_CHECKS ==="
# iOS Simulators
if [ -d "$LIB/Developer/CoreSimulator" ]; then
    du -sh "$LIB/Developer/CoreSimulator" 2>/dev/null && echo "iOS_SIMULATOR_FOUND"
fi

# Xcode DerivedData
if [ -d "$LIB/Developer/Xcode/DerivedData" ]; then
    du -sh "$LIB/Developer/Xcode/DerivedData" 2>/dev/null && echo "XCODE_DERIVEDDATA_FOUND"
fi

# Homebrew
if [ -d /opt/homebrew ]; then
    du -sh /opt/homebrew 2>/dev/null && echo "HOMEBREW_FOUND"
fi

# .nvm
if [ -d "$HOME_DIR/.nvm" ]; then
    du -sh "$HOME_DIR/.nvm" 2>/dev/null && echo "NVM_FOUND"
fi

# Mail Downloads
if [ -d "$LIB/Mail Downloads" ]; then
    du -sh "$LIB/Mail Downloads" 2>/dev/null && echo "MAIL_DOWNLOADS_FOUND"
fi

# Trash
if [ -d "$HOME_DIR/.Trash" ]; then
    du -sh "$HOME_DIR/.Trash" 2>/dev/null && echo "TRASH_FOUND"
fi

echo ""
echo "=== DONE ==="
