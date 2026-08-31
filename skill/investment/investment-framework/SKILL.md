---
name: investment-framework
description: >
  投资知识框架全局编排者。管理三大归属层（我的/博主/其他）+ 六大分类（分析框架/交易体系/投资心态/投资心得/个股/行业）+ 宏观。
  定义流水线（粗制品→粗加工→原始资源→提炼→审查）、模板表、路径表、全局规则、审查机制。
  触发词：「投资框架」「框架全貌」「pipeline」「粗加工」「提炼」「归档」「审查」「review」。
  区别于 xq-post-fetch（只抓取帖子）：本 skill 是路径和模板的唯一持有者，负责串联全部加工模块。
license: MIT
agent_created: true
metadata:
  version: "2.15.0"
  short-description: 投资知识框架全局编排者
compatibility: 通用
---

# 投资知识框架 · 全局编排者

唯一持有路径、模板、流水线规则的地方。

---

## Default Stance

### 核心原则

- **单点配置**：所有路径、模板、规则只在此定义。变更 vault 目录时只改 VAULT_ROOT 一行。
- **三层归属 + 宏观双层**：我的（用户自管）/ 博主（已登记）/ 其他（未登记投资人）。宏观分两层：顶层 `宏观/` 存通用框架，归属层下 `宏观/` 存该来源的具体分析。
- **提炼直接执行**：提炼 skill 读取原文后直接分析、创建条目、汇报结果，不需用户逐步确认。一篇帖子可拆为多条框架条目。
- **跨层靠标签**：同一标的在三层都有时，通过 frontmatter 标签检索，不靠文件结构。
- **按需创建**：任何层级目录都不预建空文件夹，有内容写入时才创建；发现空文件夹应清理（「我的」层由用户自管，不主动删）。

### 禁止行为

- 绝不修改 Obsidian vault 外的文件
- 绝不预建或保留任何层级的空文件夹——有内容写入时再建
- 绝不将非投资相关内容放入"其他"层——直接丢弃
- 绝不在"我的"层创建或修改文件——由用户自己管理
- 绝不丢弃有借鉴意义的内容
- 绝不在提炼时遗漏有借鉴意义的内容

---

## Workflow

### 路由表

| 用户意图 | 触发词 | 调用链 |
|:---|:---|:---|
| 全流程（新帖子） | 粗加工、提炼、归档 | investment-coarse-processor → investment-refine |
| 仅粗加工 | 粗加工、归档 | investment-coarse-processor |
| 仅提炼 | 提炼 | investment-refine（前置：原始资源须存在该文档且 `status=待提炼`；否则先从粗制品粗加工） |
| 帖子集提炼 | 帖子集提炼、采集后提炼 | investment-refine（#29 例外：直接从粗制品提炼 → 删源文件） |
| 截图/链接直投 | （用户发送雪球截图+链接） | #30 直投路径：粗制品(临时) → 提炼 → 删源文件 |
| 审查 | 审查、review、健康度 | investment-review |
| 查看全貌 | 投资框架、框架全貌、pipeline | 输出框架说明 |

### 粗加工前置规则（重要）

提炼的输入**必须**是已完成粗加工、位于 `工作区/原始资源/` 且 `status=待提炼` 的文件，**禁止**直接在 `工作区/粗制品/` 上提炼。

判断以**原始资源为锚点**（不主动扫描粗制品目录，避免无谓的索引开销）：

- 用户要求「提炼」某文档时，编排者先查**原始资源**里是否已存在该文档且 `status=待提炼`。
- **若原始资源中已存在 `status=待提炼` 的该文档**：直接进入 `investment-refine`。
- **若原始资源中不存在**（即没有 `status=待提炼` 的记录）：说明文档仍在 `工作区/粗制品/`，编排者须先调用 `investment-coarse-processor` 完成粗加工（粗加工会将其移入原始资源并置 `status=待提炼`），再进入 `investment-refine`。**不要跳过粗加工、直接在粗制品上提炼。**
- 用户说「粗加工+提炼」「全流程」「归档」时，自然走「粗加工 → 提炼」串联，无需额外判断。
- **例外（#29 帖子集）**：`type: 帖子集` 直接从粗制品提炼，跳过粗加工和原始资源，提炼后源文件移废纸篓。提炼路由同 #30：言论追踪 / 买卖记录 / 预测记录 → 对应博主画像文件；有框架价值 → 同时产出 wiki 条目；二者可兼得。
- **例外（#30 截图/链接直投）**：用户直接发送雪球截图（可能多张）+ 出处链接 + 关联股票。等同于 xq-post-fetch 采集的博主言论，跳过粗加工和原始资源。路径：粗制品(临时) → 直接提炼 → 删源文件。提炼路由由 agent 判断内容类型：言论追踪 / 买卖记录 / 预测记录 → 对应博主画像文件；有框架价值 → 同时产出 wiki 条目。

