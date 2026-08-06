---
name: investment-review
description: >
  投资框架审查执行器。执行内容审查（框架一致性、知行合一、我的vs博主冲突、经验验证、跨条目关联备注发现）
  和结构审查（归类正确性、frontmatter完整性、wikilink有效性、标签匹配）。
  触发词：「审查」「review」「健康度」「框架检查」。
  由 investment-framework 编排调用，不独立触发。
license: MIT
agent_created: true
metadata:
  version: "2.13.0"
  short-description: 投资框架审查执行器（含关联备注发现）
compatibility: 通用
---

# 审查执行器

---

## Default Stance

### 核心原则

- **两层审查独立执行**：内容审查和结构审查分步进行，各自产出独立报告
- **只报告不修改**：审查只输出问题清单和关联备注提案，不直接修改文件，由用户决定是否采纳
- **关联备注在审查阶段发现**：内容审查时扫描全 vault 条目，为缺少跨条目关联的条目提议补充脚注。脚注类型、格式和规则详见 `investment-framework/references/footnote-taxonomy.md`（与 tag-taxonomy.md 同级，位于 investment-framework/references/）。关联脚注以脚注形式嵌入正文相关论述处，不用独立 `## 关联` section。提炼阶段可加 `[^data-N]`（数据溯源）和 `[^date-N]`（时效标注），关联脚注仅在审查阶段添加
- **参数全部由编排者传入**：审查范围、目标目录由编排者指定
- **待回收处置例外**：全局规则 #26 的回收执行（真删 + 双向清理）属于用户经 `delete` 字段标记 + 7 天冷静期已授权的既定动作，审查直接执行并出「待回收处置报告」给出理由；其余审查发现（关联备注等）仍仅报告不修改

### 禁止行为

- 绝不直接修改任何框架文件——关联备注提案仅出现在报告中，用户确认后才写入（待回收处置的回收执行除外，属 #26 已授权动作）
- 绝不审查或修改"我的"层——「我的」层由用户自管（规则 #15），审查范围仅限 博主/其他/宏观
- 绝不将结构问题与内容问题混在同一份报告中
- 绝不在关联备注中编撰原文没有的关系——每条关联必须有内容层面的依据

---

## Workflow

### 内容审查（编号 C1-C9）

**C1**：读取参数 `{ scope_dirs, blogger_console_path }`
**C2**：扫描 scope_dirs 下所有 .md 文件
**C3**：内部一致性检查——交易体系的规则 vs 分析框架的方法论是否矛盾
**C4**：知行合一检查——投资心态中记录的纪律 vs 分析档案中的实际行为
**C5**：我的 vs 博主冲突检查（**可选，仅当用户显式要求时**）——默认不审查「我的」层（规则 #15 用户自管），若用户要求对比「我的」层方法论与「博主」层冲突，临时读取「我的」层执行
**C6**：经验验证检查——投资心得中的教训是否在后续分析档案中被验证
**C7**：关联备注——为缺少跨条目关联的条目补充脚注（脚注类型和格式见 `investment-framework/references/footnote-taxonomy.md`），在正文相关论述处嵌入标记，文末脚注定义写 wikilink + 关系类型 + 一句话说明
**C8**：关系依据复核——逐条打开文件中**已存在**的关联脚注，核对目标文件原文是否支撑其关系声明；无依据的一律记为"编撰关系"，在报告中建议删除或降级为 enhance（见 footnote-taxonomy.md「关系依据校验」）
**C9**：输出内容审查报告

### 结构审查（编号 S1-S8）

审查维度定义见 `investment-framework/references/review-rules.md`，按以下顺序执行。

**辅助 · 自动预扫（可选）**：可先调用 `scripts/vault_review.py --vault <vault路径>` 自动扫描，生成 `vault_review_result.json`，覆盖归类 / frontmatter 完整性（含 updateDate）/ 引号 / wikilink（正文 + `source` 字段）/ 脚注格式 / 标签 六维，外加扩展检查（博主画像三表原文链接检查（规则 #35）、禁用 `## 来源` 段、source 形态校验（规则 #23：内部→wikilink、外部→[标题](URL)、禁裸 URL/批次名/手写占位）、空壳 junk）。脚本严格遵守「只报告不修改」原则，仅输出 JSON。人工据 JSON 撰写报告时，聚焦机器无法判定的部分（如段落缺失是否因确无内容、标签语义是否匹配、关联备注提案）。

**辅助 · 段落布局预扫（可选）**：可追加调用 `investment-framework/scripts/verify-format.py <vault路径> --scope 其他,博主,宏观` 扫描段落布局问题（同行标题、标题间距、段落紧凑、脚注内联标记孤儿、脚注模板废话、残留 `## 来源`/空 `## 脚注`），与 vault_review.py 互补——前者覆盖结构/元数据，后者覆盖排版/脚注内联。加 `--fix` 可自动修复可修复项。

