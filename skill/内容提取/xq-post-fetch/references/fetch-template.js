// 雪球 user_timeline API fetch 模板
// 占位符：__XQ_ID__、__CUTOFF_MS__、__PAGE__
// 由 Python batch-fetch.py 替换后传入 CDP eval
// v2.3: 置顶帖用 type==="2" 识别（API 无 isTop 字段），跳过置顶帖再判断时间边界
(async () => {
  try {
    var r = await fetch(
      'https://xueqiu.com/v4/statuses/user_timeline.json?user_id=__XQ_ID__&page=__PAGE__&type=0'
    );
    if (!r.ok) return JSON.stringify({error: 'HTTP ' + r.status});
    var d = await r.json();
    var posts = [];
    if (d.statuses) {
      d.statuses.forEach(function (s) {
        try {
          // 跳过置顶帖：API 无 isTop 字段，置顶帖 type==="2"（或 mark===1）
          if (String(s.type) === '2') return;
          if (!s.created_at || s.created_at <= __CUTOFF_MS__) return;
          // 兼容新旧 API 结构：新结构字段直接内联在 s 上，旧结构在 s.data (JSON 字符串) 中
          var dd;
          if (s.user_id) {
            dd = s;
          } else if (s.data) {
            dd = JSON.parse(s.data);
          } else {
            return;
          }
          if (!dd || !dd.user_id) return;
          posts.push({
            user_id: dd.user_id,
            status_id: dd.id,
            screen_name: (dd.user || {}).screen_name || '',
            title: dd.title || '',
            text: (dd.description || '').replace(/<[^>]*>/g, '').substring(0, 500),
            created_at: dd.created_at,
            retweet_count: dd.retweet_count || 0,
            reply_count: dd.reply_count || 0,
            fav_count: dd.like_count || 0,
            is_retweet: !!dd.retweeted_status,
            source: dd.source || ''
          });
        } catch (e) {}
      });
    }
    return JSON.stringify(posts);
  } catch (e) {
    return JSON.stringify({error: e.message || String(e)});
  }
})()
