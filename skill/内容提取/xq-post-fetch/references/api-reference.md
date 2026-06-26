# API 参考

## 端点

```
GET https://xueqiu.com/v4/statuses/user_timeline.json?user_id={xq_id}&page={page}&type=0
```

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| user_id | int | 雪球用户 ID |
| page | int | 页码，从 1 开始 |
| type | int | 0=全部（含转发），1=原创 |
| count | int | 每页条数（默认 ~20，一般不需要设置） |

## 响应结构

```json
{
  "statuses": [
    {
      "id": 396224484,
      "isTop": true,
      "created_at": 1782228786000,
      "text": "<p>正文 HTML</p>",
      "description": "正文 HTML（可能不存在）",
      "data": "{...二次JSON字符串...}",
      "user_id": 9650668145,
      "user": { "screen_name": "管我财", "id": 9650668145 },
      "retweet_count": 13,
      "reply_count": 136,
      "like_count": 490,
      "retweeted_status": null,
      "source": "iPhone"
    }
  ]
}
```

> ⚠️ **双格式响应**：部分情况下帖子数据在 `s.data`（JSON 字符串，需 `JSON.parse`），
> 部分情况下直接在 `s` 的顶层字段。JS 模板已兼容两种格式。

> ⚠️ **置顶帖**：`isTop === true` 的帖子可能是几年前的，不参与时间边界判断。
> 翻页时必须先过滤掉置顶帖，再用非置顶帖的最旧时间判断是否停止。

## 字段映射

### 直接字段格式

| API 字段 | 输出字段 | 类型 | 说明 |
|:---|:---|:---|:---|
| `d.user_id` | user_id | int | 雪球用户 ID |
| `d.id` | status_id | int | 帖子 ID |
| `d.user.screen_name` | screen_name | string | 博主昵称 |
| `d.title` | title | string | 帖子标题（可能为空） |
| `d.description` 或 `d.text` | text | string | 正文（去 HTML，≤500 字） |
| `d.created_at` | created_at | int | Unix 毫秒时间戳 |
| `d.retweet_count` | retweet_count | int | 转发数 |
| `d.reply_count` | reply_count | int | 回复数 |
| `d.like_count` | like_count | int | 点赞数 |
| `d.retweeted_status` | is_retweet | bool | 非 null 表示转发帖 |
| `d.source` | source | string | 发帖设备 |

### data JSON 字符串格式

当 `s.data` 存在且为字符串时，`JSON.parse(s.data)` 后得到与上述相同的字段结构。
正文字段在 data 格式中通常为 `description`，在直接格式中可能为 `text` 或 `description`。

## 登录态验证

```javascript
document.title
// 已登录: "管我财 - 雪球" 或 "我的首页 - 雪球"
// 未登录: "雪球 - 聪明的投资者都在这里"
```

## 反爬机制

雪球使用阿里云 WAF（Web Application Firewall）。直接用 `requests` / `curl` 访问首页会返回 JS 挑战页面（HTML 而非正常响应），后续 API 调用也会被拦截。

**解决方案**：在已登录的 Chrome 浏览器上下文中通过 `fetch()` 调用 API，自动携带有效 Cookie，完全绕过 WAF。

## 已知限制

| 限制 | 说明 | 应对 |
|:---|:---|:---|
| 回复帖不稳定 | `user_timeline` 对回复帖（「回复@…」）的返回不一致，有时出现在后续页，有时完全不返回 | 如需完整回复，考虑补充调用回复专用端点 [待验证] |
| 远古帖混入首页 | API 偶尔在 page 1 返回多年前的帖子，且不标记 `isTop` | JS 模板已处理：比 cutoff 早 >1 年的帖子不参与时间边界判断 |
| 响应格式不固定 | 部分情况下帖子数据在 `s.data`（JSON 字符串），部分直接在顶层字段 | JS 模板已兼容双格式 |

## 为何不用 autocli

| 问题 | 详情 |
|:---|:---|
| 不登录返回空 | `autocli xueqiu feed` 无登录时返回 `[]` |
| 无法分页 | `feed` 不支持 `--page` |
| 无法指定用户 | `feed` 返回全局关注动态，不能按 user_id 过滤 |
| hot 上限 50 | `autocli xueqiu hot` 最多 50 条 |
| hot 无 user_id | 需从 URL 正则解析，不可靠 |
