#!/usr/bin/env python3
"""
雪球帖子保存工具

从 CDP eval 输出中解析帖子列表，按 xq_id 分组保存。

用法：
  python3 save-posts.py single -i cdp_output.json --xq-id 9650668145 --name 管我财 -o output/
  python3 save-posts.py merge -m "raw/blogger_posts_*.json" -o output/
"""

import json
import os
import sys
import glob
import re
from argparse import ArgumentParser


def parse_cdp_output(raw) -> list:
    """统一解析 CDP eval 返回值：str/list/dict/error → list"""
    if isinstance(raw, list):
        return raw
    if not isinstance(raw, dict):
        return []
    if 'error' in raw:
        raise RuntimeError(raw['error'])
    v = raw.get('value')
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        if 'error' in v:
            raise RuntimeError(v['error'])
        return [v] if v else []
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict) and 'error' in parsed:
                raise RuntimeError(parsed['error'])
            return [parsed] if parsed else []
        except json.JSONDecodeError:
            return []
    return []


def save_posts(posts: list, xq_id: int, name: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    for p in posts:
        p['_fetched_for'] = f'xq_id={xq_id}'
    safe_name = (name or str(xq_id)).replace('/', '_').replace(' ', '_')
    out_path = os.path.join(output_dir, f'{safe_name}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    return out_path


def cmd_single(args):
    if not os.path.exists(args.input):
        print(f'错误: 输入文件不存在: {args.input}', file=sys.stderr)
        sys.exit(1)
    with open(args.input, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    posts = parse_cdp_output(raw)
    out_path = save_posts(posts, args.xq_id, args.name, args.output_dir)
    print(f'博主: {args.name or args.xq_id}（ID: {args.xq_id}）')
    print(f'帖子数: {len(posts)} 条')
    print(f'输出: {out_path}')


def cmd_merge(args):
    all_posts = []
    files = sorted(glob.glob(args.merge))
    if not files:
        print('错误: 未找到匹配的文件', file=sys.stderr)
        sys.exit(1)
    for f in files:
        with open(f, 'r', encoding='utf-8') as fh:
            raw = json.load(fh)
        posts = parse_cdp_output(raw)
        for p in posts:
            m = re.search(r'blogger_posts_(\d+)\.json', f)
            if m:
                p.setdefault('user_id', int(m.group(1)))
        all_posts.extend(posts)
    os.makedirs(args.output_dir, exist_ok=True)
    out_path = os.path.join(args.output_dir, 'merged_posts.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)
    user_ids = set(p.get('user_id', 0) for p in all_posts)
    print(f'合并文件数: {len(files)}')
    print(f'总帖子数: {len(all_posts)} 条')
    print(f'涉及用户: {len(user_ids)} 位')
    print(f'输出: {out_path}')


def main():
    parser = ArgumentParser(description='雪球帖子保存工具')
    sub = parser.add_subparsers(dest='command', help='模式')
    p1 = sub.add_parser('single', help='单博主模式')
    p1.add_argument('--input', '-i', required=True, help='CDP eval 输出 JSON 文件')
    p1.add_argument('--xq-id', type=int, required=True, help='雪球用户 ID')
    p1.add_argument('--name', default=None, help='博主名')
    p1.add_argument('--output-dir', '-o', default='.', help='输出目录')
    p2 = sub.add_parser('merge', help='批量合并模式')
    p2.add_argument('--merge', '-m', required=True, help='glob 模式')
    p2.add_argument('--output-dir', '-o', default='.', help='输出目录')
    args = parser.parse_args()
    if args.command == 'single':
        cmd_single(args)
    elif args.command == 'merge':
        cmd_merge(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
