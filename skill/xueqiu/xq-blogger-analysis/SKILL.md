---
name: xq-blogger-analysis
description: |
  雪球博主画像分析的完整操作手册。管理雪球博主的投资画像提炼、更新、查询和联合分析。
  当用户提到雪球博主管理、博主画像分析、博主投资观点、或需要多角度博主分析时激活。
  覆盖博主画像的粗加工、提炼、问答、迭代全流程。
  触发词：「雪球博主」「博主画像」「博主分析」「xq-blogger-analysis」「联合分析」
  「谁在聊XX」「帮我找擅长XX的博主」「{博主名}怎么看」。
version: 2.2.0
---

# 博主分析框架 · 操作手册

> 每位雪球博主一份画像文件，一个注册表索引，全局掌控。

---

## 1. 系统架构

### 流水线

博主分析框架是投资分析框架的姊妹框架，共享粗制品入口和问答看板出口，但聚焦于**博主人物画像**而非知识条目。

```
待处理链接.md → 粗制品/ →(粗加工)→ 博主分析框架/原始资源仓库/ →(提炼)→ 博主分析框架/博主画像/
                                                                            │
                                              问答看板/ ←(问答)────────────┘
                                                  │
                                                  └──(回流)──→ 博主画像/ 或 粗制品/
```

### 目录结构

```
我的知识库/                          ← vault root
├── 待处理链接.md                    ← 共享收件箱
├── 粗制品/                          ← 共享暂存区
├── 问答看板/                        ← 共享输出区
├── 仪表盘/                          ← 仪表盘文件（v2.1 起移至 vault 根目录）
├── 投资分析框架/                    ← 非本 skill 管辖
└── 博主分析框架/                    ← 本 skill 管辖范围
    ├── 原始资源仓库/
    │   ├── 帖子/
    │   ├── 长文/
    │   ├── 链接/
    │   └── 问答/
    ├── 博主画像/                    ← 45 位博主的画像文件（{nickname}.md）
    └── 索引/
        └── registry.json            ← 运营索引（博主元数据、分组、板块、日志）
```

### 与旧架构的区别

| 维度 | 旧架构（v1） | 新架构（v2） |
|------|-------------|-------------|
| 画像存储 | `~/Ai/skill/xueqiu/xq-{name}/SKILL.md`（独立 skill） | `博主分析框架/博主画像/{nickname}.md`（vault 文件） |
| 索引 | registry.json + 各 skill 独立 frontmatter | registry.json 统一索引 + 画像 frontmatter |
| 路由 | 加载对应 xq-{id} Skill | 直接读取画像文件 |
| 数据流 | 无流水线概念 | 粗制品 → 原始资源 → 博主画像 单向流水线 |

---

## 2. 博主画像模板

每位博主对应一个 `.md` 文件，存放于 `博主分析框架/博主画像/`，文件名为 `{nickname}.md`。

### Frontmatter

