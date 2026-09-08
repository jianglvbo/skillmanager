#!/usr/bin/env python3
"""雪球用户页采集器 v2.1（2026-09-08 恢复 v2 基线并补形态字段）

采集路径：用户页滚动加载（列表+正文）→ 详情页补全截断长文 + 精确发布时间
避开：timeline API 翻页（WAF 拦截裸 URL）、show.json 连续请求（滑块验证）

v2 改进（2026-08-18 批量 42 位实战后落地）：
1. 「修改于」时间戳处理：用户页时间可能是"最后修改时间"而非发布时间——
   对「修改于」帖进详情页取「发布于」时间做窗口判定；详情页也无法确认发布时间的
   「修改于」帖（可能为旧帖被改）→ 跳过，防止误把旧帖当新帖采入
2. 详情页同时提取精确「发布于 YYYY-MM-DD HH:MM」，覆盖用户页模糊时间
3. 0 帖（cutoff 后无新帖）→ 不生成输出文件，仅报告（不再留空粗制品）
4. 自动创建/复用 session 并校验登录态（user/show.json），未登录即报错停止
5. 采集完成自动双写 info_cutoff（画像 + 控制台，复用 xq_update_cutoff.py 逻辑）
6. 滑块页检测：详情页若返回「滑动验证」页面 → 标记为摘要而非全文，不盲重试

用法: python3 xq_user_collect.py <xq_id> <nickname> <cutoff> <outfile> [--no-cutoff]
  xq_id      雪球用户 ID
  nickname   博主名（用于输出文件名与 info_cutoff 双写）
  cutoff     信息截止 ISO 时间（YYYY-MM-DDTHH:mm:ss），只采此后的帖子
  outfile    输出帖子集 markdown 路径；0 帖时不生成
  --no-cutoff  不自动双写 info_cutoff（批量调度时由调度器统一处理）

依赖：browser-act CLI（自动探测 ~/.local/bin/browser-act 或 PATH）
"""
import re, sys, os, datetime, subprocess, time

def find_ba():
    """定位 browser-act CLI：优先 ~/.local/bin，其次 PATH"""
    cands = [os.path.expanduser('~/.local/bin/browser-act'), 'browser-act']
    for c in cands:
        r = subprocess.run(['which', c], capture_output=True, text=True) if '/' not in c else None
        if '/' in c and os.path.exists(c):
            return c
        if r and r.returncode == 0:
            return r.stdout.strip()
    sys.exit('❌ browser-act CLI 未找到，请安装：uv tool install browser-act-cli --python 3.12')

BA = find_ba()
SESSION = f'xq_{os.getpid()}'  # 独立 session，避免与他人会话争用

# ---- 参数 ----
args = [a for a in sys.argv[1:] if not a.startswith('--')]
XQID, NICK, CUTOFF_S, OUTFILE = args[0], args[1], args[2], args[3]
DO_CUTOFF = '--no-cutoff' not in sys.argv
cutoff = datetime.datetime.strptime(CUTOFF_S, '%Y-%m-%dT%H:%M:%S') if CUTOFF_S else None

def run(cmd, timeout=45):
    r = subprocess.run([BA, '--session', SESSION] + cmd, capture_output=True, text=True, timeout=timeout)
    return r.stdout

def get_md():
    return run(['get', 'markdown'])

# ---- session 与登录 ----
def ensure_session():
    """创建 session 并校验登录态；失败给出人工指引"""
    browsers = run(['browser', 'list'])
    m = re.search(r'id=(\S+?)\s+name="([^"]+)"\s+type=(\S+)', browsers)
    if not m:
        sys.exit('❌ 无可用浏览器，请先创建：browser-act browser create --type chrome ...')
    bid = m.group(1)
    run(['browser', 'open', bid, 'https://xueqiu.com/'])
    time.sleep(3)
    run(['navigate', 'https://xueqiu.com/user/show.json'])
    time.sleep(1.5)
    md = get_md()
    if '用户未登录' in md or 'error_code' in md:
        sys.exit('❌ 雪球未登录。提示用户：在本地 Chrome 登录 xueqiu.com 后，'
                 '执行 browser-act browser import-profile 导入登录态，或 --headed 人工登录。')
    m = re.search(r'"id":(\d+)', md)
    if not m:
        sys.exit('❌ 登录校验异常（无法读取 user/show.json 响应）。')
    print(f'✅ 已登录，用户ID={m.group(1)}', file=sys.stderr)

