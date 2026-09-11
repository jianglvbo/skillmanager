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
  version: "2.15.0"
  short-description: 投资框架审查执行器（含关联备注发现、言论追踪审计 C10）
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

### 第零步：复核建议处理（审查首步 · 必做）

按 `investment-framework/references/review-rules.md`「复核建议处理（审查首步）」执行：`console_statement_review(action=list, status=open)` 取全部未处理建议（返回含该言论当前 `contentType/stance/target/viewText` 上下文）→ 逐条按建议用 `blogger_statement(action=update)` 修正归类 → `console_statement_review(action=apply)` 置已处理；判断建议不成立则 `action=delete` 并在报告说明理由。**本步未处理完，不得进入 C/S 维度**；修正结果并入审查报告。

### 内容审查（编号 C1-C10）

**C1**：读取参数 `{ scope_dirs, blogger_console_path }`；**C2**：扫描 scope_dirs 下所有 .md 文件
**C3**：内部一致性检查——交易体系的规则 vs 分析框架的方法论是否矛盾；**C4**：知行合一检查——投资心态中记录的纪律 vs 分析档案中的实际行为
**C5**：我的 vs 博主冲突检查（**可选，仅当用户显式要求时**）——默认不审查「我的」层（规则 #15 用户自管），若用户要求对比「我的」层方法论与「博主」层冲突，临时读取「我的」层执行
**C6**：经验验证检查——投资心得中的教训是否在后续分析档案中被验证
**C7**：关联备注——为缺少跨条目关联的条目补充脚注（脚注类型和格式见 `investment-framework/references/footnote-taxonomy.md`），在正文相关论述处嵌入标记，文末脚注定义（无 ## 脚注 标题、无 --- 分隔线）写 wikilink + 关系类型 + 一句话说明
**C8**：关系依据复核——逐条打开文件中**已存在**的关联脚注，核对目标文件原文是否支撑其关系声明；无依据的一律记为"编撰关系"，在报告中建议删除或降级为 enhance（见 footnote-taxonomy.md「关系依据校验」）
**C9**：输出内容审查报告
**C10**：言论追踪审计（**2026-09-11 扩一项原文留档覆盖率**：查 MySQL `post_history` 与 `blogger_statements` 的对照——近批采集是否都有留档、留档的 `form`/`raw_text_len` 是否缺失，用于发现「采集漏落库」；只报告不修改，缺留档不阻断审查，仅提示后续采集补上）——执行 `scripts/tracks_audit.py --vault <vault路径>`（可选 `--mysql`，凭据经环境变量 `DB_PASS` 注入、勿硬编码），核对 MySQL `blogger_statements` 数据质量（缺原文链接/direction 码值合法性/标的占位残留；买卖帖＝`stmt_trade_src` 言论行，已无独立买卖表）；画像 md 已退役（2026-09-08），比对期可经 `POST /api/blogger/resync` 做 md↔DB 行数对照（只读核对，不作为写入依据）；只报告不修改，问题并入内容审查报告

### 结构审查（编号 S1-S8）——审查维度定义见 `investment-framework/references/review-rules.md`，按以下顺序执行。

**辅助 · 预扫（可选）**：① 结构/元数据——`scripts/vault_review.py --vault <vault路径>` 生成 `vault_review_result.json`（归类/frontmatter 含 updateDate/引号/wikilink 含 source/脚注格式/标签 六维 + 言论/买卖/预测三表原文链接（#35；画像 md 已退役，vault_review 的画像文件检查仅作比对期参考）/禁用 `## 来源`/source 形态（#23）/空壳 junk 扩展检查，只报告不修改）；② 段落布局——`investment-framework/scripts/verify-format.py <vault路径> --scope 其他,博主,宏观`（同行标题/标题间距/段落紧凑/脚注内联孤儿/模板残留，`--fix` 可自动修复）。人工据 JSON 撰写报告时聚焦机器无法判定的部分（段落缺失是否确无内容、标签语义、关联备注提案）。