```yaml
---
title: 博主名
aliases: []
xq_id: ""
xq_nickname: ""
following: false
followers: null
account_age_years: null
markets: []
style_keywords: []
info_cutoff: ""
post_count: 0
status: full | skeleton
category: 博主画像          # 固定值
content_type: 人物画像       # 固定值
time_sensitivity: 中期有效   # 默认值
tags:                        # 自动生成：类型/博主画像 + 市场/XXX
  - 类型/博主画像
  - 市场/XXX
style_tags: []               # 从 style_keywords 复制
summary: ""                  # 一句话概括
sources: []                  # 关联的原始资源
queried: 0                   # 被问答引用次数
last_queried: null           # 最近查询日期
createDate: YYYY年M月D日
updateDate: YYYY年M月D日
---
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string | 博主显示名 |
| `aliases` | array | 别名列表（其他平台昵称、历史昵称） |
| `xq_id` | string | 雪球数字 ID |
| `xq_nickname` | string | 雪球当前昵称 |
| `following` | boolean | 是否已关注 |
| `followers` | number/null | 粉丝数 |
| `account_age_years` | number/null | 账号注册年数 |
| `markets` | array | 关注市场（A股、港股、美股、B股、科创板、创业板） |
| `style_keywords` | array | 投资风格关键词（5-7 个） |
| `info_cutoff` | string | 信息截止日期（YYYY-MM-DD） |
| `post_count` | number | 已分析帖子数 |
| `status` | string | `full`（完整画像）或 `skeleton`（骨架画像） |
| `category` | string | 固定值 `博主画像` |
| `content_type` | string | 固定值 `人物画像` |
| `time_sensitivity` | string | 默认 `中期有效`，画像随帖子更新 |
| `tags` | array | 自动生成：`类型/博主画像` + 每个 market 生成 `市场/{market_name}` |
| `style_tags` | array | 从 `style_keywords` 复制 |
| `summary` | string | 一句话概括博主定位 |
| `sources` | array | 关联的原始资源文件路径 |
| `queried` | number | 被问答引用次数 |
| `last_queried` | string/null | 最近查询日期 |
| `createDate` | string | 画像创建日期（YYYY年M月D日） |
| `updateDate` | string | 画像最后更新日期（YYYY年M月D日） |

### 三维分类（博主画像固定值）

博主画像使用固定的三维分类，无需手动调整：

- `category: 博主画像`（固定）
- `content_type: 人物画像`（固定）
- `time_sensitivity: 中期有效`（默认，画像随帖子更新）

### tags 生成规则

`tags` 字段由 `markets` 字段自动生成，规则如下：

- 始终包含 `类型/博主画像`
- 对 `markets` 中的每个市场，添加 `市场/{market_name}`

例如，`markets: [A股, 港股]` 会生成：

```yaml
tags:
  - 类型/博主画像
  - 市场/A股
  - 市场/港股
```

### 正文结构

```markdown
## 身份卡
（一句话定位：谁、擅长什么、投资风格概述）

## 擅长与局限
- 擅长：（具体领域、方法论优势）
- 局限：（盲区、认知偏差、不适用的场景）

## 核心投资模型
（博主的核心投资框架和方法论，每个模型独立段落）

## 决策启发式
（博主做投资决策时的经验法则和快捷判断）

## 表达DNA
（博主的语言风格、句式特征、确定性表达方式、常用词汇）

## 核心持仓与观点
（当前已知持仓、看好的标的及理由）

## 预测记录
（博主做出的投资预测，含时间、标的、方向、结果）

## 代表性语录
（最能体现博主投资思想的原始语录，标注出处和时间）

## 准确率追踪
（预测命中率统计、已验证/未验证的预测比例）

