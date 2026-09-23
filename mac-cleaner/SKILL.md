---
name: mac-cleaner
description: >
  macOS 磁盘空间分析与垃圾清理。分析 Mac 存储空间占用，找出系统数据垃圾、应用残留、缓存等无用文件，安全清理释放空间。
  触发词：「清理Mac」「Mac空间不足」「磁盘清理」「系统数据太大」「macOS清理」「释放磁盘空间」「clean mac storage」。
  排除条件：涉及用户个人文档整理/删除（Desktop/Documents/Downloads）走个人文件安全流程，先扫描报告、确认后再动。
agent_created: true
---

# macOS 磁盘清理 Skill

分析并安全清理 macOS 系统中的垃圾文件和残留数据。

## Default Stance

### 核心原则

- **先扫描后建议**：任何清理前先跑 `scripts/analyze_mac_storage.sh` 收集数据，不凭猜测
- **表格呈现**：扫描结果按路径/大小/类型/安全等级结构化展示，用户一目了然
- **确认后执行**：列出建议清理项，用户确认后才动手
- **废纸篓优先**：用 `osascript` 移至废纸篓（可恢复），绝不用 `rm -rf`

### 禁止行为（安全红线）

- **绝不清理** `~/Library/Keychains/`、`~/Library/Accounts/`
- **绝不清理** `/System/`、`/usr/` 系统目录
- **绝不使用** `rm -rf` 直接删除（一律废纸篓）
- **绝不清理** 用户明确表示需要保留的应用数据
- 清理 `Application Support` 时，必须确认对应应用已从 `/Applications/` 卸载
- 用户没提到的内容不主动询问是否删除

---

## Workflow

### 第一步：扫描分析

运行 `scripts/analyze_mac_storage.sh` 收集磁盘数据。脚本输出带标记段的结构化数据：

- `=== APFS_CONTAINER ===` — 磁盘总容量和使用率
- `=== TIMEMACHINE_SNAPSHOTS ===` — 本地 Time Machine 快照
- `=== TOP_DIRS ===` — 用户目录下最大的文件夹
- `=== APP_SUPPORT_TOP ===` — Application Support 中最大的应用数据
- `=== CACHES_TOP ===` — 最大的缓存目录
- `=== CONTAINERS_TOP ===` — 最大的容器数据
- `=== ORPHAN_CHECK ===` — 已卸载应用的残留数据（ORPHANED/ACTIVE）
- `=== SPECIAL_CHECKS ===` — Xcode、Homebrew、.nvm 等特殊位置

同时加载 `references/common-junk-locations.md` 获取已知垃圾位置清单。

### 第二步：生成清理建议

将扫描结果整理为结构化表格，按优先级排列：

1. **可安全清理的缓存**（Caches 目录，不影响应用功能）
2. **已卸载应用的残留数据**（ORPHANED 标记，可直接清理）
3. **Time Machine 本地快照**（macOS 自动管理）
4. **大型应用数据**（ACTIVE 标记，需确认后谨慎清理）

标注安全等级：🟢 安全（缓存类）/ 🟡 确认（需用户确认）/ 🔴 谨慎（在用应用数据）。

### 第三步：执行清理（分批）

1. **每次最多清理 10 个目录**
2. **用 `osascript` 移至废纸篓**：
   ```bash
   osascript -e 'tell app "Finder" to delete POSIX file "<absolute-path>"'
   ```
3. 清理前再次列出即将操作的路径和大小，获得用户确认
4. **分批执行**，每批完成后报告状态
5. 清理完毕提醒用户**手动清空废纸篓**才能真正释放空间

---

## Output Format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| scan_result | table | 扫描结果（路径/大小/类型/安全等级） |
| suggested_cleanups | list[string] | 建议清理项（含优先级） |
| executed | list[string] | 已执行清理的路径 |
| freed_space | string | 释放的空间 |
| remaining_space | string | 当前剩余可用空间 |

---

## Relative Files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| 扫描 | scripts/analyze_mac_storage.sh | 磁盘数据采集脚本 | **执行** |
| 已知垃圾位置 | references/common-junk-locations.md | 常见垃圾目录清单 | 读取 |
| 移废纸篓 | osascript（系统） | Finder 删除至废纸篓 | **执行** |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 脚本扫描输出（实际磁盘数据） |
| 2 | 用户确认（清理范围、保留项） |
| 3 | references/common-junk-locations.md（已知垃圾位置） |

---

## 自检

- [ ] 是否先扫描后建议（未跳过分析直接清理）？
- [ ] 建议项是否用表格呈现（路径/大小/类型/等级）？
- [ ] 是否获得用户确认后才执行？
- [ ] 是否用废纸篓而非 `rm -rf`？
- [ ] 单批是否 ≤10 个目录？
- [ ] 是否未触碰系统目录/钥匙串/账户数据？