**S1**：读取参数 `{ scope_dirs }`
**S2**：归类正确性——含博主层条目其作者是否均在「博主控制台」登记，未登记者误挂博主层须标记迁移至其他层（见 framework-rules #12）
**S3**：frontmatter 完整性——必填字段 title/createDate/updateDate/**author**/tags/**source** 齐全（author/source 缺失即标记）；字段顺序须按所属分类模板 canonical 排列（标准 `title→createDate→updateDate→author→tags→source`，分析档案/宏观事件型见 templates）；**禁止出现 `date` 字段**（层间边界硬约束，见 framework-rules #27）；日期字段裸写无引号
**S4**：引号有效性（全局规则 #21）
**S5**：wikilink 有效性——扫描**正文与 frontmatter `source` 字段**中的所有 wikilink，目标不存在即标记
**S6**：脚注格式——检查每条脚注定义的 wikilink 是否以单 `]]` 闭合（禁止 `]]]`/多余 `]]`），格式是否为 `[[target]] — 关系：说明`（见 footnote-taxonomy.md「格式校验」）。**额外必查**：(1) 标签前缀是否在白名单内（enhance/supplement/conflict/complement/data/date），非法标签如 `关联`/`ref` 一律标记；(2) 标签前缀与描述中中文关系词是否一致（enhance=增强、supplement=补充、conflict=冲突、complement=互补）；(3) 孤儿/悬空检查——每条定义必须有对应内联标记，每条内联标记必须有对应定义
**S7**：标签匹配
**S8**：输出结构审查报告

### 待回收处置（审查时执行，编号 R1-R5）

按全局规则 #26（delete 字段机制）处置待回收条目——**不再解析表格**，改为扫描内容型条目的 `delete` 字段。无独立回收控制台（历史由系统废纸篓兜底）。

**R1**：扫描 scope_dirs 下所有内容型条目的 frontmatter，收集含 `delete` 字段的条目，提取标记日期 `delete`（YYYY-MM-DD）
**R2**：对每个标记条目计算 `冷静天数 = today - delete`
**R3**：分支判定
- 若 `冷静天数 > 7` → 标记「本次将回收」，执行 R4
- 若 `冷静天数 ≤ 7` → 跳过，报告中提示剩余天数（`待回收（剩 N 天）`）
**R4（回收执行 · 真删 + 双向清理）**：对超期条目
- 反查 vault 中所有**指向该条目**的 wikilink 与关联脚注（含博主档案、其他条目、frontmatter `source` 字段），列出清单
- 清理这些 inbound 引用（移除脚注定义 + 正文标记，或档案 wikilink 行），保持无悬空链接
- 将条目文件移出 vault（移至系统废纸篓，完成真删），记录清理了 M 处引用
**R5**：输出「待回收处置报告」，**必须给出每条回收的理由**（超 7 天冷静期 + 标记日期 + 清理引用数）；未到期者提示剩余天数

---

## Output Format

### 内容审查报告

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| consistency_issues | list | 内部一致性问题 |
| action_alignment_issues | list | 知行合一问题 |
| framework_conflicts | list | 我的 vs 博主冲突 |
| verification_gaps | list | 未验证的经验教训 |
| fabricated_footnotes | list | 编撰关系脚注（已存在但目标文件无原文依据，建议删除或降级） |
| cross_reference_proposals | list | 提议的跨条目关联（条目路径 + wikilink + 关系类型 + 一句话说明） |

报告模板见 `references/report-templates.md`（内容审查报告模板），输出到对话中。

### 结构审查报告

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| misplaced_files | list | 归类错误的文件 |
| incomplete_frontmatter | list | frontmatter 缺失的文件（含 updateDate 缺失） |
| quoting_issues | list | frontmatter 引号格式错误的文件 |
| broken_links | list | 失效的 wikilink（正文 + source 字段） |
| footnote_format_issues | list | 脚注格式错误（多余 `]]`/格式不符 `[[target]] — 关系：说明`） |
| tag_mismatches | list | 标签不匹配的条目 |

报告模板见 `references/report-templates.md`（结构审查报告模板 + 待回收处置报告模板），输出到对话中。

---

## Relative Files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| 审查时 | investment-framework/references/review-rules.md（由 investment-framework 编排者传入） | 审查维度和检查清单 | 读取 |
| 审查时 | investment-framework/references/footnote-taxonomy.md | 脚注类型定义、格式规范、添加阶段 | 读取 |
| 审查时 | references/report-templates.md | 内容/结构/待回收处置三份报告模板 | 读取 |
| 结构审查预扫 | scripts/vault_review.py | 自动扫描脚本，输出 vault_review_result.json（只报告不修改） | **执行** |
| 段落布局预扫 | investment-framework/scripts/verify-format.py | 段落布局/脚注内联/模板废话扫描（可 --fix 自动修复） | **执行** |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 编排者传入的参数 |
| 2 | 用户约定（审查维度定义） |
| 3 | Obsidian frontmatter 规范 |

---

## 自检

- [ ] 内容审查 C1-C9 是否全部执行？（读取参数、扫描、一致性、知行合一、我的vs博主〔仅用户要求时〕、经验验证、关联备注、关系依据复核、输出报告）
- [ ] 结构审查 S1-S8 是否全部执行？（读取参数、归类、frontmatter完整性含updateDate/**author**/**source**、**字段顺序canonical(#27)**、**无流浪date(#27)**、引号有效性、wikilink含source字段、脚注格式、标签、输出报告）；归类正确性是否覆盖「博主层条目作者是否均在博主控制台登记，未登记者误挂需迁移其他层」？
- [ ] 审查范围是否正确排除「我的」层（规则 #15 用户自管）？是否仅覆盖 博主/其他/宏观？
- [ ] 脚注格式是否校验（无多余 `]]`、格式为 `[[target]] — 关系：说明`）？
- [ ] 脚注标签前缀是否全部在白名单内（enhance/supplement/conflict/complement/data/date）？标签与中文关系词是否一致？
- [ ] 是否存在孤儿脚注（有定义无内联标记）或悬空标记（有内联标记无定义）？
- [ ] 已存在脚注是否逐条复核关系依据，编撰关系是否记入报告？
- [ ] 是否只输出了报告而未修改任何文件？
- [ ] 审查范围是否覆盖了编排者指定的所有目录？
- [ ] 关联备注提案中每条是否都有内容层面的依据（非编撰）？
- [ ] 待回收处置 R1-R5 是否执行？（扫描 delete 字段、按 7 天冷静期判定、超期者真删 + 双向清理、历史记录追加、报告给出理由）？