## 关联条目
（[[相关博主]]、[[相关个股]]、[[相关板块]] 等 wikilink，确保双向链接）
```

---

## 3. 流程一：粗加工

**流向**：帖子内容 → `博主分析框架/原始资源仓库/`
**触发**：用户提供雪球帖子链接或内容，或从待处理链接.md 触发

### 帖子增量抓取

从雪球 API 获取帖子正文：

1. 确定目标博主（通过 registry.json 匹配 xq_id）
2. 从雪球 API 抓取 `info_cutoff` 之后的新帖子
   - 优先使用 `autocli read` 抓取帖子正文（复用 Chrome 登录态，token 低）
   - 降级方案：浏览器自动化打开 → 提取 → 关闭
3. 每篇帖子间隔 2-3 秒，避免触发反爬

### 类型判断

| 来源 | 类型 | 存放目录 |
|------|------|----------|
| 雪球短帖 | 帖子 | `博主分析框架/原始资源仓库/帖子/` |
| 雪球长文 | 长文 | `博主分析框架/原始资源仓库/长文/` |
| 雪球问答 | 问答 | `博主分析框架/原始资源仓库/问答/` |
| 外部链接转载 | 链接 | `博主分析框架/原始资源仓库/链接/` |

### Frontmatter 填写

```yaml
---
title: 帖子标题或首句摘要
source: 来源链接
author: 博主昵称
date: YYYY年M月D日
recorded: YYYY年M月D日
type: 帖子 | 长文 | 链接 | 问答
status: 待提炼
wiki_ref: ""
tags: []
---
```

### 处理指令传播字段

粗加工阶段需要为后续提炼传递以下元数据：

| 字段 | 说明 |
|------|------|
| `_profile` | 目标博主画像文件名（如 `APEC蓝天.md`），用于提炼时路由 |
| `_alias` | 博主别名（用于匹配已有画像） |
| `_xueqiu` | 雪球 xq_id（用于精确匹配） |

这些字段写入原始资源的 frontmatter 或正文顶部注释，供提炼流程读取。

### 保留原文

- 不精简、不删节
- 逐字稿去掉时间轴格式，整理为连贯段落
- 删除尾部反馈链接
- 保留 `![[附件/图片/xxx.jpg]]` 引用
- 完成后从 `粗制品/` 移动到 `博主分析框架/原始资源仓库/{类型}/`

---

## 4. 流程二：提炼

**流向**：`博主分析框架/原始资源仓库/` → `博主分析框架/博主画像/`
**触发**：用户说"提炼"或原始资源 `status: 待提炼` 时触发

### 步骤

1. **选择资源**：扫描 `博主分析框架/原始资源仓库/` 下 `status: 待提炼` 的文件
2. **匹配画像**：通过 `_profile`、`_alias`、`_xueqiu` 字段或 author 字段匹配已有画像
   - 匹配 `博主分析框架/博主画像/` 中的文件名、frontmatter `xq_nickname`、`aliases`、`xq_id`
3. **判断操作**：新建画像 vs 更新画像
4. **提炼写入**：按博主画像模板写入对应段落
5. **更新状态**：原始资源 `status: 已提炼`，`wiki_ref` 指向画像文件
6. **更新 registry.json**：同步 `post_count`、`info_cutoff`、`stock_mentions`、`sector_mentions`

### 新建画像

当匹配不到已有画像时：

1. 在 `博主分析框架/博主画像/` 下创建 `{nickname}.md`
2. 按博主画像模板填写完整 frontmatter
3. `status: skeleton`（初始骨架）
4. 从当前资源提炼填充各段落
5. 在 registry.json 的 `bloggers` 数组中新增一条记录
6. 当提炼的资源足够丰富（覆盖 3 个以上正文段落）时，升级为 `status: full`

### 更新画像

当匹配到已有画像时：

1. **增量追加**：新洞察追加到对应段落末尾，不覆盖已有内容
2. **冲突处理**：新旧观点矛盾时，保留两者并标注时间线（「早期观点」vs「最新观点」）
3. **更新 frontmatter**：刷新 `info_cutoff`、`post_count`、`updateDate`
4. **同步 registry.json**

### 多博主提炼原则

一篇资源可能涉及多位博主（如引用、对比、讨论）：

- 主博主：创建/更新画像，完整提炼
- 提及博主：在对应画像的「代表性语录」或「核心持仓与观点」中追加引用，标注来源
- 所有涉及的画像都要在「关联条目」中互相链接

### 交叉链接

提炼完成后：

1. 画像文件的「关联条目」段落必须列出相关博主、个股、板块的 wikilink
2. 目标条目也要反向链接回来（双向链接）
3. 相关个股条目（存放在投资分析框架的维基仓库中）也应追加博主引用

---

## 5. 运营操作

运营操作通过 `博主分析框架/索引/registry.json` 作为索引驱动。所有操作修改的是 registry.json 和/或 `博主分析框架/博主画像/` 下的画像文件。

### 5.1 路由匹配

**用途**：根据用户请求找到相关博主

```
用户请求
  ↓
第一层：这是博主分析类请求吗？
  ├── 是 → 进入第二层
  └── 否 → 不触发本框架（见负样本表）
  ↓
第二层：能精确匹配到博主吗？
  ├── 用户指定了昵称/ID → registry.json 精确匹配 → 读取画像文件
  └── 用户描述了风格/板块/市场 → 按分组/风格/板块推荐 Top 3-5
  ↓
