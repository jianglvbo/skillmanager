---
name: investment-framework
description: >
  投资知识框架全局编排者。管理三大归属层（我的/博主/其他）+ 六大分类（分析框架/交易体系/投资心态/投资心得/个股/行业）+ 宏观。
  定义流水线（粗制品→粗加工→原始资源→提炼方案→用户确认→提炼执行）、模板表、路径表、全局规则、审查机制。
  触发词：「投资框架」「框架全貌」「pipeline」「粗加工」「提炼」「归档」「审查」「review」。
  区别于 xq-post-fetch（只抓取帖子）：本 skill 是路径和模板的唯一持有者，负责串联全部加工模块。
license: MIT
agent_created: true
metadata:
  version: "1.2.0"
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
- **提炼方案驱动**：提炼 skill 分析原文后生成方案报告，用户确认或修改后再执行。一篇帖子可拆为多条框架条目。
- **跨层靠标签**：同一标的在三层都有时，通过 frontmatter 标签检索，不靠文件结构。
- **按需创建**：博主文件夹不预建空文件夹，有内容时才创建。

### 禁止行为

- 绝不修改 Obsidian vault 外的文件
- 绝不创建空博主文件夹——等有内容再建
- 绝不将非投资相关内容放入"其他"层——直接丢弃
- 绝不在"我的"层创建或修改文件——由用户自己管理
- 绝不丢弃有借鉴意义的内容
- 绝不在提炼时遗漏方案报告中的条目

---

## Workflow

### 路由表

| 用户意图 | 触发词 | 调用链 |
|:---|:---|:---|
| 全流程（新帖子） | 粗加工、提炼、归档 | investment-coarse-processor → investment-refine |
| 仅粗加工 | 粗加工、归档 | investment-coarse-processor |
| 仅提炼 | 提炼 | investment-refine（前置：原始资源须存在该文档且 `status=待提炼`；否则先从粗制品粗加工） |
| 审查 | 审查、review、健康度 | investment-review |
| 查看全貌 | 投资框架、框架全貌、pipeline | 输出框架说明 |

### 粗加工前置规则（重要）

提炼的输入**必须**是已完成粗加工、位于 `工作区/原始资源/` 且 `status=待提炼` 的文件，**禁止**直接在 `工作区/粗制品/` 上提炼。

判断以**原始资源为锚点**（不主动扫描粗制品目录，避免无谓的索引开销）：

- 用户要求「提炼」某文档时，编排者先查**原始资源**里是否已存在该文档且 `status=待提炼`。
- **若原始资源中已存在 `status=待提炼` 的该文档**：直接进入 `investment-refine` 两步模式。
- **若原始资源中不存在**（即没有 `status=待提炼` 的记录）：说明文档仍在 `工作区/粗制品/`，编排者须先调用 `investment-coarse-processor` 完成粗加工（粗加工会将其移入原始资源并置 `status=待提炼`），再进入 `investment-refine`。**不要跳过粗加工、直接在粗制品上提炼。**
- 用户说「粗加工+提炼」「全流程」「归档」时，自然走「粗加工 → 提炼」串联，无需额外判断。

### 粗加工 → investment-coarse-processor

调用 `investment-coarse-processor`，传入 `{ source_path, target_dir, blogger_console_path }`。该 skill 负责整理格式、去广告、补全 metadata 并移入原始资源目录。

### 提炼 → investment-refine（两步模式）

**第一步：提炼分析**——读取工作区/原始资源/ 下的文件全文，分析内容后生成提炼方案报告（输出到对话中，不写文件）。报告为分条目卡片式，每个条目包含：归属层、分类、建议标题、标签（来自标签体系）、拟用模板、内容摘要、条目间关联、拟写正文要点。
**第二步：用户确认**——用户审阅方案报告，可确认/修改/取消。
**第三步：提炼执行**——用户确认后，按方案逐条创建框架条目文件。如涉及已登记博主，更新博主档案；如涉及宏观事件，创建/更新宏观文件。
**第四步**：将原始资源文件的 status 改为 `已提炼`

### 审查 → investment-review

**第一步**：确定审查范围（内容审查 or 结构审查，见 references/review-rules.md）
**第二步**：内容审查——检查框架一致性、知行合一、我的 vs 博主冲突、经验验证
**第三步**：结构审查——检查归类正确性、frontmatter 完整性、wikilink 有效性、标签匹配
**第四步**：输出审查报告，标记问题项

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
| 分析框架-方法论 | investment-framework/assets/分析框架-方法论.md | 分析方法论条目 |
| 分析框架-分析档案 | investment-framework/assets/分析框架-分析档案.md | 具体标的分析记录 |
| 交易体系 | investment-framework/assets/交易体系.md | 交易规则条目 |
| 投资心态 | investment-framework/assets/投资心态.md | 心态问题/教训条目 |
| 投资心得 | investment-framework/assets/投资心得.md | 经验教训条目 |
| 宏观 | investment-framework/assets/宏观.md | 宏观事件分析条目 |
| 行业 | investment-framework/assets/行业.md | 行业分析条目 |
| 个股 | investment-framework/assets/个股.md | 个股信息枢纽条目 |
| 博主 | investment-framework/assets/博主.md | 博主档案条目 |

---

## Output Format

| 步骤 | 输出 | 位置 |
|:---|:---|:---|
| 粗加工 | 整理后的原始帖子 | {RAW_DIR}/{标题}.md |
| 提炼分析 | 提炼方案报告（分条目卡片式） | 输出到对话中 |
| 提炼执行 | 框架条目（≥1个文件） | 归属层/分类/{文件名}.md |
| 审查 | 审查报告 | 输出到对话中 |

---

## Relative Files

| 场景 | 加载文件 | 内容 |
|:---|:---|:---|
| 始终 | references/framework-rules.md | 框架边界规则、全局规则 |
| 提炼 | references/tag-taxonomy.md | 标签分类体系 + 编排派发规则 |
| 提炼/审查 | references/footnote-taxonomy.md | 脚注类型定义、格式规范、添加阶段 |
| 提炼 | assets/{模板名}.md | 对应分类的模板 |
| 审查 | references/review-rules.md | 审查维度和检查清单 |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式约定（三层归属、六大分类、博主控制台范围、标签检索） |
| 2 | Obsidian 规范（wikilink 完整路径、frontmatter 字段类型） |
| 3 | 投资研究最佳实践（方法论+分析档案分离、结果跟踪闭环） |
| 4 | 工程实践验证（单点配置、按需创建、方案报告驱动） |

---

## 自检

- [ ] 用户意图是否在路由表中？
- [ ] 所有路径是否来自路径表（非硬编码）？
- [ ] 粗加工是否只整理格式、不生成预览表？
- [ ] 提炼是否先出方案报告、用户确认后再执行？
- [ ] 方案报告中的标签是否来自标签体系？
- [ ] 博主归属是否仅限博主控制台已登记博主？
- [ ] "其他"层是否只包含投资相关的投资人内容？
- [ ] "我的"层是否未做任何修改？
- [ ] 待提炼文档是否在原始资源中存在且 `status=待提炼`？若否，是否已先从粗制品完成粗加工？
