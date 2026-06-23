// 雪球 user_timeline API fetch 模板
// 占位符：__XQ_ID__、__CUTOFF_MS__、__PAGE__
// 由 Python batch-fetch.py 替换后传入 CDP eval
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
          if (!s.data) return;
          if (!s.created_at || s.created_at <= __CUTOFF_MS__) return;
          var dd = JSON.parse(s.data);
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
