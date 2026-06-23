# CDP Eval 模板与注意事项

## 用户 Timeline API 采集

### API 端点

```
https://xueqiu.com/v4/statuses/user_timeline.json?user_id={xq_id}&page={page}&type=0
```

- `page` 从 1 开始，每页默认约 20 条
- `type=0` 为全部帖子（含转发），`type=1` 为原创

### 响应结构

```json
{
  "statuses": [
    {
      "id": 396197565,
      "category": 0,
      "column": "沪深",
      "data": "{...二次JSON字符串...}"
    }
  ]
}
```

> ⚠️ `data` 字段是二次 JSON 字符串，必须 `JSON.parse`。
> ⚠️ 部分条目 `data` 可能为 `null`/`undefined`，**必须在 try-catch 内解析**。

### data 内部字段

```json
{
  "id": 396197565,
  "title": "帖子标题",
  "description": "帖子正文（含 HTML 标签）",
  "user_id": 9650668145,
  "user": { "screen_name": "管我财" },
  "created_at": 1782177022000,
  "retweet_count": 14,
  "reply_count": 251,
  "like_count": 117,
  "retweeted_status": null,
  "source": "iPhone"
}
```

---

## 防御性 JS 模板（v2.1）

> 关键改进：逐条目 try-catch、null 检查、双层异常捕获

```javascript
(async () => {
  try {
    var resp = await fetch(
      'https://xueqiu.com/v4/statuses/user_timeline.json?user_id={xq_id}&page={page}&type=0'
    );
    if (!resp.ok) return JSON.stringify({error: 'HTTP ' + resp.status});
    var data = await resp.json();
    var cutoff = Date.now() - {hours} * 3600 * 1000;
    var posts = [];
    if (data.statuses) {
      data.statuses.forEach(function(s) {
        try {
          if (!s.data) return;
          if (!s.created_at || s.created_at <= cutoff) return;
          var d = JSON.parse(s.data);
          if (!d || !d.user_id) return;
          posts.push({
            user_id: d.user_id,
            status_id: d.id,
            screen_name: (d.user && d.user.screen_name) || '',
            title: d.title || '',
            text: (d.description || '').replace(/<[^>]*>/g, '').substring(0, 500),
            created_at: d.created_at,
            retweet_count: d.retweet_count || 0,
            reply_count: d.reply_count || 0,
            fav_count: d.like_count || 0,
            is_retweet: !!d.retweeted_status,
            source: d.source || ''
          });
        } catch(e) {}
      });
    }
    return JSON.stringify(posts);
  } catch(e) {
    return JSON.stringify({error: e.message || String(e)});
  }
})()
```

---

## CDP Proxy 超时配置

CDP Proxy 的 `sendCDP` 默认 30s 超时。雪球 API 对部分用户响应极慢（>120s），需启动时设置环境变量：

```bash
CDP_CMD_TIMEOUT=120000 node /path/to/cdp-proxy.mjs &
```

> batch-fetch.py v2.1+ 会在启动前自动 kill 旧 proxy 并以 `CDP_CMD_TIMEOUT` 重启。

---

## 字段映射

| API 字段 (data JSON) | 输出字段 | 类型 | 说明 |
|:---|:---|:---|:---|
| `d.user_id` | user_id | int | 雪球用户 ID |
| `d.id` | status_id | int | 帖子 ID |
| `d.user.screen_name` | screen_name | string | 博主昵称 |
| `d.title` | title | string | 帖子标题 |
| `d.description` | text | string | 正文（去 HTML，≤500 字） |
| `d.created_at` | created_at | int | Unix 毫秒时间戳 |
| `d.retweet_count` | retweet_count | int | 转发数 |
| `d.reply_count` | reply_count | int | 回复数 |
| `d.like_count` | fav_count | int | 点赞数 |
| `d.retweeted_status` | is_retweet | bool | 是否转发 |
| `d.source` | source | string | 发帖设备 |

## 登录态验证

```javascript
document.title
// 已登录: "我的首页 - 雪球"
// 未登录: "雪球 - 聪明的投资者都在这里"
```

## 为何不用 autocli

| 问题 | 详情 |
|:---|:---|
| 不登录返回空 | `autocli xueqiu feed` 无登录时返回 `[]` |
| 无法分页 | `feed` 不支持 `--page` |
| 无法指定用户 | `feed` 返回全局关注动态 |
| hot 上限 50 | `autocli xueqiu hot` 最多 50 条 |
| hot 无 user_id | 需从 URL 正则解析 |
