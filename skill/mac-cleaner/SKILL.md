---
name: mac-cleaner
description: macOS 磁盘空间分析与垃圾清理。分析 Mac 存储空间占用，找出系统数据垃圾、应用残留、缓存等无用文件，安全清理释放空间。触发词：「清理Mac」「Mac空间不足」「磁盘清理」「系统数据太大」「macOS清理」「释放磁盘空间」「clean mac storage」。
agent_created: true
---

# macOS 磁盘清理 Skill

分析并安全清理 macOS 系统中的垃圾文件和残留数据。

## 触发条件

当用户提出以下需求时使用本 Skill：
- 询问 Mac 磁盘空间不足原因
- 想要清理系统垃圾
- 需要释放磁盘空间
- 提到「系统数据」占比过大

## 工作流程

### 阶段 1：扫描分析

运行 `scripts/analyze_mac_storage.sh` 收集磁盘数据。该脚本输出带有标记段的结构化数据：

- `=== APFS_CONTAINER ===` — 磁盘总容量和使用率
- `=== TIMEMACHINE_SNAPSHOTS ===` — 本地 Time Machine 快照
- `=== TOP_DIRS ===` — 用户目录下最大的文件夹
- `=== APP_SUPPORT_TOP ===` — Application Support 中最大的应用数据
- `=== CACHES_TOP ===` — 最大的缓存目录
- `=== CONTAINERS_TOP ===` — 最大的容器数据
- `=== ORPHAN_CHECK ===` — 已卸载应用的残留数据（标记为 ORPHANED/ACTIVE）
- `=== SPECIAL_CHECKS ===` — Xcode、Homebrew、.nvm 等特殊位置

同时加载 `references/common-junk-locations.md` 获取已知垃圾位置清单。

### 阶段 2：生成清理建议

将扫描结果整理为结构化表格，按以下优先级排列：

1. **可安全清理的缓存**（Caches 目录，不影响应用功能）
2. **已卸载应用的残留数据**（ORPHANED 标记，可直接清理）
3. **Time Machine 本地快照**（占用空间但 macOS 会自动管理）
4. **大型应用数据**（ACTIVE 标记，需确认后谨慎清理）

用表格展示每个项目的路径和大小，标注安全等级：
- 🟢 安全 — 缓存类，清空无影响
- 🟡 确认 — 需用户确认是否仍需
- 🔴 谨慎 — 正在使用的应用数据

### 阶段 3：执行清理

清理必须严格遵守以下规则：

1. **每次最多清理 10 个目录**
2. **使用 `osascript` 移至废纸篓**，不用 `rm -rf`：
   ```bash
   osascript -e 'tell app "Finder" to delete POSIX file "<absolute-path>"'
   ```
3. **清理前再次列出即将操作的路径和大小**，获得用户确认
4. **分批执行**，每批完成后报告状态
5. 清理完毕后提醒用户**手动清空废纸篓**才能真正释放空间

### 安全红线

- **绝不清理** `~/Library/Keychains/`、`~/Library/Accounts/`
- **绝不清理** `/System/`、`/usr/` 系统目录
- **绝不使用** `rm -rf` 直接删除
- **绝不清理** 用户明确表示需要保留的应用数据
- 清理 `Application Support` 时，必须确认对应应用已从 `/Applications/` 卸载

## 交互规范

- 扫描完成后用表格呈现结果，包含路径、大小、类型（缓存/残留/在用）、安全等级
- 列出建议清理项目，等待用户确认后再执行
- 清理完成后报告释放的空间和当前剩余可用空间
- 如用户同时提到多个清理目标，在一次确认后批量执行
- 用户没提到的不要主动询问是否删除
