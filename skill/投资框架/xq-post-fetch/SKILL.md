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
  version: 4.0.1
  short-description: 通过 browser-act chrome 模式采集雪球博主帖子全文
compatibility: 通用
disable: true
---

# 雪球帖子采集 v4.0

## Default Stance

### 核心原则
- **browser-act 唯一**：只通过 browser-act CLI（chrome 模式）采集，复用 Chrome 登录态绕过阿里云 WAF。
- **全文优先**：自动检测截断内容，导航到详情页获取完整正文。
- **容错优先**：单帖失败不影响整批；置顶帖标注原始日期，不纳入时间窗口统计。
- **独立可用**：用户直接输入参数即可运行，不依赖 pipeline。

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
- 解析输出，确认可用浏览器

**第三步**：打开浏览器，导航到雪球用户页
```bash
browser-act --session xq browser open xq "https://xueqiu.com/u/{xq_id}"
```
- 验证登录态：调用 `browser-act --session xq state`，检查页面标题
  - 已登录：标题含用户昵称
  - 未登录：**停止，提示用户在 Chrome 中登录雪球**

**第四步**：提取帖子列表
1. 调用 `browser-act --session xq get markdown` 获取用户页正文
2. 从 markdown 中解析帖子列表：标题、摘要、时间、互动数据
3. **识别置顶帖**：标注「📌 置顶」+ 原始发布日期，不纳入时间窗口统计
4. 按时间过滤：仅保留 hours 小时内的帖子
5. 数量限制：不超过 max_posts 条

**第五步**：截断内容补全
1. 检查每条帖子的 markdown 是否含截断标记（`展开`、末尾 `...`、内容明显不完整）
2. 截断的长文 → 导航到详情页获取全文：
   ```bash
   browser-act --session xq navigate "https://xueqiu.com/{xq_id}/{post_id}"
   browser-act --session xq get markdown
   ```
3. 回复类短帖 → 保留摘要即可
4. 补全后标记：「✅ 全文」vs「⚠️ 摘要」

**第六步**：关闭浏览器
```bash
browser-act --session xq browser delete xq
```
- 需用户确认（browser-act 安全规则）；若会话复用中则不关闭

**第七步**：写入输出文件
- 位置：`{output_dir}/雪球采集-{nickname}-{YYYY年M月D日}.md`
- 格式：见 Output Format
- 向用户报告摘要：采集 N 条帖子，时间范围 X ~ Y，其中 M 条补全了全文

---

## Output Format

输出为 markdown 文件，兼容粗加工（coarse-processor）输入格式：

```markdown
---
title: "雪球帖子采集：{nickname} {YYYY年M月D日}"
source: "https://xueqiu.com/u/{xq_id}"
author: "{nickname}"
date: "{YYYY年M月D日}"
type: "帖子集"
status: "待粗加工"
tags: []
---

## 1. {帖子标题}

{正文全文}

> 📊 发布：{YYYY年M月D日 HH:MM} | 转发 {n} | 回复 {n} | 点赞 {n} | ✅ 全文

---

## 2. {帖子标题}

{正文全文}

> 📊 发布：{YYYY年M月D日 HH:MM} | 转发 {n} | 回复 {n} | 点赞 {n} | ⚠️ 摘要
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

---

## Relative Files

| 场景 | 加载文件 | 内容 |
|:---|:---|:---|
| 始终 | browser-act SKILL.md | browser-act 命令参考和工作流 |
| 始终 | `browser-act get-skills core` 输出 | 运行时环境状态和操作指令 |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式参数（xq_id、hours、max_posts） |
| 2 | browser-act CLI（chrome 模式页面数据） |
| 3 | 雪球页面结构（DOM / markdown 提取） |

---

## 自检

- [ ] xq_id 已传入且为数字？
- [ ] browser-act CLI 可用（`--version` 返回版本号）？
- [ ] `get-skills core` 已执行，环境状态已确认？
- [ ] Chrome 浏览器运行中 + 雪球已登录？
- [ ] 置顶帖已标注原始日期，未纳入时间窗口统计？
- [ ] 截断长文已导航到详情页补全全文？
- [ ] 输出文件 frontmatter 完整（title/source/author/date/type/status/tags）？