# ---- 用户页解析 ----
def parse_posts(md):
    """解析用户页 markdown 中的帖子块"""
    posts = {}
    lines = md.split('\n')
    ts_pattern = re.compile(r'\[([^\]]*· 来自[^\]]*)\]\(https://xueqiu.com/' + XQID + r'/(\d+)\)')
    for i, line in enumerate(lines):
        m = ts_pattern.search(line)
        if not m:
            continue
        time_text, pid = m.group(1), m.group(2)
        if pid in posts:
            continue
        body_lines = []
        j = i + 1
        while j < len(lines):
            if '转发' in lines[j] or lines[j].strip().startswith('[*'):
                break
            body_lines.append(lines[j])
            j += 1
        body = '\n'.join(body_lines).strip()
        posts[pid] = {'time_text': time_text, 'body': body,
                      'truncated': '[展开]' in body or '展开' in body,
                      'modified': '修改于' in time_text}
    return posts

def scroll_load(max_scrolls=15):
    run(['navigate', f'https://xueqiu.com/u/{XQID}'])
    time.sleep(4)
    all_posts = {}
    for s in range(max_scrolls):
        md = get_md()
        if '滑动验证' in md or '访问验证' in md:
            print('⚠️ 用户页触发滑块验证，停止滚动', file=sys.stderr)
            break
        posts = parse_posts(md)
        if len(posts) > len(all_posts):
            all_posts = posts
        else:
            break
        run(['scroll', 'down', '--amount', '2500'])
        time.sleep(2)
    return all_posts

def fetch_detail(pid):
    """详情页获取完整正文 + 精确发布时间 + 滑块检测
    返回 (body, failed, publish_dt)：
      body      完整正文（滑块页/失败时为空）
      failed    是否失败（滑块或解析失败）
      publish_dt 详情页「发布于」时间（datetime 或 None）
    """
    run(['navigate', f'https://xueqiu.com/{XQID}/{pid}'])
    time.sleep(2.5)
    md = get_md()
    if '滑动验证' in md or '访问验证' in md:
        return '', True, None  # 滑块页：标记摘要，不盲重试
    # 精确发布时间（详情页时间戳，覆盖用户页模糊时间）
    pub = None
    m = re.search(r'\[(?:修改于|发布于)\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]', md)
    if m:
        pub = datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M')
    # 正文：来源：雪球App 与 风险提示 之间
    m = re.search(r'来源：雪球App.*?\n(.*?)\n风险提示', md, re.S)
    if m:
        return m.group(1).strip(), False, pub
    return '', True, pub

# ---- 主流程 ----
ensure_session()
posts = scroll_load()
print(f'用户页共解析 {len(posts)} 条帖子', file=sys.stderr)

now = datetime.datetime.now()
def parse_time(t):
    t = t.replace('修改于', '').strip()
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

# 时间窗口过滤：非「修改于」帖按用户页时间；「修改于」帖需详情页「发布于」确认
new_posts = []
for pid, p in posts.items():
    if '置顶' in p['time_text']:
        continue
    t = parse_time(p['time_text'])
    if p['modified']:
        # 修改帖：先进详情页取发布时间再判定
        full, failed, pub = fetch_detail(pid)
        if failed:
            print(f'  ⚠️ {pid}: 详情页失败（滑块/解析），跳过', file=sys.stderr)
            continue
        if full:
            p['body'] = full
            p['completeness'] = '全文'
        if pub is None:
            # 详情页无「发布于」（可能旧帖被改，无法确认发布时间）→ 跳过防误采
            print(f'  ⏭️ {pid}: 「修改于」帖且详情页无发布时间，疑似旧帖修改，跳过', file=sys.stderr)
            continue
        if cutoff and pub <= cutoff:
            continue  # 修改时间在窗口外，真实发布时间更早 → 跳过
        p['dt'] = pub
    else:
        if cutoff and t <= cutoff:
            continue
        p['dt'] = t
    new_posts.append((pid, p))

new_posts.sort(key=lambda x: x[1]['dt'], reverse=True)
print(f'cutoff 后 {len(new_posts)} 条', file=sys.stderr)

