#!/bin/bash
# macOS Storage Analyzer — scans disk usage, caches, orphaned app data, and common junk locations
# Output: plain text with labeled sections for AI parsing

set -euo pipefail

HOME_DIR="$HOME"
LIB="$HOME_DIR/Library"
APP_SUPPORT="$LIB/Application Support"
CACHES="$LIB/Caches"
CONTAINERS="$LIB/Containers"
GROUP_CONTAINERS="$LIB/Group Containers"

echo "=== APFS_CONTAINER ==="
diskutil apfs list 2>/dev/null | grep -E "Size|Capacity|Free|Volume disk|Name:" | head -30

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
done | sort -rh | head -15

echo ""
echo "=== APP_SUPPORT_TOP ==="
# Largest Application Support directories
if [ -d "$APP_SUPPORT" ]; then
    du -d 1 -h "$APP_SUPPORT" 2>/dev/null | sort -rh | head -20
fi

echo ""
echo "=== CACHES_TOP ==="
# Largest cache directories
if [ -d "$CACHES" ]; then
    du -d 1 -h "$CACHES" 2>/dev/null | sort -rh | head -20
fi

echo ""
echo "=== CONTAINERS_TOP ==="
if [ -d "$CONTAINERS" ]; then
    du -d 1 -h "$CONTAINERS" 2>/dev/null | sort -rh | head -15
fi

echo ""
echo "=== ORPHAN_CHECK ==="
# Check for data of uninstalled apps
declare -A KNOWN_ORPHANS=(
    ["com.netease.mumu"]="网易 MuMu 模拟器"
    ["com.docker.docker"]="Docker Desktop"
    ["com.valvesoftware.steam"]="Steam"
    ["com.tencent.qqmusic"]="QQ音乐"
    ["com.tencent.qq"]="QQ"
    ["com.tencent.xinWeChat"]="微信"
    ["com.google.Chrome"]="Google Chrome"
    ["com.microsoft.edgemac"]="Microsoft Edge"
    ["com.apple.dt.Xcode"]="Xcode"
    ["com.riotgames.leagueoflegends"]="英雄联盟"
    ["com.blizzard.battle.net"]="Battle.net"
    ["com.epicgames.launcher"]="Epic Games"
)

for bundle_prefix in "${!KNOWN_ORPHANS[@]}"; do
    app_name="${KNOWN_ORPHANS[$bundle_prefix]}"
    # Check if app exists in /Applications
    app_found=$(find /Applications -maxdepth 2 -iname "*${bundle_prefix##*.}*" -type d 2>/dev/null | head -1 || true)
    
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
        if [ -z "$app_found" ]; then
            echo "ORPHANED|${app_name}|${data_size}"
        else
            echo "ACTIVE|${app_name}|${data_size}"
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
