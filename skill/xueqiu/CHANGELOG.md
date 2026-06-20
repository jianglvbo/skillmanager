# Changelog — xueqiu

## 1.4.0 — 2026-06-20

### Removed
- 删除 `data/` 目录（含 feed_scrape、metadata、posts 等历史数据），不再本地持久化分析数据
- .gitignore 规则从 `skill/xueqiu/data/*.json` 改为 `skill/xueqiu/data/` 整目录忽略
- xq-registry/SKILL.md：移除粉丝数刷新和股票提及重算中的 metadata 文件更新步骤
- 目录树结构移除 data/ 子树，明确所有原始数据用完即弃

## 1.3.0 — 2026-06-09

### Changed
- **目录名标准化**：40 个 xq-{数字ID} 目录重命名为 xq-{拼音昵称}，与 SKILL.md 的 name 字段统一
- registry.json：skill_name 从 xq-{数字ID} 格式改为 xq-{拼音昵称} 格式
- xq-registry/SKILL.md：更新所有路径引用，`xq-{数字ID}` → `xq-{拼音昵称}`
- 修复所有断链的 symlink（~/.workbuddy/skills/xq-*）
- 40 个 xq-* SKILL.md 触发词：`「xq-{数字ID}」` → `「xq-{拼音}」`
- xq-registry/SKILL.md JSON 示例 `skill_name` 字段同步更新

## 1.2.1 — 2026-06-08

### Changed
- xq-metalslime/SKILL.md：重写轮胎行业专题，从纯框架推导转为基于实际帖子分析
  - 发现并引用 2026-04-09 轮胎专帖（ID:383133930）
  - 发现并引用 2026-04-27 赛轮一季报评论
  - 修正结论：metalslime 对轮胎是「谨慎乐观」而非「碳基一键否决」
  - 新增 3 条轮胎相关语录

## 1.2.0 — 2026-06-08

### Added
- xq-registry/SKILL.md：新增 🚨 路由层（最高优先级），作为 40 个 xq-* Skill 的统一路由入口
  - 三层路由流程：请求识别 → 博主匹配 → 加载对应 Skill
  - 负样本表：明确 6 种不触发场景（随口提到、平台讨论、纯数据查询、技能操作等）
  - 路由指令：Agent 必须先过 xq-registry 匹配博主，再加载具体 Skill
  - 路由效果自检清单
- 更新 frontmatter 描述：增加路由触发词和路由入口说明

## 1.1.0 — 2026-06-08

### Changed
- xueqiu-to-bear/SKILL.md：标签从 `#WorkBuddy` 改为 `#雪球分析`
- xueqiu-to-bear/scripts/fetch_xueqiu.py：标签从 `#QoderWork` 改为 `#雪球分析`
- xq-registry/SKILL.md：去除 QoderWork 引用

### Added
- 新增 xueqiu/ 组 README.md
- 新增 xueqiu/ 组 CHANGELOG.md（本文件）
