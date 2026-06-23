# 雪球数据管道

> 本文档是 `blogger-refine` 的按需引用。仅当 config_snapshot.is_xueqiu = "是" 时才加载。
> 职责：从雪球平台获取博主元数据，注入画像 frontmatter。不参与内容提炼。

---

## 触发条件

pipeline 调用 blogger-refine 时，若 `is_xueqiu = 是`，加载本文件。

---

## 数据获取

### 1. 获取 xq_id 和基本信息

已有 xq_id（画像 frontmatter 中存在且 > 0）→ 跳过此步，直接进入第 2 步。

无 xq_id → 从以下来源获取：

| 来源 | 方法 |
|:---|:---|
| 原始资源 frontmatter | source 字段若为 `xueqiu.com/数字ID/帖子ID` 格式，提取数字 ID |
| autocli 搜索 | `autocli xueqiu search "{博主名}"` 查找博主主页 |
| 已知映射 | 控制台可能记录过历史 ID |

### 2. 获取粉丝数和近期帖子

使用 autocli：

```bash
autocli xueqiu feed --user {xq_id} --page 1 --limit 20 --format json
```

解析输出：
- `followers_count` → 写入画像 frontmatter `followers`
- 帖子列表 → 提取标题、时间、正文摘要
- 按时间倒序排列，取最近 5 篇存入画像

### 3. 帖子数聚合

```bash
autocli xueqiu feed --user {xq_id} --page 1 --limit 50 --format json | jq '.total_count'
```

> 注意：帖子数仅作参考，不做为画像质量权重。画像质量由 `score` 字段独立计算。

---

## Frontmatter 注入

获取雪球数据后，更新画像 frontmatter 以下字段：

| 字段 | 来源 | 示例 |
|:---|:---|:---|
| `xq_id` | 雪球用户数字 ID | 1107378837 |
| `xq_nickname` | 雪球当前昵称 | 重组专家 |
| `followers` | 粉丝数 | 44420 |
| `account_age_years` | 注册时长（年） | 8.3 |

---

## 帖子内容提取

从 autocli 输出中解析帖子 JSON，按以下模板追加到画像：

```markdown
## {YYYY年M月D日} 更新

当日采集 {N} 条帖子（原创{X}条，转发{Y}条）。

提及股票：{标的1}({代码})（{次数}次）

### 原创观点
- {帖子摘要}

### 提及标的
{标的列表}

> 信息截止日期更新至 {日期}
```

### 帖子 JSON 解析要点

| JSON 字段 | 用途 |
|:---|:---|
| `title` | 帖子标题（可能为空，雪球允许无标题帖） |
| `text` | 帖子正文（截取前 200 字） |
| `created_at` | 发布时间（Unix 时间戳 → YYYY年M月D日） |
| `retweeted_status` | 存在 = 转发，不存在 = 原创 |
| `view_count` | 阅读量（可选） |

---

## 与 blogger-refine 的分工边界

| 职责 | blogger-refine | xueqiu-data-pipeline |
|:---|:---|:---|
| 阅读文章内容 | ✅ | — |
| 提炼观点/风格 | ✅ | — |
| 写 summary/sources/score | ✅ | — |
| 获取 xq_id / followers | — | ✅ |
| 拉取近期帖子 | — | ✅ |
| 生成帖子摘要 | — | ✅ |
| 评分计算 | ✅ | — |
| 评分验证（对比帖子数） | — | ✅ 只做对比参考 |
