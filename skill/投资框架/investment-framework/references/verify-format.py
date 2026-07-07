#!/usr/bin/env python3
"""
投资知识库格式回检脚本
用于检查 wiki 条目的段落布局、脚注格式、内联标记等问题。

用法：
    python3 verify-format.py <vault_path> [--fix] [--scope 其他,博主,宏观]

参数：
    vault_path  Obsidian vault 根目录路径
    --fix       自动修复可修复的问题（段落布局、空脚注占位、## 来源残留）
    --scope     限定检查范围（逗号分隔的顶层目录名）

检查项：
    1. 同行标题：## / ### 嵌在段落末尾同行（不会渲染为标题）
    2. 标题间距：标题前后无空行
    3. 段落紧凑：连续 ≥5 行无空行
    4. 脚注内联标记：有定义无标记 / 有标记无定义（孤儿脚注）
    5. 脚注模板废话：描述为"A与B的跨维度关联"等无信息量内容
    6. 残留段落：## 来源、空 ## 脚注 占位
    7. source 字段：标量格式（应为 YAML 列表）
    8. 空 # 标题：独占一行的 "#"（无标题文字，不会渲染）
"""

import os, re, sys, yaml

def split_fm_body(content):
    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            return content[:end+3], content[end+3:]
    return '', content

def check_inline_headings(body):
    issues = []
    for i, line in enumerate(body.split('\n')):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if re.search(r'#{2,4}\s+\S', line):
            issues.append({'line': i+1, 'text': line[:80]})
    return issues

def check_heading_spacing(body):
    issues = []
    lines = body.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not re.match(r'^#{2,6}\s', stripped):
            continue
        if i > 0 and lines[i-1].strip() and not re.match(r'^#{1,6}\s', lines[i-1].strip()):
            issues.append({'line': i+1, 'type': 'before', 'heading': stripped[:50]})
        if i+1 < len(lines) and lines[i+1].strip() and not re.match(r'^#{1,6}\s', lines[i+1].strip()):
            issues.append({'line': i+1, 'type': 'after', 'heading': stripped[:50]})
    return issues

def check_compact_paragraphs(body):
    lines = body.split('\n')
    run = 0
    max_run = 0
    for line in lines:
        if line.strip():
            run += 1
            max_run = max(max_run, run)
        else:
            run = 0
    return [{'max_consecutive': max_run}] if max_run >= 5 else []

def check_footnote_inline(body):
    defs = set(re.findall(r'^\[\^([^\]]+)\]:', body, re.MULTILINE))
    inline = set()
    for m in re.finditer(r'\[\^([^\]]+)\]', body):
        pos = m.end()
        if pos < len(body) and body[pos] == ':':
            continue
        inline.add(m.group(1))
    issues = []
    for fn in defs - inline:
        issues.append({'type': 'no_inline', 'id': fn})
    for fn in inline - defs:
        issues.append({'type': 'no_def', 'id': fn})
    return issues

def check_footnote_quality(body):
    issues = []
    for m in re.finditer(r'^\[\^(enhance|supplement|conflict|complement)-\d+\]:\s*(.+)$', body, re.MULTILINE):
        fn_body = m.group(2).strip()
        if '的跨维度关联' in fn_body:
            issues.append({'fn': m.group(1), 'body': fn_body[:80], 'type': 'template'})
        wl_match = re.match(r'\[\[[^\]]+\]\]\s*—\s*(.*)', fn_body)
        if wl_match:
            desc = wl_match.group(1).strip()
            if desc in ('增强', '补充', '冲突', '互补', ''):
                issues.append({'fn': m.group(1), 'body': fn_body[:80], 'type': 'no_desc'})
    return issues

def check_residual_sections(body):
    issues = []
    if re.search(r'^## 来源\s*$', body, re.MULTILINE):
        issues.append({'type': 'source_section'})
    if re.search(r'^## 脚注\s*\n(## |\Z)', body, re.MULTILINE):
        issues.append({'type': 'empty_footnote'})
    return issues

def check_empty_headings(body):
    """Check for standalone '#' lines with no heading text."""
    issues = []
    for i, line in enumerate(body.split('\n')):
        if line.strip() == '#':
            issues.append({'line': i+1})
    return issues

def check_source_field(fm):
    if 'source' not in fm or fm['source'] is None:
        return [{'type': 'missing'}]
    if not isinstance(fm['source'], list):
        return [{'type': 'scalar', 'value': str(fm['source'])[:60]}]
    issues = []
    for s in fm['source']:
        if isinstance(s, str) and not s.startswith('[['):
            issues.append({'type': 'not_wikilink', 'value': s[:60]})
    return issues

def fix_inline_headings(body):
    lines = body.split('\n')
    fixed = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            fixed.append(line)
            continue
        matches = list(re.finditer(r'(?<![#\s])(#{2,4}\s+\S)', line))
        if not matches:
            fixed.append(line)
            continue
        current = line
        for m in reversed(matches):
            before = current[:m.start()].rstrip()
            after = current[m.start():].strip()
            if before:
                current = before + '\n\n' + after
        for part in current.split('\n'):
            fixed.append(part)
    return '\n'.join(fixed)

