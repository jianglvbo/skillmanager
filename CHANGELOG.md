# Changelog

本文件记录 `~/Ai/` 仓库的整体版本变更历史。

## 1.3.0 — 2026-06-12

### Added
- **mac-cleaner skill**：macOS 磁盘分析与垃圾清理（`skill/mac-cleaner/`）
  - 三段式工作流：扫描分析 → 生成建议 → 安全清理
  - 包含分析脚本 `scripts/analyze_mac_storage.sh` 和参考文档 `references/common-junk-locations.md`
  - 使用 osascript 废纸篓方式，安全可恢复

### Changed
- **纳入 GitHub 版本管理**：仓库已推送到 [github.com/jianglvbo/Ai](https://github.com/jianglvbo/Ai)（main 分支）
- **README.md**：
  - 新增 GitHub 仓库链接和版本管理章节（含首次推送和日常同步命令）
  - 安装方式从 symlink 改为 `cp -r`（匹配实际规范，保持仓库与运行实例隔离）
  - 更新目录结构和 Skill 列表（加入 mac-cleaner）
  - 更新日期 2026-06-12

## 1.2.1 — 2026-06-10

### Changed
- **link-analysis/SKILL.md**：「六、保存到熊掌记」重写为决策树——纯文本 → Bear MCP，含图片 → bearcli（因 MCP 无 `add_attachment` 能力）
- **xueqiu-to-bear/SKILL.md**：「5. 存入熊掌记」同上重写，不再将 MCP 标为「推荐」而是按场景区分

## 1.2.0 — 2026-06-10

### Removed
- **xiongzhangji**：移除熊掌记 Skill（SKILL.md、create_note.py、bear.applescript 等）
  - 原因：Bear 2.x 内置 `bearcli mcp-server`，已通过 MCP 直连熊掌记，旧 Skill 不再需要
  - QoderWork 中的 xiongzhangji skill 配置已同步移除
  - 目录已移至废纸篓，如需恢复可在废纸篓中找到

### Changed
- **link-analysis/SKILL.md**：熊掌记写入方式从 `xiongzhangji/scripts/create_note.py` 改为 Bear MCP `create_note`
- **xueqiu-to-bear/SKILL.md**：前置依赖和熊掌记写入方式从 xiongzhangji 技能改为 Bear MCP Server
- **xueqiu-following-search/SKILL.md**：前置条件和熊掌记写入方式从 xiongzhangji skill 改为 Bear MCP Server
- **README.md**：移除 xiongzhangji 的目录结构和 Skill 说明

## 1.1.0 — 2026-06-09

### Added
- 新增 CONTRIBUTING.md：仓库协作规则，面向所有接入 Agent
- README.md 新增指向 CONTRIBUTING.md 的链接

## 1.0.0 — 2026-06-08

### Added
- 新增根目录 CHANGELOG.md（本文件）
- 新增根目录 .gitignore
- 为 link-analysis、xiongzhangji skill 新增 README.md 和 CHANGELOG.md
- 为 xueqiu/ 组新增 README.md 和 CHANGELOG.md

### Changed
- **重构根目录 README.md**：改为 Agent 无关的 skill 仓库手册，去除所有 WorkBuddy/QoderWork 专属引用
- 明确仓库定位：本地 skill 仓库，Agent 无关，版本管理，仅按需更新

### Fixed
- **link-analysis/SKILL.md**：去除 `#WorkBuddy` 标签和 WorkBuddy automation 引用
- **link-analysis/scripts/add_link.py**：去除硬编码 `~/.workbuddy/` 路径
- **xiongzhangji/SKILL.md**：去除硬编码 `~/.workbuddy/skills/` 路径
- **xueqiu-to-bear/SKILL.md**：去除 `#WorkBuddy` 标签
- **xueqiu-to-bear/scripts/fetch_xueqiu.py**：去除 `#QoderWork` 标签
- **xq-registry/SKILL.md**：去除 QoderWork 引用
