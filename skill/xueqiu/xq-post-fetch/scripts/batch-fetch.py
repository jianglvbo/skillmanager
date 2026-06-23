#!/usr/bin/env python3
"""
雪球批量帖子采集 v2.1

改进：
- 分级超时 + 退避重试（默认 2 次）
- 进度持久化（断点续采）
- 单 CDP tab 复用
- CDP Proxy 超时自动配置
- 多页支持
- JS 模板外部化（references/fetch-template.js），占位符替换
- 统一返回值解析

用法：
  python3 batch-fetch.py --ids 1505944393,2681290304 --hours 48 -o output/
  python3 batch-fetch.py --ids-file ids.txt --retry 2 --cmd-timeout 120 -o output/
  python3 batch-fetch.py --ids 1505944393 --resume
"""

import json
import time
import sys
import os
import re
import subprocess
from argparse import ArgumentParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

CDP_URL = "http://localhost:3456"
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDP_PROXY_PATH = os.path.expanduser(
    "~/.workbuddy/skills/dev/skill_2053083109158420480/scripts/cdp-proxy.mjs"
)
JS_TEMPLATE_PATH = os.path.join(SKILL_DIR, "references", "fetch-template.js")


def _load_js_template() -> str:
    with open(JS_TEMPLATE_PATH, 'r') as f:
        lines = [l for l in f if not l.strip().startswith('//') and l.strip()]
    return ''.join(lines)


def _build_fetch_js(xq_id: int, page: int, cutoff_ms: int) -> str:
    tpl = _load_js_template()
    return tpl.replace('__XQ_ID__', str(xq_id)) \
              .replace('__PAGE__', str(page)) \
              .replace('__CUTOFF_MS__', str(cutoff_ms))


def parse_cdp_value(result: dict):
    if isinstance(result, list):
        return result
    if not isinstance(result, dict):
        return []
    if 'error' in result:
        raise RuntimeError(result['error'])
    v = result.get('value')
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        return [v] if v else []
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            if isinstance(parsed, dict) and 'error' in parsed:
                raise RuntimeError(parsed['error'])
            return parsed if isinstance(parsed, list) else [parsed] if parsed else []
        except json.JSONDecodeError:
            return []
    return []


def cdp_request(path, data=None, timeout=15):
    body = data.encode('utf-8') if isinstance(data, str) else data
    headers = {'Content-Type': 'application/text'} if data else {}
    req = Request(f"{CDP_URL}{path}", data=body, headers=headers)
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def cdp_new_tab(url: str) -> str:
    return cdp_request("/new", url, timeout=15)['targetId']


def cdp_close_tab(target: str):
    try:
        cdp_request(f"/close?target={target}", timeout=5)
    except:
        pass


def cdp_eval(target: str, js: str, timeout=90) -> dict:
    return cdp_request(f"/eval?target={target}", js, timeout=timeout)


def check_login(target: str) -> bool:
    r = cdp_eval(target, "document.title", timeout=10)
    return '我的首页' in str(r.get('value', ''))


