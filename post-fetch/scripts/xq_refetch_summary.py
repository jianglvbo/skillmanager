#!/usr/bin/env python3
"""摘要帖补全器（2026-09-08 沉淀，替代临时脚本）

对帖子集中标「摘要」的帖子导航详情页补全全文。

用法:
  python3 xq_refetch_summary.py [--dir OUTDIR] [--date "YYYY年M月D日"] [文件...]

安全设计（2026-09-08 事故后加固）：
  1. 正文替换仅改写正文区间 b[start(2):end(2)]，绝不吞掉摘要行与块间换行
     （原临时脚本用 group(1)+body+group(3) 丢失摘要行剩余部分 → 13 文件 79 处损坏）
  2. 写回前结构自检：## N. 数 == > 发布： 数、摘要行格式合规、无 "> 发布：## " 损坏特征
     自检不通过 → 拒绝写入该文件并报错
  3. 写回前自动备份 .bak（保留最近一次）
  4. 滑块：检测到验证页 → 激活浏览器窗口置前，等待用户手动过（默认 120s），过后继续

依赖：**ego lite**（已打开且已登录雪球）

2026-09-16 迁移：浏览器层从 browser-act 换成 ego lite（用户口径「以后别用 chrome 了，
用 ego lite」）。正文改从 ego 页面的 `.article__bd__detail` 取 DOM 文本；
滑块检测沿用，命中时把 **ego lite** 窗口置前让用户手动过。
"""
import re, sys, os, glob, time, shutil, argparse

# 统一接入层（ego lite；不再依赖 browser-act / Chrome）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xq_ego import bring_to_front, ego_session   # noqa: E402
# 仅当要补全 vault 里的历史批次时才需要它（默认输入目录见下）
VAULT = '/Users/jianglb/Library/Mobile Documents/iCloud~md~obsidian/Documents/投资知识库'
# ⚠️ 2026-09-16 修正：采集产物**不再进 vault**（落 post_history 后即清理），
# 所以默认目录改成工具层的临时输出目录。要在已入库的帖子上补全，需先把帖子集
# 从 post_history 导出成 md（本脚本只吃 md 文件）。
DEFAULT_DIR = os.path.expanduser("~/.cache/xueqiu-spyder/out")
# 备份目录在 vault 外（2026-09-09：.bak 不得污染 vault）
BACKUP_DIR = os.path.expanduser('~/.cache/post-fetch/backups')

PUB_LINE_RE = re.compile(
    r'^> 发布：\d{4}年\d{1,2}月\d{1,2}日 \d{1,2}:\d{2} \| 形态：(回复|短文|长文) \| (全文|摘要) \| \[原文\]\(https://xueqiu\.com/\d+/\d+\)$',
    re.M)


def sync_status(text):
    """按摘要帖数量同步 frontmatter status（2026-09-09：摘要言论不可提炼）

    含摘要帖 → status: "待提炼-含摘要"（提炼时须跳过「摘要」帖）
    全部全文 → status: "待提炼"
    """
    n_summary = len(re.findall(r'\| 摘要 \| \[原文\]', text))
    target = '待提炼-含摘要' if n_summary else '待提炼'
    return re.sub(r'^status: .*$', f'status: "{target}"', text, count=1, flags=re.M)


def read_detail(page):
    """读详情页正文＋页面文本（ego：DOM 直取，不再依赖 browser-act 的 markdown）"""
    body = page.evaluate(
        "() => { const el = document.querySelector('.article__bd__detail');"
        " return el ? el.textContent.trim() : ''; }") or ''
    page_text = page.text()
    return body, page_text


def is_slider(text):
    return ('滑动验证' in text) or ('访问验证' in text) or ('按住滑块' in text) or ('安全验证' in text)


def detect_form(body):
    if re.search(r'回复\s*\[?@', body) or re.search(r'(?m)^>\s*\[?@', body):
        return '回复'
    if len(body) >= 200 or re.search(r'(?m)^#{1,6}\s', body):
        return '长文'
    return '短文'


def clean_emoji(body):
    return re.sub(r'!\[([^\]]*)\]\([^)]*"\[([^\]]*)\]"[^)]*\)', r'[\2]', body)


