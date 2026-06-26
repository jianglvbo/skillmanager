---
name: knowledge-pipeline
description: >
  知识框架全局编排者。定义七模块清单、调用链、路径表、模板表、全局规则、所有输出模板。
  加工 skill 不包含任何路径和模板——全部由此传入。路径变更只改这里。
  触发词：「框架」「全貌」「pipeline」「全局」「怎么用」「流程」。
  区别于 link-ingest（只抓取链接）、coarse-processor（只做粗加工）：pipeline 是路径和模板的唯一持有者，负责串联全部加工模块。
license: MIT
agent_created: true
metadata:
  version: "6.0.0"
  short-description: 知识框架全局编排者
compatibility: 通用
---

# 知识框架 · 全局编排者

唯一持有路径、模板、调用链的地方。加工 skill 全部无默认值，缺参数就报错。

---

## Default Stance

### 核心原则
- **单点配置**：所有路径、模板、规则、阈值只在此定义。加工 skill 零硬编码——它们是纯执行引擎，通过 rules_path 读取规则文件。
- **参数必填**：加工 skill 所有参数由 pipeline 传入，缺参即报错。不给默认值。
- **编排不执行**：pipeline 只决定调用链，不亲自读写文件。
- **先读队列再扫目录**：粗加工/提炼前必读 PENDING_QUEUE，用 Dataview 查询确定待处理文件，不逐目录扫描。

### 禁止行为
- 绝不修改 Obsidian vault 外的文件
- 绝不在加工 skill 中硬编码路径或模板路径
- 绝不跳过读取 PENDING_QUEUE 直接扫目录
- 绝不擅自修改路径表中的常量值

---

## Workflow

### 路由表

pipeline 被加载后，Agent 根据用户意图选择调用链：

| 用户意图 | 触发词 | 调用链 |
|:---|:---|:---|
| 链接收集（飞书/IM 渠道） | 无（自动触发） | 链接收集 → 存入粗制品 |
| 链接收集（WorkBuddy 渠道） | 无（自动触发） | 链接收集 → 存入 daily-links |
| 投资知识全流程 | 粗加工、提炼、归档 | 链接收集 → 粗加工 → 维基提炼；路由决策：若 author 在 BLOGGER_CONSOLE 中，并行触发「博主画像纯提炼」 |
| 博主画像全流程 | 博主画像、画像更新 | 链接收集 → 粗加工 → 博主提炼 → 更新控制台 |
| 博主画像纯提炼 | 画像提炼（已有资源） | 博主提炼 → 更新控制台 |
| 仅问答 | 怎么看、分析、q&a | 知识问答 |
| 仅审查 | 审查、健康度、review | 维基审查 |
| 仅粗加工 | 粗加工、归档 | 粗加工 |
| 财报分析（双源） | 财报分析、结合框架分析 | 知识问答(source:both) → equity-research → QA_OUTPUT |
| 财报分析（仅 wiki） | 用 wiki 分析、结合投资框架 | 知识问答(source:wiki) → equity-research → QA_OUTPUT |
| 财报分析（仅博主） | 结合博主观点分析 | 知识问答(source:blogger) → equity-research → QA_OUTPUT |
| 财报分析（无背景） | 直接分析财报 | equity-research → QA_OUTPUT |

### 执行步骤

**第一步**：解析用户意图，匹配路由表
**第二步**：路由决策——若命中「投资知识全流程」，检查 source 的 `author` 是否在 BLOGGER_CONSOLE 中——若在，并行触发「博主画像纯提炼」链路
**第三步**：从路径表获取本次需要的常量
**第四步**：按所有匹配的调用链逐模块传入参数执行（多条链路独立并行，互不耦合）
**第五步**：每步完成后自检
**第六步**：确认所有匹配链路是否完整走完

---

## 路径表

| 常量 | 值 | 说明 |
|:---|:---|:---|
| VAULT_ROOT | /Users/jianglb/Library/Mobile Documents/iCloud~md~obsidian/Documents/我的知识库 | Obsidian vault 根目录 |
| ROUGH_DRAFTS | {VAULT_ROOT}/粗制品/ | 未分类内容暂存 |
| WIKI_RAW | {VAULT_ROOT}/原始资源仓库 | 归档后原始资源 |
| WIKI_TARGET | {VAULT_ROOT}/维基仓库/投资分析 | 结构化知识目录 |
| BLOGGER_PROFILE | {VAULT_ROOT}/维基仓库/博主画像 | 博主画像目录 |
| BLOGGER_CONSOLE | {VAULT_ROOT}/仪表盘/博主控制台.md | 博主注册控制台 |
| PENDING_QUEUE | {VAULT_ROOT}/仪表盘/待处理队列.md | 待处理队列 |
| QA_OUTPUT | {VAULT_ROOT}/问答看板 | 问答产物输出 |
| REVIEW_OUTPUT | {VAULT_ROOT}/问答看板 | 审查产物输出 |

