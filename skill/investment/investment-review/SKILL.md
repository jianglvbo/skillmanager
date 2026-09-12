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
  排除条件：提炼与粗加工不归本 skill；框架路径/模板/规则以 investment-framework 为准，本 skill 只做审查并落库。

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

### 第零步之二：待复核队列处理（审查首步之二 · 必做；2026-09-12 新增）

用户原话：「显示你无法处理的需要我复核的帖子，这种帖子在下次审查的时候可以处理，并且内化规则，让我以后可以不用再审核类似的帖子」。队列在看板「待复核」页（左侧菜单，在「审查」**前面**），agent 侧走 `MCP pending_review`：

1. `action=list, status=pending_internalize` → **已答复但规则还没落地**的项（这批是本步的核心工作）；
2. 逐条：按用户答复**修数据**（改归类/补标的名/改时间/补别名…）→ 把答复**内化成规则/案例**（落点四选一，见 framework-rules #49：`framework-rules.md` 条目 / `stocks.aliases` / `mention_case` / `refine-schema.md` 细则）→ `action=internalize` 把落点写回 `internalized`；
2b. **`verdict=delete`（用户写了「删除：<理由>」）＝必须真的删**（2026-09-12 用户明确：「有的帖子质量不够，但是你提炼了，这种我就会在复核意见写上删除」）：
    - 取清单：`pending_review(action=list, status=pending_internalize, verdict=delete)`；
    - 逐条 `blogger_statement(action=delete, id)`（买卖帖走 `blogger_trade delete`）→ `action=internalize` 写「已删除言论 #id + 规则落点」；
    - **必须把删除理由内化**：追加到 `refine-schema.md` 信息密度门槛的**「用户删过的类型」判据表**，并按判据回看同批/存量同类帖子一并处理；
    - **不许反问用户「确定要删吗」**、不许只改内容、不许跳过（理由已给＝已授权；删除不可逆但这是用户明确要求）。
3. 再看 `action=list, status=open`：**还没答的**不要替用户决定——在报告里列出「待用户裁决 N 条」即可（含每条的问题与候选）；若发现某条其实规则已覆盖，改为 `action=resolve` 并写清依据（同时把规则落点写进 `internalized`）；
4. 报告里写明结果：**「待复核：处理 N 条（内化 M 条 / 忽略 K 条），仍待裁决 J 条」**。

**只答不内化＝违规**：用户答一次是为了以后不再答同类问题，答复不进规则就等于让用户重复劳动（framework-rules #49）。

### 内容审查（编号 C1-C10）

**C1**：读取参数 `{ scope_dirs, blogger_console_path }`；**C2**：扫描 scope_dirs 下所有 .md 文件
**C3**：内部一致性检查——交易体系的规则 vs 分析框架的方法论是否矛盾；**C4**：知行合一检查——投资心态中记录的纪律 vs 分析档案中的实际行为
**C5**：我的 vs 博主冲突检查（**可选，仅当用户显式要求时**）——默认不审查「我的」层（规则 #15 用户自管），若用户要求对比「我的」层方法论与「博主」层冲突，临时读取「我的」层执行
**C6**：经验验证检查——投资心得中的教训是否在后续分析档案中被验证
**C7**：关联备注——为缺少跨条目关联的条目补充脚注（脚注类型和格式见 `investment-framework/references/footnote-taxonomy.md`），在正文相关论述处嵌入标记，文末脚注定义（无 ## 脚注 标题、无 --- 分隔线）写 wikilink + 关系类型 + 一句话说明
**C8**：关系依据复核——逐条打开文件中**已存在**的关联脚注，核对目标文件原文是否支撑其关系声明；无依据的一律记为"编撰关系"，在报告中建议删除或降级为 enhance（见 footnote-taxonomy.md「关系依据校验」）
**C9**：输出内容审查报告
**C0（2026-09-12 新增）：别名与规则迭代核对**——审查时对「个股指代」做一次回看：① 言论里出现、但 `stocks.aliases` 未登记的称呼 → 补登（`stock_alias`）；② 被误挂的常用词（如「好美的风景」→ 美的集团）→ 改正关联 + 若缺歧义标记则 `mark-ambiguous` + 把案例写进 `stock-mention-rules.md` 误判清单；③ 报告里单列「本次新增别名 / 新增歧义词 / **新增判定案例** / 规则修订」四项，做到**知识随审查沉淀**；案例用 `stock_alias(action=case-add)` 落 `mention_case`，不要写进 md。

