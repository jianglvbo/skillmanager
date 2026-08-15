#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""健身塑形控制台结构校验：JS 语法 + div/section 平衡 + 服务可用。
用法: python3 validate.py [index.html 路径，默认 web/index.html]
输出: 每项 OK/FAIL；任一 FAIL 退出码 1。
"""
import re
import subprocess
import sys
import urllib.request

HTML = sys.argv[1] if len(sys.argv) > 1 else "/Users/jianglb/WorkBuddy/2026-08-10-21-02-24/fitness-console/web/index.html"

fail = []

def check(name, ok, detail=""):
    print(("✅ " if ok else "❌ ") + name + (f" · {detail}" if detail else ""))
    if not ok:
        fail.append(name)

# 1. JS 语法（提取全部 <script> 内联块，node --check）
try:
    c = open(HTML, encoding="utf-8").read()
except FileNotFoundError:
    check("读取文件", False, HTML)
    sys.exit(1)

scripts = "\n".join(re.findall(r"<script>(.*?)</script>", c, re.S))
tmp = "/tmp/fc_validate.js"
open(tmp, "w", encoding="utf-8").write(scripts)
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
check("JS 语法", r.returncode == 0, r.stderr.strip()[:300] if r.returncode else "")

# 2. div 开闭平衡
o, cl = len(re.findall(r"<div[\s>]", c)), len(re.findall(r"</div>", c))
check("div 平衡", o == cl, f"开{o} 闭{cl}")

# 3. section 开标签完整（5 个主页面 section 闭合正确、无粘连）
bad = re.findall(r"</section>\s*id=", c)
sections = re.findall(r'<section class="page[^"]*" id="page-([a-z]+)"', c)
need = {"plan", "diet", "workout", "me", "settings"}
check("section 完整", not bad and need.issubset(set(sections)), f"缺失:{need-set(sections)} 粘连:{len(bad)}")

# 4. 服务可用（可选）
try:
    with urllib.request.urlopen("http://127.0.0.1:8699/", timeout=5) as resp:
        check("本机服务", resp.status == 200, f"HTTP {resp.status}")
except Exception as e:
    check("本机服务", False, str(e)[:100])

sys.exit(1 if fail else 0)
