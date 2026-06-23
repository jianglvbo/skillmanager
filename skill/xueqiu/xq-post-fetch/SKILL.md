---
name: xq-post-fetch
description: >
  雪球博主帖子采集。输入 xq_id，通过 CDP Proxy 连接已登录 Chrome，
  调用雪球 user_timeline API 抓取帖子，输出结构化 JSON。
  支持单博主、批量、断点续采、多页、分级超时重试。
  触发词：「抓取雪球」「雪球动态」「feed fetch」「xq feed」「采集雪球」「抓取帖子」。
  区别于 blogger-refine：只采集不提炼。
  区别于 link-ingest：批量非逐链，输出 JSON 不写 Obsidian。
  排除条件：含「分析」「提炼」「画像」等加工意图。
license: MIT
agent_created: true
metadata:
  version: "2.1.0"
  short-description: 按 xq_id 通过 CDP Proxy 采集雪球帖子（重试+分页+断点续采）
compatibility: 通用
---

# 雪球博主帖子采集 v2.1

## Default Stance

### 核心原则
- **ID 驱动**：输入 xq_id，由调用方决定采集谁，不从 xq-registry 读取
- **零内部状态**：不内置博主列表，不依赖外部映射表
- **脚本优先**：用 batch-fetch.py / save-posts.py 确定性执行
- **只采不评**：不分析、不提炼，原始数据原样留存
- **CDP Proxy 优先**：复用 Chrome 登录会话绕过 WAF
- **容错优先**：逐条目 try-catch，单条异常不影响整批

### 禁止行为
- 绝不内置或硬编码博主列表
- 绝不在采集阶段分析或总结帖子内容
- 绝不使用 autocli `feed`（不登录返回空、无分页）
- 绝不直接 curl API（阿里 WAF 拦截）
- 绝不用 screen_name 作主键（user_id 唯一不变）

---

## Workflow

### 输入参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|:---|:---|:---|:---|:---|
| xq_id | int | 是 | — | 雪球用户 ID |
| xq_name | string | 否 | 用 xq_id | 博主名 |
| hours | int | 否 | 48 | 时间窗口 |
| output_dir | string | 否 | `~/.workbuddy/data/xueqiu-advisors/raw_posts/{date}/` | 输出目录 |
| retry | int | 否 | 2 | 失败重试次数 |
| max_pages | int | 否 | 3 | 每个用户最多抓取页数 |
| cmd_timeout | int | 否 | 120 | CDP 单次 eval 超时（秒） |
| resume | bool | 否 | false | 是否断点续采 |

### 第一步：启动 CDP Proxy（带超时配置）

```bash
# batch-fetch.py 会自动：kill 旧 proxy → 以 CDP_CMD_TIMEOUT 重启
python3 scripts/batch-fetch.py --ids {xq_id} --cmd-timeout 120 -o {output_dir}
```

手动模式：
```bash
CDP_CMD_TIMEOUT=120000 node {cdp-proxy-path} &
```

> 雪球 API 对部分用户响应极慢（>120s），默认 30s 超时必定失败。
> batch-fetch.py 会自动设置 `CDP_CMD_TIMEOUT` 环境变量。

### 第二步：打开雪球并验证登录

batch-fetch.py 自动处理：创建 tab → 检查标题 → 未登录提示用户。

### 第三步：调用 user_timeline API（防御性 JS）

JS 模板见 `references/cdp-templates.md`，batch-fetch 使用的独立 JS 模板见 `references/fetch-template.js`。

关键改进：
- 每条 `JSON.parse(s.data)` 包裹在独立 try-catch 内
- 检查 `s.data` 非空、`s.created_at` 在窗口内
- 双层异常捕获（fetch 层 + 逐条目层）
- JS 模板外部化，Python 占位符替换避免 f-string 嵌套

### 第四步：保存并报告

```bash
python3 scripts/save-posts.py single -i {output}.json --xq-id {id} --name {name} -o {dir}
python3 scripts/save-posts.py merge -m "raw/blogger_posts_*.json" -o {dir}
```

### 批量采集

```bash
python3 scripts/batch-fetch.py --ids 1505944393,2681290304 \
  --hours 48 --retry 2 --max-pages 3 --cmd-timeout 120 -o output/

python3 scripts/batch-fetch.py --ids-file all_ids.txt --resume -o output/
```

---

## Output Format

```json
{
  "user_id": 1505944393,
  "status_id": 396211063,
  "screen_name": "雪月霜",
  "title": "...",
  "text": "正文，HTML 已去除，≤500字...",
  "created_at": 1782177022000,
  "retweet_count": 0,
  "reply_count": 9,
  "fav_count": 3,
  "is_retweet": false,
  "source": "Android",
  "_fetched_for": "xq_id=1505944393"
}
```

| 字段 | 类型 | 来源 |
|:---|:---|:---|
| user_id | int | `d.user_id` |
| status_id | int | `d.id` |
| screen_name | string | `d.user.screen_name` |
| title | string | `d.title` |
| text | string | `d.description`（去 HTML ≤500字） |
| created_at | int | Unix 毫秒 |
| retweet_count | int | `d.retweet_count` |
| reply_count | int | `d.reply_count` |
| fav_count | int | `d.like_count` |
| is_retweet | bool | `d.retweeted_status != null` |
| source | string | `d.source` |

---

## Relative Files

| 场景 | 文件 | 内容 |
|:---|:---|:---|
| JS 模板 + 超时说明 | `references/cdp-templates.md` | 防御性 JS、API 结构、字段映射 |
| batch-fetch 使用的 JS 模板 | `references/fetch-template.js` | 独立 JS 文件，占位符替换 |
| 单条保存/合并 | `scripts/save-posts.py` | 统一 CDP 值解析 + 文件输出 |
| 批量采集（推荐） | `scripts/batch-fetch.py` | 重试 + 分页 + 断点续采 + tab 复用 |

---

## Source Hierarchy

| 优先级 | 来源 | 内容 |
|:---|:---|:---|
| 1 | 用户显式约定 | xq_id 输入、窗口、输出目录 |
| 2 | 雪球 API | user_timeline.json 结构、data 二次 JSON |
| 3 | web-access skill | CDP Proxy 连接 |
| 4 | 知识框架 pipeline | 采集 → 粗加工 → 画像更新 |
| 5 | 工程实践 | 120s 超时、退避重试、进度持久化、0.3s 间隔 |

---

## 自检

- [ ] xq_id 已传入且为数字？
- [ ] CDP Proxy 以 `CDP_CMD_TIMEOUT >= 90` 启动？
- [ ] 雪球登录态已验证？
- [ ] JS eval 中每条 `JSON.parse(s.data)` 有独立 try-catch？
- [ ] 帖子已按时间窗口过滤并写入输出文件？
- [ ] 批量模式下 `.progress.json` 已写入？
- [ ] 失败博主已记录并可重试？
