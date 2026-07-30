---
name: xq-post-fetch
description: |
  雪球帖子采集。通过 browser-act CLI（chrome 模式）采集指定博主的帖子全文，
  自动检测截断并补全长文，输出结构化 markdown 文件。
  触发词：「抓取雪球」「雪球帖子」「采集雪球」「xq fetch」「雪球动态」
  排除条件：含「分析」「提炼」「画像」等关键词时交给 blogger-refine / wiki-refine。
  依赖条件：browser-act CLI 已安装 + Chrome 浏览器运行中 + 雪球已登录。
  区别于 browser-act：xq-post-fetch 是雪球专用采集引擎，browser-act 是通用浏览器自动化。
metadata:
  version: "4.1.2"
  short-description: 通过 browser-act chrome 模式采集雪球博主帖子全文
compatibility: 通用
---

# 雪球帖子采集 v4.1

## Default Stance

### 核心原则
- **browser-act 唯一**：只通过 browser-act CLI（chrome 模式）采集，复用 Chrome 登录态绕过阿里云 WAF。
- **全文优先**：自动检测截断内容，导航到详情页获取完整正文。
- **容错优先**：单帖失败不影响整批；置顶帖标注原始日期，不纳入时间窗口统计。
- **独立可用**：用户直接输入参数即可运行，不依赖 pipeline。
- **确定性优先**：帖子解析按 `references/page-structure.md` 的 pattern 执行，不靠自由发挥。

### 禁止行为
- 绝不内置或硬编码博主列表
- 绝不直接 curl / requests 调 API（阿里云 WAF 拦截）
- 绝不在采集阶段分析或总结帖子内容
- 绝不跳过截断检测（长文必须补全全文）
- 绝不将置顶帖归入「今日」时间范围

---

## Workflow

### 输入参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|:---|:---|:---|:---|:---|
| xq_id | int | 是 | — | 雪球用户 ID |
| hours | int | 否 | 48 | 时间窗口（小时） |
| max_posts | int | 否 | 20 | 最大采集条数 |
| output_dir | path | 否 | 粗制品目录 | 输出目录 |

**第一步**：检查 browser-act CLI
```bash
browser-act --version
```
- 不可用 → 报错停止，提示 `uv tool install browser-act-cli --python 3.12`

**第二步**：加载 browser-act 运行指令
```bash
browser-act get-skills core --skill-version 2.0.2
```
- **禁止跳过**——返回环境状态、可用浏览器列表、操作指令
- 解析输出，确认可用浏览器 ID 和已有 session

**第三步**：打开浏览器，导航到雪球用户页

**会话管理**（按顺序判断）：
1. `browser-act session list` 查看活跃会话
2. 扫描**本对话的工具调用历史**：是否已执行过 `browser open --session <name>`？
   - 是 → 该 session 是我的，直接 `navigate` 到目标 URL
   - 否 → 该 session 不是我的，**不要操作它**
3. 没有我的 session → 用 `browser-act --session xq browser open {browser_id} "https://xueqiu.com/u/{xq_id}"` 创建新 session
4. 有我的 session → 直接 `browser-act --session {name} navigate "https://xueqiu.com/u/{xq_id}"`

**验证登录态**：
- `browser-act --session {name} get title`
- 标题含用户昵称 → 已登录
- 标题不含昵称或含「登录」→ **停止，提示用户在 Chrome 中登录雪球**

**第四步**：获取当前时间 + 提取帖子列表

1. 获取基准时间：`date "+%Y-%m-%d %H:%M"`
2. 调用 `browser-act --session {name} wait stable` 等待页面加载
3. 调用 `browser-act --session {name} get markdown` 获取用户页正文
4. **加载 `references/page-structure.md`**，按其规则解析：
   - 识别帖子区域边界（过滤导航栏、profile、推荐、页脚等噪声）
   - 从每个帖子块提取：post_id（从 `xueqiu.com/{xq_id}/(\d+)` 正则）、时间、正文、互动数据
   - 时间格式转换（`N小时前`、`昨天 HH:MM`、`MM-DD HH:MM` → 绝对时间，详见 references）
5. **识别置顶帖**：标注「📌 置顶」+ 原始发布日期，不纳入时间窗口统计
6. 按时间过滤：仅保留 hours 小时内的帖子
7. 数量限制：不超过 max_posts 条

**滚动加载更多**：
- 如果首屏帖子数 < max_posts 且最旧帖子仍在时间窗口内 → 需要滚动加载：
  ```bash
  browser-act --session {name} scroll down --amount 2000
  browser-act --session {name} wait stable
  browser-act --session {name} get markdown
  ```
- 重新解析 markdown，合并新帖子（按 post_id 去重）
- 重复直到帖子数 ≥ max_posts 或最旧帖子超出时间窗口

**第五步**：截断内容补全

对每条帖子执行截断检测（规则见 `references/page-structure.md` 截断检测章节）：

1. 有 `[展开]()` → **确定截断**，导航详情页补全
2. 无 `[展开]()` 但正文不完整 → 导航详情页确认
3. 正文完整 → 保留

补全流程：
```bash
browser-act --session {name} navigate "https://xueqiu.com/{xq_id}/{post_id}"
browser-act --session {name} wait stable
browser-act --session {name} get markdown
```
- 从详情页提取完整正文（正文在 `来源：雪球App` 和 `风险提示` 之间）
- 详情页同时提供精确发布时间（`发布于 YYYY-MM-DD HH:MM`），覆盖用户页的模糊时间
- 补全后标记：「✅ 全文」vs「⚠️ 摘要」