# 截断帖补全（非修改帖也需要详情页验证全文）
results = []
for pid, p in new_posts:
    if p['truncated'] or p['body'] == '':
        full, failed, pub = fetch_detail(pid)
        if not failed and full:
            p['body'] = full
            p['completeness'] = '全文'
            if pub and (p.get('dt') is None or p['modified']):
                p['dt'] = pub
        else:
            p['completeness'] = '摘要'
    else:
        p['completeness'] = '全文'
    results.append((pid, p))

# ---- 输出：0 帖不生成文件 ----
if len(results) == 0:
    print(f'ℹ️ {NICK}: cutoff 后无新帖，不生成输出文件')
    sys.exit(0)

today_cn = datetime.date.today().strftime('%Y年%m月%d日')
today_iso = datetime.date.today().strftime('%Y-%m-%d')
lines = ['---', f'title: "雪球帖子采集：{NICK} {today_cn}"', f'source: "https://xueqiu.com/u/{XQID}"',
         f'author: "{NICK}"', f'date: {today_iso}', f'recorded: {today_iso}', 'type: "帖子集"',
         'status: "待提炼"', 'tags: []', '---', '']
def extract_title(body, max_len=40):
    """提取帖子标题：完整首句优先；无完整句子时安全截断（绝不切断 markdown 链接）
    2026-08-26 修复：原实现 body[:30] 硬切会切断 [text](https://xueqiu... 链接，
    且完整句子正则把 URL 中的半角 '?'/'!' 误当句末导致匹配失败。
    """
    # 1) 完整首句优先（仅全角标点断句；内容允许半角 !?，避免 URL 中的 '?'/'!' 打断匹配）
    m = re.match(r'^([^。！？\n]+[。！？])', body)
    if m:
        return m.group(1)
    # 2) 无完整句子：将链接整体占位后截断，回退到最近安全边界，再还原链接
    links = []
    def mask(m):
        links.append(m.group(0))
        return f'\x00{len(links)-1}\x00'
    # 兼容 [alt](url) 与 [[alt]](url)（Obsidian 双括号）两种链接形态
    masked = re.sub(r'!?\[\[?[^\]]*\]\]?\([^)]*\)', mask, body)
    truncated = len(masked) > max_len
    cut = masked[:max_len]
    if truncated:
        for i in range(len(cut) - 1, -1, -1):
            if cut[i] in ' \n\t，。！？、；：':
                cut = cut[:i]
                break
    def unmask(m):
        return links[int(m.group(1))]
    cut = re.sub(r'\x00(\d+)\x00', unmask, cut)
    return cut.strip()

def detect_form(body):
    """帖子形态判定（output-format.md 2026-09-06 起落进摘要行）：
    有「回复 @」/引用块 → 回复；正文 <200 字且无引用块 → 短文；≥200 字或含小标题 → 长文
    """
    if re.search(r'回复\s*\[?@', body) or re.search(r'(?m)^>\s*\[?@', body):
        return '回复'
    if len(body) >= 200 or re.search(r'(?m)^#{1,6}\s', body):
        return '长文'
    return '短文'

for i, (pid, p) in enumerate(results, 1):
    body = p['body']
    title = extract_title(body)
    ts = p['dt'].strftime('%Y年%m月%d日 %H:%M') if p.get('dt') else p['time_text']
    form = detect_form(body)
    lines += [f'## {i}. {title}', '', body, '',
              f'> 发布：{ts} | 形态：{form} | {p["completeness"]} | [原文](https://xueqiu.com/{XQID}/{pid})', '', '---', '']

os.makedirs(os.path.dirname(OUTFILE) or '.', exist_ok=True)
with open(OUTFILE, 'w') as f:
    f.write('\n'.join(lines))
print(f'✅ {NICK}: {len(results)} 条 → {os.path.basename(OUTFILE)}')

# ---- 自动双写 info_cutoff（画像 + 控制台）----
if DO_CUTOFF:
    now_iso = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'xq_update_cutoff.py')
    r = subprocess.run(['python3', script, NICK, now_iso], capture_output=True, text=True)
    print(f'   info_cutoff 双写：{r.stdout.strip() or r.stderr.strip()}', file=sys.stderr)
