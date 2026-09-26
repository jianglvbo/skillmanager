#!/usr/bin/env python3
"""Bark 推送到用户 iPhone（api.day.app，device key 已写死）。

用法: notify.py [标题] 正文|-
  标题缺省为 "ZCode"；正文传 "-" 时从 stdin 读（适合多行/长文本）。
退出码: 0 = API code 200 成功；1 = 推送失败（打印返回体或异常）；2 = 用法错误。
"""
import json
import sys
import urllib.request

DEVICE_KEY = "DYrdRmSCeBxCS4Puvg2n67"  # 用户 2026-09-26 确认非敏感，可写死
SERVER = "https://api.day.app/push"


def main() -> int:
    args = sys.argv[1:]
    if len(args) == 1:
        title, body = "ZCode", args[0]
    elif len(args) == 2:
        title, body = args
    else:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if body == "-":
        body = sys.stdin.read()
    if not body.strip():
        print("正文为空", file=sys.stderr)
        return 2

    payload = json.dumps({"device_key": DEVICE_KEY, "title": title, "body": body}).encode()
    req = urllib.request.Request(
        SERVER, data=payload, headers={"Content-Type": "application/json; charset=utf-8"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15).read().decode()
    except Exception as exc:
        print(f"推送失败: {exc}", file=sys.stderr)
        return 1
    print(resp)
    return 0 if '"code":200' in resp else 1


if __name__ == "__main__":
    sys.exit(main())