**C10**：言论追踪审计（执行 `scripts/tracks_audit.py --vault <vault路径> [--mysql]`，凭据用环境变量 `DB_PASS`）——**2026-09-12 重写后**核对 MySQL `statements`（六表视图）数据质量：空正文/缺原文链接/缺 `form`、`content_type` 与 `stance` 码值合法性、P1 三类（trade/predict/research）缺实体关联、复核建议积压（`statement_review_sub`）；兼看「insight 帖具象化覆盖率」（该有框架条目的心得帖要有 `wiki_ref`）。**原文留档覆盖率按 30 天窗口判**（`post_history_id` 回指，逾 30 天查不到属正常、不计缺口）。画像 md 已废弃，不再做 md↔DB 对照。**只报告不修改**，问题并入内容审查报告。

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

> **2026-08-16 起不产出 md 报告**：审查完成后按 `references/report-templates.md` 组装结构化 record，`MCP 工具 `review_record`（REST POST /api/review/record 兼容）` 写入投资看板（同 date 幂等覆盖）。落库失败不阻断主流程，但须提示「审查数据未落入看板，需补录」。

### 落库字段（完整明细见 `references/report-templates.md` §八）

| 字段 | 说明 |
|:---|:---|
| `c_groups` / `s_groups` | 内容审查（C3/C4/C6/C7/C8/C10）与结构审查（S 维度）分组；每项 `{title, severity, tag, headers, rows, text}` |
| `rows` | 推荐对象数组 `{列名: 值, 状态: pass\|fail\|warn}`（带状态列的表格必须显式给状态，看板据此渲染徽章） |
| `checks` | 脚本指标表；`recycle` 待回收处置（done/cooling/doneHist/rows）；`actions` 建议动作（num/text/status） |
| `meta` / `method` / `summary` / `mainProblems` | 范围与基线 / 方法 / 总结 / 主要问题（markdown 结构化，看板渲染小节与列表） |

> **修复动作不落库**：用户授权修复后另写 `修复记录-{YYYY-MM-DD}.md`（vault 执行日志），由审查 date 文字引用。

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

- [ ] **待复核队列是否处理**（第零步之二）？**`verdict=delete` 的项是否都真的删掉了**（言论已不存在）并把删除理由内化成低质帖判据？已答复未内化的项是否都**修了数据 + 内化成规则/案例 + 回写 `internalized`**？仍未裁决的项是否在报告里列清（未替用户决定）？报告是否写了「处理 N 条（内化 M / 忽略 K），仍待裁决 J 条」？
- [ ] 内容审查 C1-C10 是否全部执行？（读取参数、扫描、一致性、知行合一、我的vs博主〔仅用户要求时〕、经验验证、关联备注、关系依据复核、言论追踪审计 C10、输出报告）
- [ ] 结构审查 S1-S8 是否全部执行？（读取参数、归类、frontmatter完整性含updateDate/**author**/**source**、**字段顺序canonical(#27)**、**无流浪date(#27)**、引号有效性、wikilink含source字段、脚注格式、标签、输出报告）；归类正确性是否覆盖「博主层条目作者是否均在博主控制台登记，未登记者误挂需迁移其他层」？
- [ ] 审查范围是否正确排除「我的」层（规则 #15 用户自管）？是否仅覆盖 博主/其他/宏观？是否覆盖了编排者指定的所有目录？
- [ ] 脚注格式是否校验（无多余 `]]`、格式为 `[[target]] — 关系：说明`）？标签前缀是否全部在白名单内（enhance/supplement/conflict/complement/opposite/data/date）且与中文关系词一致？
- [ ] 是否存在孤儿脚注（有定义无内联标记）或悬空标记（有内联标记无定义）？已存在脚注是否逐条复核关系依据，编撰关系是否记入报告？
- [ ] 是否只输出了报告而未修改任何文件？关联备注提案中每条是否都有内容层面的依据（非编撰）？
- [ ] 待回收处置 R1-R5 是否执行？（扫描 delete 字段、按 7 天冷静期判定、超期者真删 + 双向清理、历史记录追加、报告给出理由）？