**S1**：读取参数 `{ scope_dirs }`
**S2**：归类正确性——含博主层条目其作者是否均在博主控制台（看板 MySQL bloggers 表）登记，未登记者误挂博主层须标记迁移至其他层（见 framework-rules #12）
**S3**：frontmatter 完整性——必填字段 title/createDate/updateDate/**author**/tags/**source** 齐全（author/source 缺失即标记）；字段顺序须按所属分类模板 canonical 排列（标准 8 字段 `title→createDate→updateDate→author→star→delete→tags→source`，分析档案/宏观事件型见 framework-rules #27）；**禁止出现 `date` 字段**（层间边界硬约束，见 framework-rules #27）；日期字段裸写无引号
**S4**：引号有效性（全局规则 #21）
**S5**：wikilink 有效性——扫描**正文与 frontmatter `source` 字段**中的所有 wikilink，目标不存在即标记
**S6**：脚注格式——检查每条脚注定义的 wikilink 是否以单 `]]` 闭合（禁止 `]]]`/多余 `]]`），格式是否为 `[[target]] — 关系：说明`（见 footnote-taxonomy.md「格式校验」）。**额外必查**：(1) 标签前缀是否在白名单内（enhance/supplement/conflict/complement/opposite/data/date），非法标签如 `关联`/`ref` 一律标记；(2) 标签前缀与描述中中文关系词是否一致（enhance=增强、supplement=补充、conflict=冲突、complement=互补、opposite=对立、opposite=对立）；(3) 孤儿/悬空检查——每条定义必须有对应内联标记，每条内联标记必须有对应定义
**S7**：标签匹配；**S8**：输出结构审查报告

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
**R6（收尾 · 必做）**：**规律固化**——按 `review-rules.md`「规律固化（审查收尾步）」把本次全部发现（C 维度 + S 维度 + 复核建议处理）强制二分为「一次性数据问题 / 可泛化规律」；可泛化的必须当场回写对应规范（`framework-rules.md` 对应编号 / `investment-refine/SKILL.md` 判据 / 操作门脚本加校验项），并在落库 record 的 summary 与汇报中写明「本次固化了什么（文件+条目）、哪些判定一次性、未固化理由」。**未执行 R6 不得结束审查**。

---

## Output Format

> **2026-08-16 起：审查不再产出 md 报告文件，直接落库投资看板**。审查完成后按 `references/report-templates.md`（落库 schema 模板）组装结构化 record，`MCP 工具 `review_record`（REST POST /api/review/record 兼容，连接见 Ai/tools/investment-console-mcp/README.md）` 写入投资看板（幂等：同 date 覆盖）。落库失败不阻断主流程，但汇报中明确提示「审查数据未落入看板，需补录」。

### 内容审查（C 维度）

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| c_groups | array | 内容审查分组（C3 内部一致性 / C4 知行合一 / C6 经验验证 / C8 编撰脚注 / C7 关联提案 / C10 言论追踪审计），每项 `{title, severity, tag, headers, rows, text}` 入 `groups` 数组 |

**rows 推荐对象数组（看板 v0.12.61+ 支持，直观性最佳）**：每行 `{列名: 值, 状态: pass|fail|warn}`，列名与 headers 对应；`状态` 显式给出（C3 内部一致性、C4 知行合一、C6 经验验证等需状态列的表格必须带），供看板直接渲染状态徽章，不再靠结果文本推断：
```json
{ "title": "C3 内部一致性抽查", "severity": "ok", "tag": "C3",
  "headers": ["检查项", "结果"],
  "rows": [
    { "检查项": "HIS1963 新建4条 vs 既有", "结果": "认知演进自洽，非矛盾", "状态": "pass" },
    { "检查项": "永不补仓 vs 马丁反马丁", "结果": "跨作者相反指令，需裁决", "状态": "fail" }
  ] }
```
关联备注（C7）关系列值用统一词：`对立/冲突/互补/补充/增强/数据`（看板按词着色：对立粉紫、冲突红、互补绿、补充/增强蓝、数据灰）。headers 可由对象 keys 推导（可省略，但建议保留便于列序）。

**rows 中 wikilink 字段值**（含"条目/关联目标/博主/条目A/条目B/目标/来源"等列名的值）应为**真实存在的完整 vault 相对路径**（如 `博主/逻辑拐点/逻辑拐点.md`），含 `.md` 后缀、含目录前缀；**禁止描述性命名**（如"逻辑拐点画像·黄酒观点"——这种不可点击、不可验证，是 v0.12.65 前的旧妥协，看板 v0.12.69+ 已通过 linkReal 兜底但根因是审查方送的数据不精确）。去除 `[[]]` 包裹。

`/api/review/list` 会自动扫描每条 wikilink 在 vault 的存在性并注入 `linkExists: {path: true|false}` + `linkReal: {v: realRel}` 两份映射（v0.12.68/69 智能解析：①精确路径 ②补 .md ③index basename ④「博主名画像·主题」→博主画像 ⑤「博主名《标题》」→博主名下同名文件）。看板按 linkReal 优先展示《原文件名.md》+ 跳真实文件，缺失（linkReal==null）才走 linkExists 删除线+tooltip"待生成，建议由博主画像 skill 补全"。

**server 扫描必须兼容两种 rows 形态**（v0.12.73 教训：C6 经验验证用对象数组 rows 时被 `Array.isArray(row)` 过滤跳过，linkReal 无映射 → 看板误判"已删除"）：`Array.isArray(row) ? row[ci] : row[headers[ci]]` 取值。凡改 server 扫描逻辑，必须用「字符串数组 + 对象数组」两种 rows 各测一遍。

**"状态"列渲染契约**（v0.12.74）：rows 显式 `状态` 字段（headers 自带"状态"列或对象键 `status`）看板渲染为徽章（PASS 绿/FAIL 红/WARN 橙），**不允许落库纯文本 `warn` 之外的变体**；状态值统一 `pass/fail/warn`。C6 经验验证"待跟踪"预测语义 = warn（未验证/未证伪），待后续数据验证后更新 pass/fail。

**C7 headers 顺序固定**：`["条目", "关联目标", "说明", "关系"]`——关系列固定最右（与检查清单"状态"列右对齐，视觉统一），说明列位于关联目标与关系之间、宽度最大、承载完整理由。

**"说明"列必须写完整理由**（v0.12.69 用户反馈："显示尽可能完整"）：不少于一句完整话，包含**双方观点对比**（谁主张什么）与**关系判定**（为什么是对立/互补），便于后人无需读原文也能判断关联合理性。示例（合格）：`"逻辑拐点认为黄酒无高端土壤、炒炒别当真，与metalslime看多对立"`。反例（过短，不合格）：`"阿兰模型层视角，metalslime硬件层视角"`——只描述视角不说冲突点、无法裁决。

**审查脚本生成关联备注前必须校验目标文件已存在**：用 `getIndex().files` 查真实 rel；若未生成则**降级为"待补全关联"分组**（tag=`C7-pending`）或在说明里加 `[待生成]` 标记，**避免看板出现"建议建关系但目标不存在"的违和感**。

### 结构审查（S 维度）

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| s_groups | array | 结构审查分组（S2 归类错误 / S5 失效 Wikilink / S6 脚注格式 / S7 标签 / 模板段落缺失 / 其他结构问题），每项 `{title, severity, tag, headers, rows, text}` 入 `groups` 数组 |
| checks | array | 脚本指标（vault_review.py 输出表逐行）：`{item, result, compare, status}`，**status 统一落 `pass/fail/warn`**（勿落 ok/good/error/warning 等变体；看板接口已做兼容归一，但源头统一最干净）。**`item` 落库用中文**（v0.12.71 用户要求：检查项显示中文；审查脚本英文键 → 落库前按下方对照表映射中文），看板 CHECK_LABELS 亦维护全量英文键→中文映射兜底历史数据。**新增检查项时**：①脚本英文键同步进看板 CHECK_LABELS；②落库 item 用中文。**result/compare 只存纯数据，禁 emoji 徽章**（对勾/警示/叉号等符号）：result 只落数值/文本（如 `0`、`5`），状态图标由看板按 status_code 用 SVG 渲染，禁止把展示样式写进数据（2026-08-31 用户要求，违者视为数据污染）。 |

**检查项中文对照表**（英文键 → 落库中文）：

| 英文键 | 中文 | 英文键 | 中文 |
|:---|:---|:---|:---|
| `no_fm / fm_error` | frontmatter 缺失/格式错误 | `recycle_invalid` | 回收标记无效 |
| `missing_fields` | frontmatter 字段缺失 | `info_cutoff_mismatch` | info_cutoff 失同步 |
| `field_order` | frontmatter 字段顺序 | `quoting` | 引号规范 |
| `missing_core_sections` | 模板核心段落缺失 | `footnote_links_workspace` | 脚注链接指向工作区 |
| `wikilink_issues` | wikilink 失效 | `legacy_footnote_heading` | 旧式脚注标题 |
| `tag_issues` | 标签不匹配 | `forbidden_source_section` | 禁用 ## 来源 段 |
| `blogger_not_registered` | 博主未登记 | `source_as_invalid` | source 形态非法 |
| `stock_code_missing` | 股票代码缺失 | `stray_date` | 游离日期字段 |
| `recycle_pending` | 待回收条目 | `unclassified` | 未归类文件 |
| `recycle_expired` | 回收过期条目 | `junk_files` | 空壳文件 |
| `macro_template_mismatch` | 宏观模板不匹配 | `blogger_has_source` | 画像比对副本误含 source |
| `blogger_has_platform_id` | 画像副本误含 platform_id | `blogger_empty_link_row` | 画像副本空原文链接行 |
| `blogger_table_no_link_col` | 画像副本缺原文链接列 | `verify-format 段落布局` | 段落布局 |

### 总结与主要问题（结构化，便于看板直观展示）

`summary` 与 `mainProblems` 建议用结构化 markdown（看板渲染为小节标题 + 圆点列表 + 段落）：
- `###` 分小节（看板渲染为主题色小节标题）
- `- ` 无序列表 / `1. ` 有序列表（看板渲染为圆点列表）
- 普通段落一行一句，避免超长无断句段落

### 落库 record（组装规则）

| 字段 | 来源 |
|:---|:---|
| date / title | 审查日期与标题 |
| meta | 审查范围/扫描文件数/工具/对比基线/原则 |
| method | 审查方法简述 |
| mainProblems | 总体结论 |
| checks | 脚本指标表 |
| groups | **s_groups + c_groups 合并**（通用分组，看板自动渲染） |
| recycle | 待回收处置（done/cooling/doneHist/rows） |
| actions | 建议动作表（num/text/status） |
| summary | 总结与建议 |

> 落库 schema 见 `references/report-templates.md`。**修复动作不落库**：用户授权修复后另写 `修复记录-{YYYY-MM-DD}.md`（vault 执行日志），对应审查用 date 文字引用。

---

## Relative Files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| 审查时 | investment-framework/references/review-rules.md（由 investment-framework 编排者传入） | 审查维度和检查清单 | 读取 |
| 审查时 | investment-framework/references/footnote-taxonomy.md | 脚注类型定义、格式规范、添加阶段 | 读取 |
| 审查时 | references/report-templates.md | 审查落库 schema 模板（字段规范 + status 取值 + 落库调用规范 + 扩展机制） | 读取 |
| 结构审查预扫 | scripts/vault_review.py | 自动扫描脚本，输出 vault_review_result.json（只报告不修改） | **执行** |
| 段落布局预扫 | investment-framework/scripts/verify-format.py | 段落布局/脚注内联/模板废话/模板成分残留扫描（可 --fix 自动修复） | **执行** |
| 言论追踪审计（C10） | scripts/tracks_audit.py | 言论追踪专项审计：vault「言论追踪」section 质量 + MySQL tracks 数据质量/方向码值/同步一致性（--mysql 需 DB_PASS 环境变量） | **执行** |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 编排者传入的参数 |
| 2 | 用户约定（审查维度定义） |
| 3 | Obsidian frontmatter 规范 |

---

## 自检

- [ ] 内容审查 C1-C10 是否全部执行？（读取参数、扫描、一致性、知行合一、我的vs博主〔仅用户要求时〕、经验验证、关联备注、关系依据复核、言论追踪审计 C10、输出报告）
- [ ] 结构审查 S1-S8 是否全部执行？（读取参数、归类、frontmatter完整性含updateDate/**author**/**source**、**字段顺序canonical(#27)**、**无流浪date(#27)**、引号有效性、wikilink含source字段、脚注格式、标签、输出报告）；归类正确性是否覆盖「博主层条目作者是否均在博主控制台登记，未登记者误挂需迁移其他层」？
- [ ] 审查范围是否正确排除「我的」层（规则 #15 用户自管）？是否仅覆盖 博主/其他/宏观？是否覆盖了编排者指定的所有目录？
- [ ] 脚注格式是否校验（无多余 `]]`、格式为 `[[target]] — 关系：说明`）？标签前缀是否全部在白名单内（enhance/supplement/conflict/complement/opposite/data/date）且与中文关系词一致？
- [ ] 是否存在孤儿脚注（有定义无内联标记）或悬空标记（有内联标记无定义）？已存在脚注是否逐条复核关系依据，编撰关系是否记入报告？
- [ ] 是否只输出了报告而未修改任何文件？关联备注提案中每条是否都有内容层面的依据（非编撰）？
- [ ] 待回收处置 R1-R5 是否执行？（扫描 delete 字段、按 7 天冷静期判定、超期者真删 + 双向清理、历史记录追加、报告给出理由）？