### 粗加工 → investment-coarse-processor

调用 `investment-coarse-processor`，传入 `{ source_path, target_dir, blogger_console_path }`。该 skill 负责整理格式、去广告、补全 metadata 并移入原始资源目录。**硬约束：绝不修改/精简/重组正文内容**——正文（含图片引用、转录稿段落、重复内容）原封不动保留，只动 frontmatter 和末尾工具广告。

### 提炼 → investment-refine（直接执行）

**第一步：分析原文**——读取源文件全文（常规：原始资源；帖子集：粗制品），分析内容，判断归属层、分类、标签、库内关系。
**第二步：创建条目**——按分析结果直接创建框架条目文件。如涉及已登记博主，更新博主档案；如涉及宏观事件，创建/更新宏观文件。
**第三步：汇报 + 收尾**——向用户报告产出条目；将源文件 status 改为 `已提炼`（常规）或移入废纸篓（帖子集 #29）。

### 审查 → investment-review

**第一步**：确定审查范围（内容审查 or 结构审查，见 references/review-rules.md）
**第二步**：内容审查——检查框架一致性、知行合一、我的 vs 博主冲突、经验验证
**第三步**：结构审查——检查归类正确性、frontmatter 完整性、wikilink 有效性、标签匹配
**第四步**：组装结构化落库数据（按 investment-review/references/report-templates.md 的 schema），`MCP 工具 `review_record`（REST POST /api/review/record 兼容，连接见 Ai/tools/investment-console-mcp/README.md）` 写入投资看板（2026-08-16 起不再产出 md 审查报告）
**第五步（待回收处置 · 默认执行）**：审查扫描全部内容型条目的 `delete` 字段（见 framework-rules #26），按 7 天冷静期处置超期条目（真删 + 双向清理）并出「待回收处置」数据（入落库 recycle 字段）给出理由；未到期条目在数据中提示剩余天数

### 操作门（事前校验 · 2026-08-14 新增）

原则：**问题在产生当天拦截，不等每周审查**——每个流水线操作在出口必须过校验门，审查降级为兜底网（2026-08-14 教训：13 处悬空引用/29 处 info_cutoff/34 处模板段落全部机器可检，却积压 7 周至审查才暴露）。

| 操作 | 出口校验门 | 工具 |
|:---|:---|:---|
| 采集/同步后（xq-post-fetch 前置步骤） | 控制台-画像 info_cutoff 一致 + 博主层残留检测 | execution-guide 第 6-7 步 |
| 提炼后（refine 第二步收尾） | 段落布局/模板段落完整 0 问题 | scripts/verify-format.py |
| **删除/回收/移动前**（#25/#26） | inbound 引用反查，清理完才允许删 | scripts/check_inbound.py |
| 任意批量操作后 / 提交前 | 增量扫描 git 变更文件（秒级） | investment-review/scripts/vault_review.py --incremental |

每周审查仍保留：内容层（C3 一致性 / C4 知行合一 / C6 经验验证 / C7 关联备注）+ 待回收处置，是操作门覆盖不到的兜底网。

### 看板联动（investment-console · 2026-08-17 新增）

流水线结果写入本地看板（`http://127.0.0.1:8698`，端口 8698，launchd 托管），看板不产生知识、只呈现结果：

