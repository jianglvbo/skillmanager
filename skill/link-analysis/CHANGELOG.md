# Changelog — link-analysis

## 2.1.1 (2026-06-22)

### Changed
- **Skill 解耦**：移除对 xq-registry 的显式引用，路由判断流程自行描述逻辑

## 2.1.0 (2026-06-22)

### Changed
- **目录结构更新**：仪表盘上移至 vault 根目录，投资分析框架和博主分析框架精简为核心数据目录

## 2.0.0 (2026-06-21)

### Changed
- **路由逻辑**：新增 `_route` 字段（博主分析/投资知识/both），链接转译时自动判断资源流向
- **处理指令传播**：新增 `_route`/`_profile`/`_alias`/`_xueqiu` 临时字段，通过 frontmatter 在流水线中传递
- **双框架支持**：vault 结构更新为「我的知识库」下两个子框架（投资分析框架 + 博主分析框架）
- **共享基础设施**：待处理链接、粗制品、问答看板在 vault 根目录，两个框架共用

## 1.2.0 — 2026-06-18

### Changed
- SKILL.md：IM 渠道链接收集统一存入 `~/.qoderworkcn/daily-links/YYYY-MM-DD.json`，不再直接写 Obsidian 粗制品目录
- SKILL.md：移除 WorkBuddy 专属章节，合并为通用 IM 收集流程
- SKILL.md：新增"定时分析"章节，引用 protocol.md 作为批量分析协议
- SKILL.md：内容抓取策略拆分为"实时场景"和"定时任务场景"两张表，消除抖音策略不一致
- SKILL.md：新增截图/图片收集流程和 JSON 格式说明
- scripts/add_link.py：数据目录从 `~/Ai/skill/link-analysis/data` 改为 `~/.qoderworkcn/daily-links/`
- README.md：安装路径从 `~/.agent/skills/` 改为 `~/.qoderworkcn/skills/`，移除手动创建数据目录步骤
- README.md：定时执行章节引用 protocol.md

### Added
- 抖音 Web API 端点文档记录（`/aweme/v1/web/aweme/detail/`）

## 1.1.0 — 2026-06-08

### Changed
- 去除 SKILL.md 中所有 `#WorkBuddy`、`#qoder` 标签，改为通用 `#每日分析`
- 将 WorkBuddy automation 引用改为通用表述
- scripts/add_link.py：数据目录从 `~/.workbuddy/daily-links` 改为 `~/Ai/skill/link-analysis/data`

### Added
- 新增 README.md
- 新增 CHANGELOG.md（本文件）
