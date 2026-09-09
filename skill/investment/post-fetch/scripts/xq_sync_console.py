#!/usr/bin/env python3
"""雪球关注列表同步 → 看板博主控制台对比（前置步骤脚本化，2026-08-19 新增；2026-09-07 改读看板 API）

博主控制台权威 = 看板 MySQL bloggers 表（vault 博主控制台.md 已退役删除）。一键输出：
  1. 新增博主（关注中但看板未登记）
  2. 取关博主（看板登记但已不关注）
  3. ID 不一致（看板 ID 与关注列表不符）
  4. 博主层残留（看板无登记但 博主/<名>/ 存在文件夹）
  5. 待采集清单（雪球ID非空博主）

用法: python3 xq_sync_console.py [--dry-run|--apply]
  --dry-run（默认）只输出对比报告；Agent 向用户确认后
  --apply 实际落地变更：新增 → POST /api/bloggers 登记；取关 → 仅报告（须用户到看板确认后手工删除，涉及目录回收不自动执行）
  --half-year 新博主的「信息截止」基准（默认：半年前今天 17:50:00）

依赖：browser-act CLI + 已登录雪球 session + 看板服务（127.0.0.1:8698）
"""
import re, sys, os, json, subprocess, datetime, argparse, urllib.request

VAULT = '/Users/jianglb/Library/Mobile Documents/iCloud~md~obsidian/Documents/投资知识库'
BLOGGER_DIR = os.path.join(VAULT, '博主')
API = 'http://127.0.0.1:8698'

def api(path, payload=None):
    if payload is None:
        with urllib.request.urlopen(API + path, timeout=15) as r:
            return json.load(r)
    req = urllib.request.Request(API + path, data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)

def find_ba():
    cands = [os.path.expanduser('~/.local/bin/browser-act'), 'browser-act']
    for c in cands:
        if '/' in c and os.path.exists(c):
            return c
        r = subprocess.run(['which', c], capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.strip()
    sys.exit('❌ browser-act CLI 未找到')

BA = find_ba()
SESSION = f'xq_sync_{os.getpid()}'

import atexit
def _close_session():
    """脚本结束自动关闭本 session（2026-09-09 修复 session 泄漏）"""
    try:
        subprocess.run([BA, 'session', 'close', SESSION], capture_output=True, text=True, timeout=20)
    except Exception:
        pass
atexit.register(_close_session)

def run(cmd):
    r = subprocess.run([BA, '--session', SESSION] + cmd, capture_output=True, text=True, timeout=45)
    return r.stdout

def fetch_following():
    """分页拉取关注列表，返回 {screen_name: id}"""
    following = {}
    page = 1
    while True:
        run(['navigate', f'https://xueqiu.com/friendships/groups/members.json?gid=0&page={page}&count=50'])
        import time; time.sleep(1.5)
        md = run(['get', 'markdown'])
        if '用户未登录' in md:
            sys.exit('❌ 雪球未登录，无法同步关注列表')
        m = re.search(r'```\n?(\{.*\})\n?```', md, re.S) or re.search(r'(\{.*\})', md, re.S)
        if not m:
            break
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            break
        users = data.get('users', [])
        if not users:
            break
        for u in users:
            following[u['screen_name']] = u['id']
        if page >= data.get('maxPage', 1):
            break
        page += 1
    return following

def parse_console():
    """读看板博主控制台（MySQL bloggers 表），返回 {name: {id, is_xq, special, cutoff}} 与最大编号"""
    data = api('/api/bloggers/live')
    console = {}
    max_no = 0
    for b in data['data']['bloggers']:
        try: max_no = max(max_no, int(b.get('name') and 0 or 0) or 0)
        except Exception: pass
        console[b['name']] = {'id': b.get('xueqiuId') or '', 'is_xq': (b.get('platform') or '') == '雪球',
                              'special': bool(b.get('special')), 'cutoff': b.get('infoCutoff') or '',
                              'registered': bool(b.get('registered'))}
    return console, max_no

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='实际落地变更（默认 dry-run 只报告）')
    ap.add_argument('--half-year', default=None, help='新博主信息截止基准（默认半年前今天 17:50:00）')
    args = ap.parse_args()

    # 登录 + 拉取关注列表
    browsers = run(['browser', 'list'])
    m = re.search(r'id=(\S+?)\s+name="([^"]+)"\s+type=(\S+)', browsers)
    if not m:
        sys.exit('❌ 无可用浏览器')
    run(['browser', 'open', m.group(1), 'https://xueqiu.com/'])
    import time; time.sleep(3)
    print('拉取关注列表...', file=sys.stderr)
    following = fetch_following()

    console, max_no = parse_console()
    xq_console = {n: v for n, v in console.items() if v['id']}

    new = {n: i for n, i in following.items() if n not in console}
    unfollow = {n: v for n, v in xq_console.items() if n not in following}
    id_mismatch = {n: (v['id'], following[n]) for n, v in xq_console.items()
                   if n in following and str(following[n]) != v['id']}
    dirs = [d for d in os.listdir(BLOGGER_DIR) if os.path.isdir(os.path.join(BLOGGER_DIR, d)) and not d.startswith('.')]
    residual = [d for d in dirs if d not in console]

    print(f"\n===== 同步报告（{'dry-run，未改动' if not args.apply else '已落地'}）=====")
    print(f"关注列表: {len(following)} 人 | 控制台: {len(console)} 行 | 雪球ID非空: {len(xq_console)}")
    print(f"\n【新增】关注中但控制台未登记: {len(new)}")
    for n, i in new.items():
        print(f"  + {n} ({i})")
    print(f"\n【取关】控制台登记但已不关注: {len(unfollow)}")
    for n, v in unfollow.items():
        print(f"  - {n} ({v['id']})")
    print(f"\n【ID 不一致】: {len(id_mismatch)}")
    for n, (cid, fid) in id_mismatch.items():
        print(f"  ! {n}: 控制台={cid} vs 关注={fid}")
    print(f"\n【博主层残留】控制台无登记但文件夹存在: {len(residual)}")
    for d in residual:
        print(f"  ! {d}")

    # ---- apply 落地 ----
    if args.apply:
        half = args.half_year or (datetime.date.today() - datetime.timedelta(days=182)).strftime('%Y-%m-%dT17:50:00')
        added = 0
        for name, xid in sorted(new.items(), key=lambda x: x[1]):
            try:
                r = api('/api/bloggers', {'name': name, 'xueqiuId': str(xid), 'platform': '雪球', 'infoCutoff': half})
                print(f"  + 登记 {name} ({xid}): {'ok' if r.get('ok') else r.get('error')}")
                if r.get('ok'): added += 1
            except Exception as e:
                print(f"  + 登记 {name} 失败: {e}")
        if unfollow:
            print(f"\n⚠️ 取关 {len(unfollow)} 人需到看板博主控制台手工删除（涉及目录回收，脚本不自动执行）: {', '.join(sorted(unfollow))}")
        print(f"\n✅ 已落地：新增登记 {added} 人")
    else:
        print("\nℹ️ 使用 --apply 落地变更（新增走看板 API 登记；取关须看板手工处理）")

    # 待采集清单
    print(f"\n【待采集】控制台雪球ID非空博主: {len(xq_console)} 位（含新增需确认）")
    for n in sorted(xq_console, key=lambda x: x):
        mark = ' [新增?]' if n in new else ''
        print(f"  {n}\t{console[n]['id']}\t截止:{console[n].get('cutoff') or '(空)'}{mark}")

if __name__ == '__main__':
    main()