- **提炼** → `MCP refine_record`（refine 第四步已实现，targets 含 thinking 5 步/basis/why/relation）→ 提炼时间轴 + 决策链路图
- **审查** → `MCP review_record`（review 第四步已实现）→ 审查模块（2026-08-16 起不再产出 md 审查报告）
- **预测控制台**（2026-08-31 方案 A：MySQL 唯一存储，vault 不再存控制台 Markdown）→ `MCP console_list_subjects / console_get_subject / console_add_prediction / console_update_status / console_add_track`（见 prediction-console skill v2.0）→ 看板预测控制台模块（个股/行业/市场三页签）
- **决策链路图 10 节点规范**（用户拍板）：源→识别→◆归属层判断◆→拆分决策→三列分叉（价值/归类/◆关系判断◆/生成/产物卡）→汇合→校验；**判断只留给有真实分叉的节点**（归属层/关系）；关系判断=生成决策（thinking[3]），审查 C3/C7=写后质检，不重复
- **产物展示**：多产物**横向并联**（产物徽章并排、无箭头，不用 SVG 分叉图——用户试用后否决）
- 失败处理：API 失败不阻断主流程，汇报提示「看板数据未写入」
- 完整契约/渲染要点/设计铁律 → `references/console-guide.md`

---

## 动态上下文（运行时注入）

执行任何流水线步骤前，编排者**必须**先获取以下环境信息（不靠记忆、不靠脑补）：

| 信息 | 获取方式 | 用途 |
|:---|:---|:---|
| 当前日期 | `date "+%Y-%m-%d"` | 框架条目 `updateDate`、审查冷静天数计算（review R2）、博主控制台「信息截止」更新（xq-post-fetch 第八步） |
| 当前时间 | `date "+%Y-%m-%d %H:%M"` | 雪球采集时间窗口基准（xq-post-fetch 第四步） |
| 待提炼文档状态 | 查询原始资源 frontmatter `status` | 判定走粗加工 or 直接提炼（粗加工前置规则） |

> 各执行 skill 在需要时自行获取（如 refine 写 `updateDate` 前、review 算冷静天数前、xq-post-fetch 时间窗口前），编排者不代为传递时间戳。

---

## 路径表

| 常量 | 值 | 说明 |
|:---|:---|:---|
| VAULT_ROOT | /Users/jianglb/Library/Mobile Documents/iCloud~md~obsidian/Documents/投资知识库 | vault 根目录 |
| MY_DIR | {VAULT_ROOT}/我的 | 用户自管层 |
| BLOGGER_DIR | {VAULT_ROOT}/博主 | 已登记博主层 |
| OTHER_DIR | {VAULT_ROOT}/其他 | 未登记投资人层 |
| MACRO_DIR | {VAULT_ROOT}/宏观 | 通用宏观框架与分析工具 |
| MACRO_BLOGGER | {BLOGGER_DIR}/{博主名}/宏观 | 该博主对具体宏观事件的分析 |
| MACRO_OTHER | {OTHER_DIR}/宏观 | 未登记投资人对具体宏观事件的分析 |
| ROUGH_DIR | {VAULT_ROOT}/工作区/粗制品 | 粗制品暂存 |
| RAW_DIR | {VAULT_ROOT}/工作区/原始资源 | 粗加工后原始资源 |
| BLOGGER_CONSOLE | {VAULT_ROOT}/工作区/博主控制台.md | 博主注册控制台 |

---

## 模板路径表

| 模板 | 路径 | 用途 |
|:---|:---|:---|
| 分析框架-方法论 | investment-framework/assets/分析框架-方法论.md | 分析方法论条目（纯结构骨架） |
| 分析框架-分析档案 | investment-framework/assets/分析框架-分析档案.md | 具体标的分析记录（纯结构骨架） |
| 交易体系 | investment-framework/assets/交易体系.md | 交易规则条目（纯结构骨架） |
| 投资心态 | investment-framework/assets/投资心态.md | 心态问题/教训条目（纯结构骨架） |
| 投资心得 | investment-framework/assets/投资心得.md | 经验教训条目（纯结构骨架） |
| 宏观 | investment-framework/assets/宏观.md | 宏观事件分析条目（纯结构骨架） |
| 行业 | investment-framework/assets/行业.md | 行业分析条目（纯结构骨架） |
| 个股 | investment-framework/assets/个股.md | 个股信息枢纽条目（纯结构骨架） |
| 博主 | investment-framework/assets/博主.md | 博主档案条目（纯结构骨架） |