> **运行时替换**：Agent 执行时需将 `{VAULT_ROOT}` 替换为上表中的实际路径。变更 vault 目录时只需修改 VAULT_ROOT 一行。

---

## 模板路径表

| 模板 | 路径 | 用途 |
|:---|:---|:---|
| raw-frontmatter | knowledge-pipeline/assets/raw-frontmatter.md | 原始资源 frontmatter |
| wiki-entry | knowledge-pipeline/assets/wiki-entry.md | 维基条目通用模板 |
| wiki-method | knowledge-pipeline/assets/wiki-method.md | 方法论条目 |
| wiki-case-study | knowledge-pipeline/assets/wiki-case-study.md | 案例条目 |
| wiki-data-interp | knowledge-pipeline/assets/wiki-data-interp.md | 数据解读条目 |
| wiki-opinion | knowledge-pipeline/assets/wiki-opinion.md | 观点条目 |
| wiki-market-overview | knowledge-pipeline/assets/wiki-market-overview.md | 市场概况条目 |
| blogger-frontmatter | knowledge-pipeline/assets/blogger-frontmatter.md | 博主画像 frontmatter |
| blogger-profile | knowledge-pipeline/assets/blogger-profile.md | 博主画像 11 章统一模板（含填充指引） |
| qa-output | knowledge-pipeline/assets/qa-output.md | 问答输出模板 |
| review-report | knowledge-pipeline/assets/review-report.md | 审查报告模板 |
| question-templates | knowledge-pipeline/assets/question-templates.md | 提问模板 |

## 规则文件路径表

| 规则文件 | 路径 | 用途 |
|:---|:---|:---|
| refine-rules | knowledge-pipeline/assets/refine-rules.md | 提炼规则定义（category映射、标题规则、frontmatter清单、提炼原则） |
| review-rules | knowledge-pipeline/assets/review-rules.md | 审查规则定义（维度阈值、合法值、正则模式、字段映射） |
| coarse-rules | knowledge-pipeline/assets/coarse-rules.md | 粗加工规则定义（逐字稿处理、清洗规则） |
| ingest-rules | knowledge-pipeline/assets/ingest-rules.md | 链接收集规则定义（工具映射、frontmatter字段） |
| blogger-rules | knowledge-pipeline/assets/blogger-rules.md | 博主提炼规则定义（控制台默认值、post_score、语录规则） |

---

## 调用链详情

### 投资知识全流程

**第一步**：链接收集 → `{ url, source_type, output_dir: ROUGH_DRAFTS }`
**第二步**：粗加工 → `{ source_path, target_dir: WIKI_RAW, type, template_path: raw-frontmatter, rules_path: coarse-rules }`
**第三步**：维基提炼 → `{ source_path, target_dir: WIKI_TARGET, category, content_type, time_sensitivity, template_path, rules_path: refine-rules }`
- template_path 按 content_type 选择：wiki-method / wiki-case-study / wiki-data-interp / wiki-opinion / wiki-market-overview
- 一篇素材可能产出 ≥1 条维基条目（提炼前分析后按概念拆分），每条以知识概念命名标题

### 博主画像全流程

**第一步**：链接收集 → `{ url, source_type, output_dir: ROUGH_DRAFTS }`
**第二步**：粗加工 → `{ source_path, target_dir: WIKI_RAW, type, template_path: blogger-frontmatter, rules_path: coarse-rules }`
**第三步**：读 BLOGGER_CONSOLE → 提取 config_snapshot = { name, aliases, is_xueqiu, is_following, is_starred }
**第四步**：博主提炼 → `{ source_path, config_snapshot, profile_path: BLOGGER_PROFILE/{name}.md, template_path: blogger-profile, rules_path: blogger-rules }` → 返回 { profile_content, console_delta }
**第五步**：写 profile_content 到 BLOGGER_PROFILE/{name}.md
**第六步**：用 console_delta 更新 BLOGGER_CONSOLE 对应行

### 博主画像纯提炼（已有原始资源）

**第一步**：读 BLOGGER_CONSOLE → config_snapshot
**第二步**：若画像不存在 → 扫描原始资源仓库（帖子/ + 长文/），收集该作者全部文章作为 source_paths
**第三步**：博主提炼 → `{ source_path, config_snapshot, profile_path, template_path: blogger-profile, rules_path: blogger-rules }` → 返回 { profile_content, console_delta }
**第四步**：写 profile_content
**第五步**：更新控制台

### 审查

**第一步**：维基审查 → `{ target_dir: WIKI_TARGET, dimensions, output_dir: REVIEW_OUTPUT, template_path: review-report, rules_path: review-rules }`

### 财报分析

