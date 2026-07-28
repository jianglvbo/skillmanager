# Changelog

## 2026-07-22
- `investment-refine/SKILL.md`（v2.5.1）：
  - 写入硬约束新增「原文链接格式」：表格内链接一律 `[原文](URL)`，禁止裸 URL（#30）
  - 根因：审计发现 6 个博主档案 117 处言论追踪原文链接为裸 URL（子 Agent 写入时未遵守 #30），已全部修复
- `investment-refine/SKILL.md`（v2.5.0）：
  - Workflow 第二步新增「写入硬约束」子节：wikilink 完整路径（禁止 basename）、个股文件名带代码、禁止 `## 来源` 段、模板 section 全量输出、字段顺序 canonical、日期裸写
  - 言论追踪具象化指针显式要求完整路径 `见 [[博主/{名}/{分类}/{文件名}]]`
  - 自检新增写入硬约束校验项
  - 根因：审计发现 28 条 basename wikilink + 4 个个股缺代码 + 3 个 `## 来源` 残留 + 112 个 section 缺失，均因写入环节无前置约束、仅靠自检兜底（子 Agent 不执行自检）
- `references/framework-rules.md`：
  - 规则 #30 新增「原文链接格式」：表格内链接一律用 `[原文](URL)` 格式，不贴裸 URL（避免撑宽表格）

## 2026-07-21（审计修复 · v2.4.0）
- `references/framework-rules.md`：
  - 新增规则 #33（段落布局：标题前后空行、段落间空行、禁止同行标题、连续行数上限）
  - 新增规则 #34（脚注内联标记成对：禁止孤儿脚注、禁止模板废话）
- `investment-review/SKILL.md`（v2.4.0）：
  - 结构审查预扫新增 verify-format.py 段落布局扫描（与 vault_review.py 互补）
  - Relative Files 补充 verify-format.py 引用
- `investment-coarse-processor/SKILL.md`（v2.2.0）：
  - 第四步"去广告"补充 AI 整理工具固定模式（`## 全文整理` 重复转录稿、尾部积分/反馈广告、图片 embed+caption）
- `investment-refine/SKILL.md`（v2.4.1）：
  - Relative Files 补充 footnote-taxonomy.md 和模板文件依赖声明

## 2026-07-20
- `references/framework-rules.md`：
  - 规则 #31 新增「当时价格取值优先级」：成交价 > 开盘竞价位 > 发帖时实时价，禁止事后收盘价
  - 规则 #31 新增「备注只记操作理由」：盘后现象/感受不入备注
  - 规则 #32 重写为「微信/IM 截图与链接输入流程」：新增输入形式处理（连续截图合并、链接用浏览器、截图+链接组合）、博主轻创建、原文链接必填提醒、路由细化（言论追踪四子表+提炼分流）、档案更新。原独立 skill xq-screenshot-input 已删除合并入此

## 2026-07-18（v2.3.0）
- `references/framework-rules.md`：
  - 新增规则 #31（博主档案「个股买卖记录」规范：表格列/操作枚举/东方财富API实时价格/市值亿为单位）
  - 新增规则 #32（微信/IM 截图输入流程：识别博主→路由落地→买卖记录必录）
  - 规则 #30 信号子表边界更新：买卖操作不进信号表，进个股买卖记录

## 2026-07-10（v2.3.0）
- `references/framework-rules.md`：
  - 新增规则 #29（帖子集例外流程：直接从粗制品提炼→删源文件、精华去糟粕三态、灰区裁决）
  - 新增规则 #30（言论追踪 4 子表：具象化/观点/信号/互动，统一列含原文链接）
- `investment-refine/SKILL.md`（v2.4.0）：
  - 提炼改为直接执行（不再等待用户逐步确认），批量操作连续执行后统一汇报

## 2026-07-07
- `references/review-rules.md`：
  - 结构审查新增「脚注格式」维度（多余 `]]` / 格式不符 `[[target]] — 关系：说明`）
  - wikilink 有效性明确包含 frontmatter `source` 字段
  - frontmatter 完整性显式标注 `updateDate` 必填
  - 内容审查新增「已存在脚注关系复核」维度（防编撰关系）
- `references/footnote-taxonomy.md`：
  - 新增「格式校验」小节（单 `]]` 闭合、格式规范、孤儿脚注）
  - 新增「关系依据校验」小节（审查必查，无原文依据记为编撰关系，建议删除或降级）