> 模板 = 纯结构骨架（字段 + section 标题 + 表格表头），**不含解释**。各 section 的写作指引统一在 `references/template-guide.md`；字段/标签/来源/脚注规则见 framework-rules / tag-taxonomy / footnote-taxonomy。产出文件可保留模板空结构（空 section / 空表格表头），但不得出现模板解释残留（花括号占位、blockquote 指引、frontmatter 注释、全空占位行，verify-format.py 检测）。

---

## Output Format

编排者自身不产出文件，输出为对下游模块的调度结果与汇报：

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| routed_skill | string | 本次调度的下游 skill（coarse-processor / refine / review） |
| output_summary | string | 下游执行结果摘要（产出条目数、更新档案等） |
| next_action | string | 后续动作提示（如"源文件待提炼"） |

下游具体产出物（粗加工原始帖子、框架条目、审查落库数据）由各 skill 的 Output Format 定义，位置见下方路径表。

---

## Relative Files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| 始终 | references/framework-rules.md | 框架边界规则、全局规则 | 读取 |
| 提炼 | references/template-guide.md | 各模板 section 写作指引（模板为纯结构骨架，写作要求统一在此） | 读取 |
| 提炼 | references/tag-taxonomy.md | 标签分类体系 + 编排派发规则 | 读取 |
| 提炼/审查 | references/footnote-taxonomy.md | 脚注类型定义、格式规范、添加阶段 | 读取 |
| 提炼 | assets/{模板名}.md | 对应分类的模板（纯结构骨架） | 读取 |
| 审查 | references/review-rules.md | 审查维度和检查清单 | 读取 |
| 看板联动 | references/console-guide.md | 看板数据契约（refine/review 落库）、决策链路图 10 节点规范、产物展示约定、前端设计铁律 | 读取 |
| 审查（段落布局） | scripts/verify-format.py | 段落布局/脚注内联/模板废话/模板成分残留（空表格行/来源blockquote/frontmatter注释/花括号占位）扫描（可 --fix 自动修复）。**纯标准库无第三方依赖**（2026-08-14 起，原依赖 PyYAML） | **执行** |
| 删除/回收/移动前（#25/#26） | scripts/check_inbound.py | inbound 引用反查（wikilink/脚注/source 字段），双向清理范围确认工具 | **执行** |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式约定（三层归属、六大分类、博主控制台范围、标签检索） |
| 2 | Obsidian 规范（wikilink 完整路径、frontmatter 字段类型） |
| 3 | 投资研究最佳实践（方法论+分析档案分离、结果跟踪闭环） |
| 4 | 工程实践验证（单点配置、按需创建、直接执行） |

---

## 自检

- [ ] 用户意图是否在路由表中？
- [ ] 所有路径是否来自路径表（非硬编码）？
- [ ] 粗加工是否只整理格式、不生成预览表？
- [ ] 提炼是否直接执行并汇报结果（无等待确认环节）？
- [ ] 提炼产出的标签是否来自标签体系？
- [ ] 博主归属是否仅限博主控制台已登记博主？是否存在 Agent 自动补登（违规）或未登记作者误挂博主层？
- [ ] 待回收处置是否严格按 #26（用户加 `delete` 字段标记、状态由审查计算、7 天冷静期、超期真删+双向清理+理由报告），Agent 不替用户标记、不 shortcut？**粗制品例外**：`工作区/粗制品/` 跳过冷静期即时可回收（2026-08-16 确认），内容型条目绝不缩短？
- [ ] "其他"层是否只包含投资相关的投资人内容？
- [ ] "我的"层是否未做任何修改？
- [ ] 待提炼文档是否满足前置条件？（常规：原始资源 `status=待提炼`；帖子集：粗制品 `type: 帖子集` 按 #29 直接提炼）
- [ ] **操作门是否已过**（2026-08-14 新增）？——删除/回收/移动前是否已运行 `check_inbound.py` 反查并清理引用？批量操作后是否已运行 `vault_review.py --incremental` 增量校验？
- [ ] **看板是否已联动**（2026-08-17 新增）？——提炼后是否 `MCP refine_record`（targets 含 thinking 5 步/basis/why/relation）？审查后是否 `MCP review_record`？API 失败时是否汇报「看板数据未写入」？（契约见 references/console-guide.md）
