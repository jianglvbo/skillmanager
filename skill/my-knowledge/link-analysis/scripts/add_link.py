#!/usr/bin/env python3
"""
链接收集工具 - 将链接追加到当天的收集队列
用法: python3 add_link.py <url> <source> [note]

示例:
  python3 add_link.py "https://xueqiu.com/..." "雪球" "重组专家看好耀才"
  python3 add_link.py "https://mp.weixin.qq.com/..." "微信公众号"
"""

import sys
import json
import os
from datetime import datetime

def main():
    if len(sys.argv) < 3:
        print("用法: python3 add_link.py <url> <source> [note]", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    source = sys.argv[2]
    note = sys.argv[3] if len(sys.argv) > 3 else ""

    # 今天的日期文件
    today = datetime.now().strftime("%Y-%m-%d")
    links_dir = os.path.expanduser("~/.qoderworkcn/daily-links")
    os.makedirs(links_dir, exist_ok=True)
    filepath = os.path.join(links_dir, f"{today}.json")

    # 读取已有链接
    links = []
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            links = json.load(f)

    # 检查是否已存在相同 URL
    existing_urls = {item['url'] for item in links}
    if url in existing_urls:
        print(f"DUPLICATE=true (链接已存在)")
        print(f"TOTAL={len(links)}")
        return

    # 追加新链接
    new_link = {
        "url": url,
        "source": source,
        "received_at": datetime.now().astimezone().isoformat(),
        "note": note
    }
    links.append(new_link)

    # 保存
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(links, f, ensure_ascii=False, indent=2)

    print(f"ADDED=true")
    print(f"TOTAL={len(links)}")
    print(f"FILE={filepath}")

if __name__ == "__main__":
    main()