第三层：读取画像文件，基于画像内容回答问题
```

**匹配规则**：

1. **精确匹配**：用户输入的昵称/ID 在 registry.json 的 `nickname`、`xueqiu_id`、画像 `aliases` 中搜索
2. **风格匹配**：按 `style_keywords` 过滤
3. **板块匹配**：按 `sector_mentions` 排序
4. **市场匹配**：按 `markets` 过滤
5. **匹配不到** → 诚实告知「这位博主不在当前注册表中」，提示是否需要新增

### 5.2 改名检测

1. 读取 registry.json 中所有博主的 `xueqiu_id` 和当前 `nickname`
2. 访问 `https://xueqiu.com/u/{xueqiu_id}` 获取最新昵称（每次间隔 2-3 秒）
3. 比对发现不一致时：
   - registry.json 的 `name_change_log` 追加记录 `{ timestamp, old_name, new_name, xueqiu_id }`
   - 更新 registry.json 的 `nickname`
   - 重命名画像文件：`{old_nickname}.md` → `{new_nickname}.md`
   - 更新画像 frontmatter 的 `title`、`xq_nickname`、`aliases`（旧名追加到 aliases）
   - 通知用户变更详情

### 5.3 粉丝数刷新

1. 通过雪球 API 批量获取元数据：
   - 使用 `browser_cookie3` 解密 Chrome cookies 获取登录态
   - 访问 `https://xueqiu.com/user/show.json?id={id}`
   - 提取 `followers_count`、`created_at`、`status_count`、`friends_count`
   - 每次间隔 2.5 秒，每 10 个一批休息 12 秒
2. 更新 registry.json 中每位博主的 `followers_count`、`account_age_years`、`status_count`
3. 同步更新画像 frontmatter 的 `followers`、`account_age_years`
4. 输出变更摘要（涨粉 Top 5、掉粉 Top 5）

### 5.4 帖子增量抓取

1. 确定目标博主（可单个或批量）
2. 从雪球 API 抓取 `info_cutoff` 之后的新帖子
3. 新帖子先写入 `博主分析框架/原始资源仓库/`（走粗加工流程）
4. 对每篇新帖子执行提炼（走提炼流程）
5. 批量模式：按 `info_cutoff` 从旧到新排序，逐批处理

### 5.5 股票提及重算

1. 遍历 `博主分析框架/博主画像/` 下所有画像文件，用预定义股票名列表（含别名）搜索五个段落：
   - 核心持仓与观点（holdings: true/false）
   - 预测记录（predictions: 计数）
   - 代表性语录（quotes: 计数）
   - 决策启发式（heuristics: 计数）
   - 核心投资模型（models: 计数）
2. 生成新的 `stock_mentions` 映射
3. 覆盖写入 registry.json 的 `stock_mentions` 字段
4. 同时扫描板块关键词：对每位博主画像，用 `sectors` 中的 `keywords` 计数 → 写入 `sector_mentions`
5. 输出变更报告（股票/板块提及变化 Top 10）

**股票名列表**维护在 registry.json 的 `stock_aliases` 字段中，用户可要求添加/删除别名。

### 5.6 风格标签刷新

1. 遍历所有画像文件正文，用关键词列表搜索投资风格词频：
   价值投资、成长、深度价值、逆向、高股息、收息、量化、技术派、
   困境反转、长期持有、宏观、产业、消费、科技、资源、周期、
   波段、杠杆、定投、分仓、集中持股、左侧、右侧交易
2. 对每位博主，取出现频率最高的 5-7 个词作为 `style_keywords`
3. 更新 registry.json 的 `style_keywords`
4. 同步更新画像 frontmatter 的 `style_keywords`
5. 重建 registry.json `groups` 中的风格分组（type: style）
6. 输出变更（新进入/退出某分组的博主）

### 5.7 全量更新

按顺序执行：