def ensure_cdp_proxy(cmd_timeout: int):
    try:
        r = cdp_request("/health", timeout=3)
        if r.get('status') == 'ok':
            return
    except:
        pass
    try:
        subprocess.run(['pkill', '-f', 'cdp-proxy.mjs'], capture_output=True)
    except:
        pass
    time.sleep(2)
    env = os.environ.copy()
    env['CDP_CMD_TIMEOUT'] = str(cmd_timeout * 1000)
    subprocess.Popen(
        ['node', CDP_PROXY_PATH],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    time.sleep(4)
    for _ in range(5):
        try:
            r = cdp_request("/health", timeout=5)
            if r.get('status') == 'ok':
                return
        except:
            time.sleep(2)
    raise RuntimeError("CDP Proxy 启动失败")


def fetch_user_page(target: str, xq_id: int, hours: int,
                    page: int, timeout: int) -> list:
    cutoff_ms = int((time.time() - hours * 3600) * 1000)
    js = _build_fetch_js(xq_id, page, cutoff_ms)
    r = cdp_eval(target, js, timeout=timeout)
    return parse_cdp_value(r)


def fetch_user_with_retry(target: str, xq_id: int, hours: int,
                           max_pages: int, timeouts: list) -> list:
    all_posts = []
    retry = 0
    page = 1
    while page <= max_pages:
        t = timeouts[min(retry, len(timeouts) - 1)]
        try:
            posts = fetch_user_page(target, xq_id, hours, page, t)
            if isinstance(posts, dict) and 'error' in posts:
                raise RuntimeError(posts['error'])
            all_posts.extend(posts)
            if len(posts) < 15:
                break
            page += 1
            retry = 0
            time.sleep(0.3)
        except Exception as e:
            retry += 1
            if retry > len(timeouts):
                print(f"  ❌ 重试耗尽: {e}", file=sys.stderr)
                break
            print(f"  ⚠️  retry {retry}/{len(timeouts)}: {e}", file=sys.stderr)
            time.sleep(2 ** retry)
    return all_posts


def load_progress(output_dir: str) -> dict:
    path = os.path.join(output_dir, '.progress.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {'completed': {}, 'failed': {}, 'pending': []}


def save_progress(output_dir: str, progress: dict):
    path = os.path.join(output_dir, '.progress.json')
    with open(path, 'w') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def main():
    parser = ArgumentParser(description='雪球批量帖子采集 v2.1')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ids', help='逗号分隔的 xq_id')
    group.add_argument('--ids-file', help='xq_id 列表文件')
    parser.add_argument('--hours', type=int, default=48, help='时间窗口（小时）')
    parser.add_argument('--output-dir', '-o', default='.')
    parser.add_argument('--retry', type=int, default=2, help='重试次数')
    parser.add_argument('--max-pages', type=int, default=3, help='最大页数')
    parser.add_argument('--cmd-timeout', type=int, default=120, help='CDP 命令超时（秒）')
    parser.add_argument('--resume', action='store_true', help='断点续采')
    parser.add_argument('--delay', type=float, default=0.3, help='用户间延迟（秒）')
    args = parser.parse_args()

    if args.ids:
        ids = [int(x.strip()) for x in args.ids.split(',') if x.strip()]
    else:
        with open(args.ids_file) as f:
            ids = [int(line.strip()) for line in f
                   if line.strip() and not line.startswith('#')]
    if not ids:
        print("错误: 无有效 xq_id", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    progress = load_progress(args.output_dir) if args.resume else {
        'completed': {}, 'failed': {}, 'pending': [str(i) for i in ids]
    }

    remaining = [str(i) for i in ids if str(i) not in progress.get('completed', {})]
    if not remaining:
        print("所有博主已完成采集")
        return

    base = args.cmd_timeout
    timeouts = [base, base + 30, base + 60][:args.retry + 1]

    print(f"目标: {len(ids)} 位 | 剩余: {len(remaining)} | 窗口: {args.hours}h")
    print(f"重试: {args.retry}次 | 超时: {timeouts}s | 多页: 最多{args.max_pages}页")

    print("\n启动 CDP Proxy...")
    ensure_cdp_proxy(args.cmd_timeout)
    print("  ✅ Proxy 就绪")

    print("打开雪球...")
    target = cdp_new_tab('https://xueqiu.com/')
    time.sleep(3)
    if not check_login(target):
        cdp_close_tab(target)
        print("❌ 雪球未登录！请在 Chrome 中登录后重试", file=sys.stderr)
        sys.exit(1)
    print("  ✅ 已登录")

    total_posts = 0
    print(f"\n开始采集 {len(remaining)} 位...\n")

    for i, uid_str in enumerate(remaining):
        uid = int(uid_str)
        print(f"[{i+1}/{len(remaining)}] uid={uid} ", end='', flush=True)

        posts = fetch_user_with_retry(target, uid, args.hours,
                                       args.max_pages, timeouts)

        out_file = os.path.join(args.output_dir, f'blogger_posts_{uid}.json')
        with open(out_file, 'w') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)

        n = len(posts)
        total_posts += n
        print(f"→ {n} posts")

        if n > 0:
            progress.setdefault('completed', {})[uid_str] = n
        else:
            progress.setdefault('failed', {})[uid_str] = 'no_posts_or_timeout'

        save_progress(args.output_dir, progress)

        if i < len(remaining) - 1:
            time.sleep(args.delay)

    n_ok = len(progress.get('completed', {}))
    n_fail = len(progress.get('failed', {}))
    print(f"\n{'=' * 50}")
    print(f"完成: {total_posts} 条 / {n_ok}/{len(ids)} 位博主")
    if n_fail:
        failed = list(progress['failed'].keys())
        print(f"失败: {len(failed)} 位 — {', '.join(failed[:10])}")
    print(f"输出: {os.path.abspath(args.output_dir)}")

    cdp_close_tab(target)


if __name__ == '__main__':
    main()