def fetch_detail(xid, pid, page, wait_slider=120):
    """详情页取正文（ego 通道）。滑块时把 ego lite 置前，等用户手动过。返回 (body, ok)"""
    url = f'https://xueqiu.com/{xid}/{pid}'
    page.goto(url)
    time.sleep(1.5)
    body, page_text = read_detail(page)
    if is_slider(page_text) or is_slider(body):
        print(f'  🧩 {pid}: 滑块验证！已把 ego lite 置前，请手动过验证（最多等 {wait_slider}s）',
              file=sys.stderr, flush=True)
        bring_to_front()
        deadline = time.time() + wait_slider
        while time.time() < deadline:
            time.sleep(4)
            page.goto(url)
            time.sleep(1.5)
            body, page_text = read_detail(page)
            if not (is_slider(page_text) or is_slider(body)):
                print(f'  ✅ {pid}: 滑块已通过', file=sys.stderr, flush=True)
                break
        else:
            print(f'  ⏭️ {pid}: 等待超时，保留摘要', file=sys.stderr, flush=True)
            return '', False
    if body:
        return clean_emoji(body), True
    return '', False


def validate(text):
    """写回前结构自检，返回 (ok, reason)"""
    if '> 发布：## ' in text:
        return False, '检测到损坏特征 "> 发布：## "'
    n_h2 = len(re.findall(r'(?m)^## \d+\. ', text))
    n_pub = len(re.findall(r'(?m)^> 发布：', text))
    if n_h2 != n_pub:
        return False, f'帖子数({n_h2}) 与摘要行数({n_pub}) 不一致'
    pubs = re.findall(r'(?m)^> 发布：.*$', text)
    for p in pubs:
        if not PUB_LINE_RE.match(p):
            return False, f'摘要行格式异常: {p[:60]}'
    return True, ''


def process_file(path, page, wait_slider, dry_run=False):
    content = open(path).read()
    blocks = re.split(r'(?m)^(?=## \d+\. )', content)
    summary = done = fail = 0
    new_blocks = []
    for b in blocks:
        m = re.search(r'\[原文\]\(https://xueqiu\.com/(\d+)/(\d+)\)', b)
        if not m or '| 摘要 |' not in b:
            new_blocks.append(b)
            continue
        summary += 1
        xid, pid = m.group(1), m.group(2)
        body, ok = fetch_detail(xid, pid, page, wait_slider)
        if not ok:
            fail += 1
            new_blocks.append(b)
            continue
        m2 = re.search(r'(?m)^(## .+?\n\n)(.*?)(\n\n> 发布：)', b, re.S)
        if m2:
            # ✅ 只替换正文区间，保留标题、摘要行与块间结构
            b = b[:m2.start(2)] + body + b[m2.end(2):]
        b = b.replace('| 摘要 |', '| 全文 |')
        b = re.sub(r'形态：(回复|短文|长文)', f'形态：{detect_form(body)}', b, count=1)
        done += 1
        new_blocks.append(b)

    if not done:
        return summary, 0, fail, True

    new_text = ''.join(new_blocks)
    ok, reason = validate(new_text)
    if not ok:
        print(f'  ❌ {os.path.basename(path)}: 自检失败，拒绝写入（{reason}）', file=sys.stderr, flush=True)
        return summary, 0, fail, False
    new_text = sync_status(new_text)
    if dry_run:
        print(f'  ℹ️ {os.path.basename(path)}: dry-run 自检通过，未写入', file=sys.stderr, flush=True)
        return summary, done, fail, True
    # 备份放 vault 外（2026-09-09 用户要求：.bak 不得污染 vault）
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(path, os.path.join(
        BACKUP_DIR, f'{os.path.basename(path)}.{time.strftime("%Y%m%d-%H%M%S")}.bak'))
    open(path, 'w').write(new_text)
    return summary, done, fail, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', default=DEFAULT_DIR, help='帖子集目录')
    ap.add_argument('--date', default=None, help='批次日期，如 "2026年09月08日"（默认全部）')
    ap.add_argument('--wait-slider', type=int, default=120, help='滑块等待秒数')
    ap.add_argument('--dry-run', action='store_true', help='只自检不写入')
    ap.add_argument('files', nargs='*')
    args = ap.parse_args()

    files = args.files or sorted(glob.glob(os.path.join(
        args.dir, f'雪球采集-*{args.date}.md' if args.date else '雪球采集-*.md')))
    tot = {'s': 0, 'd': 0, 'f': 0}
    with ego_session() as page:            # 一个会话跑完全部文件，退出时关桥（不留页签）
        for f in files:
            if not os.path.exists(f):
                continue
            s, d, fa, ok = process_file(f, page, args.wait_slider, args.dry_run)
            tot['s'] += s; tot['d'] += d; tot['f'] += fa
            if s:
                print(f'{os.path.basename(f)}: 摘要{s} 补全{d} 跳过{fa}{"" if ok else " [自检失败]"}',
                      file=sys.stderr, flush=True)
    print(f"\n===== 汇总: 摘要{tot['s']} 补全{tot['d']} 待重试{tot['f']} =====", file=sys.stderr)


if __name__ == '__main__':
    main()