1. 改名检测（5.2）
2. 粉丝数与账号信息刷新（5.3）
3. 帖子增量抓取（5.4）— 仅对 `info_cutoff` 超过 7 天的博主
4. 股票提及重算（5.5）
5. 风格标签刷新（5.6）
6. 输出完整更新报告

#### 更新操作速查表

| 操作 | 改画像文件 | 改 registry.json | 需要登录雪球 |
|------|:---------:|:----------------:|:-----------:|
| 改名检测 | ✓ | ✓ | ✓ |
| 粉丝数刷新 | ✓ | ✓ | ✓ |
| 帖子增量 | ✓ | ✓ | ✓ |
| 股票提及重算 | ✗ | ✓ | ✗ |
| 板块关键词扫描 | ✗ | ✓ | ✗ |
| 风格标签刷新 | ✓ | ✓ | ✗ |
| 全量更新 | ✓ | ✓ | ✓ |

### 5.8 联合分析

当用户提出一个投资话题，希望听取多位博主意见时：

```
步骤 1: 确认参与的博主（用户指定 或 根据话题匹配推荐 3-5 位）
步骤 2: 读取每位博主的画像文件，基于画像内容以该博主的视角对话题发表观点
步骤 3: 汇总所有观点，输出联合分析报告：
  - 共识区：多数博主一致认同的观点
  - 分歧点：观点明显对立的地方（标注谁 vs 谁）
  - 独特洞察：某位博主独有的、其他博主未提及的角度
  - 风险提示：各博主提到的主要风险
```

**输出格式**：
每位博主的发言用引用块包裹，标注「{昵称}说：」及权重分，保持该博主的表达 DNA（句式、词汇、确定性风格）。

### 5.9 加权推荐

当话题涉及具体股票或板块时启用。

**话题展开**：用户输入可以是股票名或板块名。
- 输入股票名（如"腾讯"）→ 直接用 `stock_mentions` 计算
- 输入板块名（如"算力"、"白酒"）→ 展开为：该板块所有关联股票 + 板块关键词。对每位博主，股票分 = 该板块下所有关联股票的 `stock_mentions` 得分之和 + `sector_mentions` 中该板块的关键词提及分

registry.json 的 `sectors` 字段定义了 16 个板块，每个板块包含：
- `stocks`: 关联股票列表（用于展开查询）
- `keywords`: 板块关键词（用于画像文件文本扫描）
- `description`: 板块描述

16 个板块：AI应用、互联网平台、医药、半导体、房地产、新能源车、有色金属、消费、煤炭/能源、电信/运营商、电力/公用事业、白酒、算力/AI算力、航运/周期、银行/金融、黄金/贵金属

**权重分公式**：

```
权重分 = 股票提及分 x 0.50 + 资历分 x 0.30 + 影响力分 x 0.20
```

**三个维度**：

1. **股票提及分（50%，最高权重）**：
   - **专注度分（60%）**：该股票/板块在该博主所有股票讨论中占比。占比越高说明越聚焦
   - **深度分（40%）**：维度覆盖数（持仓/预测/语录/启发式/模型），5 维 = 100 分

   板块查询时：将该板块下所有关联股票的 `stock_mentions` 和 `sector_mentions` 合并计算

   > 关键设计：使用相对专注度而非绝对提及数。一个只聊 3 只股票且其中 1 只是腾讯的博主，比聊 30 只股票其中提到腾讯的博主得分更高。

2. **资历分（30%）**：
   - 10 年以上：100 分
   - 5-10 年：80 分
   - 3-5 年：60 分
   - 1-3 年：40 分
   - 1 年以下：20 分
   - 未知：50 分（中间值）

3. **影响力分（20%）**：
   - 50 万+：100 分
   - 10-50 万：80 分
   - 5-10 万：60 分
   - 1-5 万：40 分
   - 1 万以下：20 分
   - 未公开：30 分

