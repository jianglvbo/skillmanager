#!/usr/bin/env python3
"""
投资知识库 inbound 引用反查脚本（framework-rules #25/#26 执行工具）

用途：删除 / 回收 / 移动某条目**之前**必跑，列出 vault 内所有指向它的引用
     （wikilink + 关联脚注定义 + frontmatter source 字段），确认双向清理范围，
     防止删除后残留悬空链接（2026-08-14 教训：段永平 7 文件删除未反查，
     遗留 11 处悬空脚注引用直至审查才暴露）。

用法：
    python3 check_inbound.py <vault> <target> [--basename]

参数：
    vault    Obsidian vault 根目录路径
    target   目标条目相对路径（可带 .md 后缀），如 "博主/段永平/段永平"
    --basename  额外按文件名简写匹配（[[文件名]] 形式；Obsidian 支持但库内不规范，
             命中简写时标注，由用户判断是否为真引用）

输出：
    逐条列出：来源文件 | 行号 | 引用文本 | 匹配类型（完整路径/简写basename）
    无引用时输出 "无 inbound 引用，可安全删除"

依赖：Python 3.8+，仅标准库（os/re/argparse）。
"""
import os, re, argparse

def main():
    ap = argparse.ArgumentParser(description="反查 vault 内指向目标条目的引用")
    ap.add_argument("vault", help="vault 根目录路径")
    ap.add_argument("target", help="目标条目相对路径（可带 .md 后缀）")
    ap.add_argument("--basename", action="store_true", help="额外按文件名简写匹配")
    args = ap.parse_args()

    vault = os.path.expanduser(args.vault)
    t = args.target.rstrip('.md')
    tbase = t.split('/')[-1]
    if not os.path.isdir(vault):
        print(f"vault 路径不存在: {vault}")
        return 2

    EXCLUDE = {".git", ".obsidian", ".trash", ".space", ".smart-env", ".makemd", "__visit_history"}
    hits = []
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in EXCLUDE]
        for fn in files:
            if not fn.endswith('.md'):
                continue
            rel = os.path.relpath(os.path.join(root, fn), vault)
            try:
                lines = open(os.path.join(root, fn), encoding='utf-8').read().split('\n')
            except (UnicodeDecodeError, OSError):
                continue
            for i, line in enumerate(lines, 1):
                for m in re.finditer(r'\[\[([^\]]+)\]\]', line):
                    link = m.group(1).rstrip('.md')
                    if link == t:
                        hits.append((rel, i, m.group(0), '完整路径'))
                    elif args.basename and (link == tbase or link.endswith('/' + tbase)):
                        hits.append((rel, i, m.group(0), '简写basename(请人工确认)'))

    if not hits:
        print(f"无 inbound 引用，可安全删除: {t}")
        return 0
    print(f"发现 {len(hits)} 处指向 [{t}] 的引用（删除前须全部清理）:")
    for rel, line_no, text, mtype in sorted(hits):
        print(f"  {rel}:{line_no}  {text}  [{mtype}]")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
