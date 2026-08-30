#!/usr/bin/env python3
"""雪球用户页采集器（2026-08-15 实战验证，40 位博主 382 条零风控触发）

采集路径：用户页滚动加载（列表+正文）→ 详情页补全截断长文（全文验证）
避开：timeline API 翻页（WAF 拦截裸 URL）、show.json 连续请求（滑块验证）

用法: python3 xq_user_collect.py <xq_id> <nickname> <cutoff> <outfile>
  xq_id    雪球用户 ID
  nickname 博主名（用于输出文件名）
  cutoff   信息截止 ISO 时间（YYYY-MM-DDTHH:mm:ss），只采此后的帖子
  outfile  输出帖子集 markdown 路径

依赖：browser-act CLI（session 名为 xq2，可在脚本顶部 SESSION 变量修改）
"""
"""雪球用户页采集：导航用户页 → 滚动加载 → 解析帖子 → 详情页补全截断 → 输出帖子集
用法: python3 xq_collect.py <xqid> <nickname> <cutoff> <outfile>
"""
import re, sys, os, datetime, subprocess, json

XQID, NICK, CUTOFF_S, OUTFILE = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
SESSION = 'xq2'
BA = '/Users/jianglb/.local/bin/browser-act'
cutoff = datetime.datetime.strptime(CUTOFF_S, '%Y-%m-%dT%H:%M:%S') if CUTOFF_S else None

def run(cmd):
    r = subprocess.run([BA, '--session', SESSION] + cmd, capture_output=True, text=True, timeout=60)
    return r.stdout

def get_md():
    return run(['get', 'markdown'])

def parse_posts(md):
    """解析用户页 markdown 中的帖子块（时间戳行前可能有作者名前缀）"""
    posts = {}
    lines = md.split('\n')
    # 时间戳模式：任意位置 [时间· 来自设备](https://xueqiu.com/{xqid}/{postid})
    ts_pattern = re.compile(r'\[([^\]]*· 来自[^\]]*)\]\(https://xueqiu.com/' + XQID + r'/(\d+)\)')
    for i, line in enumerate(lines):
        m = ts_pattern.search(line)
        if not m:
            continue
        time_text, pid = m.group(1), m.group(2)
        if pid in posts:
            continue
        # 收集正文直到互动行
        body_lines = []
        j = i + 1
        while j < len(lines):
            if '转发' in lines[j] or lines[j].strip().startswith('[*'):
                break
            body_lines.append(lines[j])
            j += 1
        body = '\n'.join(body_lines).strip()
        posts[pid] = {'time_text': time_text, 'body': body, 'truncated': '[展开]' in body or '展开' in body}
    return posts

def scroll_load(max_scrolls=15):
    """导航用户页 + 滚动加载直到帖子数不再增加"""
    run(['navigate', f'https://xueqiu.com/u/{XQID}'])
    subprocess.run(['sleep', '4'])
    all_posts = {}
    for s in range(max_scrolls):
        md = get_md()
        posts = parse_posts(md)
        if len(posts) > len(all_posts):
            all_posts = posts
        else:
            break
        run(['scroll', 'down', '--amount', '2500'])
        subprocess.run(['sleep', '2'])
    return all_posts

def fetch_detail(pid):
    """详情页获取完整正文"""
    run(['navigate', f'https://xueqiu.com/{XQID}/{pid}'])
    subprocess.run(['sleep', '2.5'])
    md = get_md()
    m = re.search(r'来源：雪球App.*?\n(.*?)\n风险提示', md, re.S)
    if m:
        return m.group(1).strip(), False
    return '', True

# 主流程
posts = scroll_load()
print(f'用户页共解析 {len(posts)} 条帖子', file=sys.stderr)

# 时间转换：解析 MM-DD HH:MM 或 昨天 或 N小时前
now = datetime.datetime.now()
def parse_time(t):
    t = t.replace('修改于', '').strip()
    # 完整日期：YYYY-MM-DD HH:MM（置顶帖/专栏帖）
    m = re.match(r'(\d{4})-(\d{2})-(\d{2}) (\d+):(\d+)', t)
    if m:
        return datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
    if '昨天' in t:
        d = (now - datetime.timedelta(days=1))
        m = re.search(r'(\d+):(\d+)', t)
        if m:
            return d.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0)
        return d
    m = re.match(r'(\d{2})-(\d{2}) (\d+):(\d+)', t)
    if m:
        return datetime.datetime(now.year, int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))
    m = re.match(r'(\d+)小时前', t)
    if m:
        return now - datetime.timedelta(hours=int(m.group(1)))
    m = re.match(r'(\d+)分钟前', t)
    if m:
        return now - datetime.timedelta(minutes=int(m.group(1)))
    return now

# 过滤 cutoff 后 + 非置顶（时间在合理范围）
new_posts = []
for pid, p in posts.items():
    t = parse_time(p['time_text'])
    if cutoff and t <= cutoff:
        continue
    # 置顶帖：时间远早于窗口且带置顶标记
    if '置顶' in p['time_text']:
        continue
    p['dt'] = t
    new_posts.append((pid, p))

new_posts.sort(key=lambda x: x[1]['dt'], reverse=True)
print(f'cutoff 后 {len(new_posts)} 条', file=sys.stderr)

# 详情页补全截断帖
results = []
for pid, p in new_posts:
    if p['truncated'] or p['body'] == '':
        full, failed = fetch_detail(pid)
        if not failed and full:
            p['body'] = full
            p['completeness'] = '全文'
        else:
            p['completeness'] = '摘要'
    else:
        p['completeness'] = '全文'
    results.append((pid, p))

# 生成输出
date_str = '2026年8月15日'
lines = ['---', f'title: "雪球帖子采集：{NICK} {date_str}"', f'source: "https://xueqiu.com/u/{XQID}"',
         f'author: "{NICK}"', f'date: "{date_str}"', f'recorded: "{date_str}"', 'type: "帖子集"',
         'status: "待提炼"', 'tags: []', '---', '']
for i, (pid, p) in enumerate(results, 1):
    # 标题：正文首句
    body = p['body']
    title = ''
    m = re.match(r'^([^。！？!?\n]+[。！？!?])', body)
    if m:
        title = m.group(1)
    else:
        title = body[:30]
    lines += [f'## {i}. {title}', '', body, '',
              f'> 发布：{p["dt"].strftime("%Y年%m月%d日 %H:%M")} | {p["completeness"]} | [原文](https://xueqiu.com/{XQID}/{pid})', '', '---', '']

with open(OUTFILE, 'w') as f:
    f.write('\n'.join(lines))
print(f'✅ {NICK}: {len(results)} 条 → {os.path.basename(OUTFILE)}')