**推荐流程**：
1. 对所有 `status: full` 且 `markets` 包含该股票所在市场的博主计算权重分
2. 按权重分排序，从 Top 10 中选择 4-5 位风格差异最大的博主
3. 风格差异化判断：确保入选博主的 `style_keywords` 不完全重叠，优先选入不同投资流派
4. 展示推荐列表（含权重分明细）给用户确认后再开始

### 5.10 使用频次追踪

**记录规则**：每当用户在对话中查询某位博主的画像（通过提到博主名字、ID 等方式），在 registry.json 的 `usage_log` 数组中追加一条记录：

```json
{
  "nickname": "管我财",
  "timestamp": "2026-06-05T14:30:00",
  "action": "query",
  "topic": "港股分红策略"
}
```

action 类型：`query`（咨询观点）、`update`（更新画像）、`compare`（联合分析中被调用）

**报告功能**：当用户说「我的关注权重」或「使用统计」时，统计并展示：

- 近 7 天 / 30 天 / 全部 的博主调用排行
- 按 topic 聚合的热门话题
- 从未被调用过的博主列表（冷板凳）
- 使用频率与博主分组的交叉分析

---

## 6. registry.json 数据结构

**文件位置**：`博主分析框架/索引/registry.json`

```json
{
  "version": "2.0",
  "last_updated": "2026-06-20",
  "total_bloggers": 45,
  "stats": {
    "full_profiles": 40,
    "skeleton_profiles": 5,
    "total_posts_analyzed": 4796
  },
  "bloggers": [...],
  "groups": {...},
  "stock_aliases": {...},
  "sectors": {...},
  "usage_log": [...],
  "name_change_log": [...]
}
```

### bloggers 数组

每位博主的 blogger 对象：

| 字段 | 类型 | 说明 |
|------|------|------|
| `profile_file` | string | 画像文件名（如 `APEC蓝天.md`） |
| `xueqiu_id` | string | 雪球数字 ID |
| `nickname` | string | 当前昵称 |
| `post_count` | number | 已分析帖子数 |
| `model_count` | number | 核心投资模型数 |
| `status` | string | `full` 或 `skeleton` |
| `fan_level` | string | 粉丝量级描述 |
| `info_cutoff` | string | 信息截止日期 |
| `profile_url` | string | 雪球主页链接 |
| `markets` | array | 关注市场列表 |
| `style_keywords` | array | 投资风格关键词（5-7 个） |
| `stock_mentions` | object | 股票提及详情 `{ "股票名": { holdings, predictions, quotes, heuristics, models } }` |
| `sector_mentions` | object | 板块关键词命中 `{ "板块名": 次数 }` |
| `account_age_years` | number/null | 账号注册年数 |
| `followers_count` | number/null | 粉丝数 |
| `created_at` | string | 注册日期 |
| `status_count` | number | 发帖总数 |

### groups 对象

自动生成的分组：

- **市场分组**（type: market）：A股方向、港股达人、美股视角、B股玩家、创业板关注、科创板关注
- **风格分组**（type: style）：价值投资派、成长投资派、深度价值、逆向投资、高股息/收息、量化/技术派、困境反转、宏观视角、产业研究、消费赛道、科技赛道、资源/周期、长期持有派、趋势、波段、杠杆、分仓、集中持股、定投、左侧、右侧交易
- **状态分组**（type: status）：完整画像
- **自定义分组**（type: custom）：用户手动创建

### sectors 对象

16 个板块定义，每个包含 `stocks`（关联股票）、`keywords`（关键词）、`description`（描述）。

### 其他字段

- `stock_aliases`：股票名别名映射（含别名），用户可增删
- `usage_log`：使用频次追踪日志
- `name_change_log`：改名历史记录

每次修改 registry.json 后，更新 `last_updated` 字段为当前日期。

---

## 7. 路由层

> 所有博主相关请求**必须**经过本框架统一路由，不得跳过索引直接匹配画像文件。

### 路由流程