财报作为分析素材，不进 pipeline 做提炼。pipeline 负责检索知识背景，交给 equity-research 插件做分析，产出存到问答看板。

**第一步**：解析用户输入 → 确定公司名、财报类型（年报/业绩公告/深度研究）、知识源选择（双源/仅 wiki/仅博主/无背景）
**第二步**：若需知识背景 → 知识问答 `{ question: "{公司名} {行业} 基本面 竞争格局", source: wiki/blogger/both, output_dir: QA_OUTPUT, template_path: qa-output }` → 检索结果作为 background
**第三步**：equity-research → 根据财报类型选择对应 skill
- 年报 PDF → equity-research:读年报({ pdf, background })
- 业绩公告 → equity-research:业绩快评({ pdf, background })
- 深度报告 → equity-research:深度报告({ company, materials, background })
**第四步**：分析产出保存到 {QA_OUTPUT}/YYYY年M月D日-{公司名}-财报分析.md

---

## Output Format

pipeline 向各加工 skill 传参的固定格式：

```
{ param1: value, param2: value, ... }
```

所有参数值从路径表和模板表取值，严禁硬编码。

---

## Relative Files

| 场景 | 加载文件 | 内容 |
|:---|:---|:---|
| 始终 | assets/raw-frontmatter.md | 原始资源 frontmatter 模板 |
| 始终 | assets/wiki-entry.md | 维基条目通用模板 |
| 提炼方法类 | assets/wiki-method.md | 方法论条目模板 |
| 提炼案例类 | assets/wiki-case-study.md | 案例条目模板 |
| 提炼数据类 | assets/wiki-data-interp.md | 数据解读条目模板 |
| 提炼观点类 | assets/wiki-opinion.md | 观点条目模板 |
| 提炼市场概况 | assets/wiki-market-overview.md | 市场概况条目模板 |
| 博主提炼 | assets/blogger-profile.md | 博主画像 11 章统一模板 |
| 博主粗加工 | assets/blogger-frontmatter.md | 博主画像 frontmatter |
| 问答时 | assets/qa-output.md | 问答输出模板 |
| 审查时 | assets/review-report.md | 审查报告模板 |
| 提炼规则 | assets/refine-rules.md | 提炼规则定义（category映射、标题规则、frontmatter清单） |
| 审查规则 | assets/review-rules.md | 审查规则定义（维度阈值、合法值、正则模式） |
| 粗加工规则 | assets/coarse-rules.md | 粗加工规则定义（逐字稿处理、清洗规则） |
| 链接收集规则 | assets/ingest-rules.md | 链接收集规则定义（工具映射、frontmatter字段） |
| 博主提炼规则 | assets/blogger-rules.md | 博主提炼规则定义（控制台默认值、post_score） |
| 生成问题时 | assets/question-templates.md | 提问模板参考 |

---

## Source Hierarchy

| 优先级 | 来源 | 涉及内容 |
|:---|:---|:---|
| 1 | 用户显式约定 | 目录结构、命名规范、日期格式、控制台默认值、渠道区分逻辑 |
| 2 | Obsidian 规范 | wikilink 完整路径、frontmatter 字段类型、Dataview 查询语法 |
| 3 | 工程实践验证 | 参数必填模式、单点配置原则、先读队列再扫目录 |

---

## 全局规则

- 日期格式：YYYY年M月D日
- 文件命名：不带日期前缀
- wikilink：完整路径，不加 emoji 前缀
- 控制台默认值：雪球博主=是、雪球关注=是、特别关注=否（空单元格=默认值）
- 提炼前必读控制台，提炼后必更新控制台
- **粗加工/提炼前必读 PENDING_QUEUE**，用 Dataview 查询确定待处理文件
- 加工 skill 全部参数必填，不传即报错
- 新增博主画像时，须扫描全部原始资源，收集该作者所有文章一并提炼
- 所有 vault 内路径均以 VAULT_ROOT 为基准，变更 vault 时只改路径表 VAULT_ROOT 一行
- VAULT_ROOT = `/Users/jianglb/Library/Mobile Documents/iCloud~md~obsidian/Documents/我的知识库`（iCloud Obsidian vault）
- 原始资源仓库位于 vault 根目录「原始资源仓库/」，博主画像与维基条目均位于「维基仓库/」下

---

## 语言约定

- 输入：接受中文
- 输出：默认中文
- 文件命名：中文文件名，不带日期前缀
- 日期格式：YYYY年M月D日

---

## 自检

- [ ] 用户意图是否在路由表中？
- [ ] 所有参数值是否来自路径表/模板表（非硬编码）？
- [ ] 是否已读 PENDING_QUEUE（粗加工/提炼流程）？
- [ ] 调用链是否完整执行？
- [ ] 财报分析路由：source 参数是否已传入知识问答？分析产出是否保存到 QA_OUTPUT？