**引用内容处理**：帖子中的引用块（`>` 前缀）保留，区分作者原文和引用原文（详见 references）。

**Emoji 清洗**：雪球表情图片 `![表情](url)` 替换为 `[表情]` 或删除（详见 references）。

**第六步**：关闭浏览器
```bash
browser-act session close {name}
```
- 采集完成后关闭 session 释放资源
- 若后续还需复用（如连续采集多个博主）→ 不关闭，提示用户

**第七步**：写入输出文件
- 位置：`{output_dir}/雪球采集-{nickname}-{YYYY年M月D日}.md`
- 格式：见 Output Format
- 向用户报告摘要：采集 N 条帖子，时间范围 X ~ Y，其中 M 条补全了全文

**第八步**：更新博主画像 info_cutoff

如果 vault 中存在该博主的画像文件（`博主/{nickname}/{nickname}.md`）：
1. 更新 `info_cutoff` 为当前日期
2. 更新 `updateDate` 为当前日期
3. 不修改画像的其他内容（分析/提炼由后续环节负责）

如果博主文件夹不存在 → 跳过此步，不自动创建

**采集完成即结束**：本 skill 仅负责采集。产出的帖子集按 `framework-rules.md` #29 例外流程，由 investment-refine **直接执行**提炼（不进原始资源、不需用户确认、提炼后源文件移废纸篓）。精华去糟粕判定清单见 `references/refine-checklist.md`（由 investment-refine 加载）。采集阶段不分析内容（遵守本 skill 禁止行为）。

> **`[原文]` 链接是画像表原文链接的唯一权威来源**：每帖输出均带 `[原文](https://xueqiu.com/{xq_id}/{post_id})`（见 Output Format），采集阶段须确保**每帖都带 `[原文]` 链接、不得丢弃**——后续提炼填充博主画像三表「原文链接」列（言论追踪/个股买卖/预测，见 framework-rules #35）一律取自此链接，禁止填采集批次名、禁止留空。

---

## Output Format

输出为 markdown 文件（帖子集按 #29 例外流程直接进提炼，不经粗加工）：

```markdown
---
title: "雪球帖子采集：{nickname} {YYYY年M月D日}"
source: "https://xueqiu.com/u/{xq_id}"
author: "{nickname}"
date: "{YYYY年M月D日}"
recorded: "{YYYY年M月D日}"
type: "帖子集"
status: "待提炼"
tags: []
---

## 1. {帖子标题}

{正文全文}

> 📊 发布：{YYYY年M月D日 HH:MM} | 转发 {n} | 回复 {n} | 点赞 {n} | ✅ 全文 | [原文](https://xueqiu.com/{xq_id}/{post_id})

---

## 2. {帖子标题}

{正文全文}

> 📊 发布：{YYYY年M月D日 HH:MM} | 转发 {n} | 回复 {n} | 点赞 {n} | ⚠️ 摘要 | [原文](https://xueqiu.com/{xq_id}/{post_id})
```

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| title | string | 帖子标题（无标题时用首句前 20 字） |
| text | string | 正文全文（截断帖补全后标记） |
| created_at | string | 发布时间（YYYY年M月D日 HH:MM） |
| retweet_count | int | 转发数 |
| reply_count | int | 回复数 |
| like_count | int | 点赞数 |
| is_pinned | bool | 是否置顶（📌 标记） |
| completeness | string | ✅ 全文 / ⚠️ 摘要 |
| post_url | string | 帖子原文链接（`https://xueqiu.com/{xq_id}/{post_id}`） |

---

## Relative Files

| 场景 | 加载文件 | 内容 |
|:---|:---|:---|
| 第四步解析帖子 | `references/page-structure.md` | 帖子 markdown 结构、post_id 提取、时间格式转换、互动数据解析、截断检测、引用内容处理、emoji 清洗 |
| 采集后提炼帖子集 | `references/refine-checklist.md` | 精华去糟粕价值流水线、灰区裁决、言论追踪 4 类落位、丢弃确认清单（framework-rules #29 例外，由 investment-refine 加载） |
| 始终 | browser-act SKILL.md | browser-act 命令参考和工作流 |
| 始终 | `browser-act get-skills core` 输出 | 运行时环境状态和操作指令 |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式参数（xq_id、hours、max_posts） |
| 2 | browser-act CLI（chrome 模式页面数据） |
| 3 | 雪球页面结构（`references/page-structure.md` 中的解析规则） |
| 4 | browser-act 通用文档 |

---

## 自检

- [ ] xq_id 已传入且为数字？
- [ ] browser-act CLI 可用（`--version` 返回版本号）？
- [ ] `get-skills core` 已执行，环境状态和浏览器列表已确认？
- [ ] session 归属已判断（本对话历史中有无 `browser open --session` 调用）？
- [ ] 雪球已登录（页面标题含用户昵称）？
- [ ] `references/page-structure.md` 已加载用于帖子解析？
- [ ] 当前时间已获取（`date` 命令），用于 48h 窗口计算？
- [ ] 置顶帖已标注原始日期，未纳入时间窗口统计？
- [ ] 截断长文（含 `[展开]()`）已导航到详情页补全全文？
- [ ] 输出文件 frontmatter 完整（title/source/author/date/recorded/type/status）？
- [ ] 博主画像 info_cutoff 已更新（如画像文件存在）？