```
用户请求
  ↓
第一层：这是博主分析类请求吗？
  ├── 是 → 进入第二层
  └── 否 → 不触发本框架（见负样本表）
  ↓
第二层：能精确匹配到博主吗？
  ├── 用户指定了昵称/ID → registry.json 精确匹配
  └── 用户描述了风格/板块/市场 → 按分组/风格/板块推荐 Top 3-5
  ↓
第三层：读取 博主分析框架/博主画像/{nickname}.md，基于画像内容回答
```

### 路由指令（给 Agent）

1. 接收到博主相关请求时，先读取 `博主分析框架/索引/registry.json` 完成博主匹配
2. 匹配成功后，读取对应的 `博主分析框架/博主画像/{nickname}.md` 画像文件
3. 多博主场景：先在 registry.json 中完成博主组合推荐，让用户确认后逐一读取画像
4. 匹配不到博主 → 诚实告知，禁止强行匹配

### 负样本：什么时候不触发

| 场景 | 示例 | 原因 |
|------|------|------|
| 随口提到 | "我之前刷到过鹿鼎公的帖子" | 闲聊提及，不是咨询 |
| 平台讨论 | "雪球这个功能怎么用" | 讨论的是平台，不是博主观点 |
| 纯数据查询 | "雪球上茅台讨论热度怎么样" | 要的是平台数据，不是博主分析 |
| 非投资场景 | "这个博主是哪里人" | 问的是个人信息，不是投资观点 |
| 博主已锁定 | "用 APEC蓝天的框架分析茅台" | 用户已明确指定 → 直接读取画像，不需路由 |

### 博主无法匹配时

- 诚实告知「这位博主不在当前注册表中」
- 提示：「需要我抓取这位新博主的帖子并创建画像吗？」
- **禁止**：强行匹配一个不相关的博主、编造博主观点

---

## 8. 查询配方

> 以下 Dataview 查询供 AI 在执行操作时使用。通过 Obsidian MCP 的 `vault_read` 或 `search_query` 执行。

### 博主画像全量视图

```dataview
TABLE xq_nickname AS "雪球昵称", status AS "状态", markets AS "市场",
      style_keywords AS "风格", followers AS "粉丝数", post_count AS "帖子数", info_cutoff AS "信息截止"
FROM "博主分析框架/博主画像"
SORT title ASC
```

### 完整画像 vs 骨架画像

```dataview
TABLE status, post_count, info_cutoff
FROM "博主分析框架/博主画像"
WHERE status = "skeleton"
SORT title ASC
```

### 按市场过滤

> 使用 `markets` 字段过滤，不使用 `contains(tags, "市场/...")`。

```dataview
TABLE xq_nickname, style_keywords, followers
FROM "博主分析框架/博主画像"
WHERE contains(markets, "港股")
SORT followers DESC
```

多市场过滤示例：

```dataview
TABLE xq_nickname, style_keywords, markets
FROM "博主分析框架/博主画像"
WHERE contains(markets, "港股") OR contains(markets, "美股")
SORT followers DESC
```

### 待提炼队列

```dataview
TABLE date, type, author, file.folder
FROM "博主分析框架/原始资源仓库"
WHERE status = "待提炼"
SORT type ASC, date DESC
```

### 最近更新画像

```dataview
TABLE updateDate, post_count, info_cutoff
FROM "博主分析框架/博主画像"
SORT updateDate DESC
LIMIT 10
```

### 信息过期画像（超过 30 天未更新）

```dataview
TABLE info_cutoff, post_count
FROM "博主分析框架/博主画像"
WHERE date(info_cutoff) < date(today) - dur(30 days)
SORT info_cutoff ASC
```

---

## 9. 审查规则

### 审查维度

1. **画像完整性**：
   - `status: skeleton` 且 `createDate` 超过 30 天 → 长期骨架，需提醒补全
   - 正文段落缺失（如缺少「核心投资模型」或「表达DNA」） → 不完整
   - frontmatter 必填字段为空（`xq_id`、`markets`、`style_keywords`）

2. **时效性检查**：
   - `info_cutoff` 超过 90 天 → 画像可能过时
   - `updateDate` 超过 60 天 → 长期未更新
   - 「核心持仓与观点」段落中的持仓可能已变动