def fix_heading_spacing(body):
    lines = body.split('\n')
    fixed = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^#{2,6}\s', stripped):
            if fixed and fixed[-1].strip() and not re.match(r'^#{1,6}\s', fixed[-1].strip()):
                fixed.append('')
            fixed.append(line)
            if i+1 < len(lines) and lines[i+1].strip() and not re.match(r'^#{1,6}\s', lines[i+1].strip()):
                fixed.append('')
        else:
            fixed.append(line)
    return '\n'.join(fixed)

def fix_residual_sections(body):
    body = re.sub(r'\n*## 来源\n.*?(?=\n## |\Z)', '', body, flags=re.DOTALL)
    body = re.sub(r'\n## 脚注\n(?=\n## |\Z)', '\n', body)
    return body

def fix_empty_headings(body):
    """Remove standalone '#' lines with no heading text."""
    lines = body.split('\n')
    new_lines = [line for line in lines if line.strip() != '#']
    body = '\n'.join(new_lines)
    body = re.sub(r'\n{3,}', '\n\n', body)
    return body

def verify_file(fpath, rel):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    fm_text, body = split_fm_body(content)
    if not body:
        return None
    fm = {}
    if fm_text:
        try:
            fm = yaml.safe_load(fm_text[3:fm_text.find('---', 3)].strip()) or {}
        except:
            pass
    issues = {
        'file': rel,
        'inline_headings': check_inline_headings(body),
        'heading_spacing': check_heading_spacing(body),
        'compact_paragraphs': check_compact_paragraphs(body),
        'footnote_inline': check_footnote_inline(body),
        'footnote_quality': check_footnote_quality(body),
        'residual_sections': check_residual_sections(body),
        'empty_headings': check_empty_headings(body),
        'source_field': check_source_field(fm) if fm else [],
    }
    issues = {k: v for k, v in issues.items() if v}
    return issues if len(issues) > 1 else None

def fix_file(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    fm_text, body = split_fm_body(content)
    if not body:
        return False
    original = body
    body = fix_inline_headings(body)
    body = fix_heading_spacing(body)
    body = fix_residual_sections(body)
    body = fix_empty_headings(body)
    if body != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(fm_text + body)
        return True
    return False

def main():
    if len(sys.argv) < 2:
        print("用法: python3 verify-format.py <vault_path> [--fix] [--scope 其他,博主,宏观]")
        sys.exit(1)
    vault = sys.argv[1]
    auto_fix = '--fix' in sys.argv
    scope = None
    if '--scope' in sys.argv:
        idx = sys.argv.index('--scope')
        if idx + 1 < len(sys.argv):
            scope = set(sys.argv[idx+1].split(','))
    skip_names = {'博主.md', '其他.md', '宏观.md', '我的.md', '工作区.md', '原始资源.md', '粗制品.md'}
    wiki_dirs = ('我的', '博主', '其他', '宏观')
    total_files = 0
    total_issues = 0
    files_with_issues = 0
    fix_count = 0
    counters = {k: 0 for k in ['inline_headings', 'heading_spacing', 'compact_paragraphs',
                                'footnote_inline', 'footnote_quality', 'residual_sections',
                                'source_field', 'empty_headings']}
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in {'.obsidian', '.trash', '附件'}]
        rel_root = os.path.relpath(root, vault)
        top = rel_root.split('/')[0]
        if top not in wiki_dirs or (scope and top not in scope):
            continue
        for f in files:
            if not f.endswith('.md') or f in skip_names:
                continue
            fpath = os.path.join(root, f)
            rel = os.path.relpath(fpath, vault)
            total_files += 1
            if auto_fix:
                if fix_file(fpath):
                    fix_count += 1
            result = verify_file(fpath, rel)
            if result:
                files_with_issues += 1
                for key in counters:
                    if key in result:
                        counters[key] += len(result[key])
                        total_issues += len(result[key])
    print(f"=== 格式回检报告 ===")
    print(f"扫描文件: {total_files}")
    print(f"问题文件: {files_with_issues}")
    print(f"问题总数: {total_issues}")
    if auto_fix:
        print(f"自动修复: {fix_count} 个文件")
    print()
    for k, v in counters.items():
        label = {'inline_headings': '同行标题', 'heading_spacing': '标题间距',
                 'compact_paragraphs': '段落紧凑', 'footnote_inline': '脚注孤儿',
                 'footnote_quality': '脚注废话', 'residual_sections': '残留段落',
                 'source_field': 'source字段', 'empty_headings': '空#标题'}[k]
        print(f"{label}: {v}")
    print()
    if total_issues == 0:
        print("✅ 全部通过")
    else:
        print(f"❌ 发现 {total_issues} 个问题")
    return 1 if total_issues > 0 else 0

if __name__ == '__main__':
    sys.exit(main())