3. **一致性检查**：
   - 画像 frontmatter 与 registry.json 数据不一致（`post_count`、`followers`、`style_keywords`）
   - 画像文件名与 registry.json 的 `profile_file` 不匹配

4. **孤立画像检测**：
   - 画像文件的 backlinks 为空 → 无其他条目引用
   - `usage_log` 中从未被查询过的博主

5. **交叉链接检查**：
   - 「关联条目」段落为空或缺失
   - 关联的 wikilink 目标文件不存在（断链）

### 审查操作

| 类型 | 操作 |
|------|------|
| 增量审查 | 每次提炼后检查被更新的画像 |
| 全量审查 | 扫描全部画像 + registry.json 一致性 |
| 索引同步 | registry.json 与画像 frontmatter 双向校验 |

---

## 10. 常用命令速查

| 用户说 | 动作 |
|--------|------|
| 「雪球博主列表」/「博主画像列表」 | 展示全部博主的昵称、ID、状态、粉丝量 |
| 「港股达人都谁」 | 查询 groups 中港股达人分组成员 |
| 「谁擅长困境反转」 | 按 style_keywords 过滤 |
| 「检查博主改名」 | 执行改名检测流程（5.2） |
| 「刷新粉丝数」/「更新博主信息」 | 批量刷新粉丝数、注册年数（5.3） |
| 「更新 xxx 的帖子」 | 增量抓取指定博主新帖子并提炼画像（5.4） |
| 「增量更新所有博主」 | 批量增量抓取 info_cutoff 超 7 天的博主 |
| 「重算股票提及」/「刷新股票权重」 | 重新扫描画像计算 stock_mentions（5.5） |
| 「刷新风格标签」 | 重新提取 style_keywords 并重建分组（5.6） |
| 「全量更新雪球博主」/「refresh all」 | 一键执行全部更新操作（5.7） |
| 「我的关注权重」 | 输出 usage_log 统计报告 |
| 「xxx 和 yyy 怎么看 {话题}」 | 执行双博主联合分析 |
| 「帮我选几个人分析 {话题}」 | 加权推荐博主组合 + 联合分析 |
| 「谁在聊算力」/「谁在聊白酒」 | 按板块展开查询，输出博主排行 |
| 「板块热度排行」 | 展示 16 个板块的博主提及排行 |
| 「给 xxx 加标签 '核心圈'」 | 创建自定义分组 |
| 「哪些博主还没补全」 | 展示 status=skeleton 的博主 |
| 「{昵称}怎么看{股票}」 | 路由匹配 → 读取画像 → 基于画像内容分析 |
| 「{板块/风格}方向的博主推荐」 | 按分组 + 加权推荐 Top 3-5 |

---

## 11. 诚实边界

- 分组标签基于画像文件文本分析自动生成，可能不够精准，用户可手动调整
- 改名检测依赖雪球主页可访问性，如遇反爬限制会跳过并告知
- 使用追踪只记录当前 Agent 实例内的调用，跨实例不共享
- 联合分析中的「观点」是基于画像内容的推理，不代表博主本人当前实时看法
- 原始帖子数据在提炼后保留在 `博主分析框架/原始资源仓库/`，如需重新提炼可回溯
- 路由层依赖 registry.json 的数据完整性，新增博主后需同步更新分组和风格标签
- 画像内容基于已分析的帖子提炼，帖子样本量不足时画像可能不完整

---

## 12. 注意事项

- **仪表盘位置**：`仪表盘/` 目录位于 vault 根目录（`我的知识库/仪表盘/`），不在 `博主分析框架/` 下。查找或更新仪表盘文件时请使用根目录路径。
- **市场过滤**：Dataview 查询统一使用 `contains(markets, "市场名")` 过滤，不使用 `contains(tags, "市场/...")`。
- **tags 自动生成**：`tags` 字段由 `markets` 自动生成，手动修改 `markets` 后需同步刷新 `tags`。
