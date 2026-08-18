#!/usr/bin/env python3
"""双写更新 info_cutoff：博主画像 frontmatter + 博主控制台表格行（2026-08-15 实战验证）

用法: python3 xq_update_cutoff.py <nickname> <ISO时间>
  nickname  博主名
  ISO时间   格式 YYYY-MM-DDTHH:mm:ss（通常为采集完成时间）

行为：① 画像 博主/<名>/<名>.md 的 info_cutoff + updateDate
      ② 控制台 工作区/博主控制台.md 对应行「信息截止」列 + 控制台 frontmatter updateDate
"""
"""双写更新 info_cutoff：博主画像 frontmatter + 博主控制台表格行
用法: python3 xq_update_cutoff.py <nickname> <ISO时间>
"""
import re, sys, os

VAULT = '/Users/jianglb/Library/Mobile Documents/iCloud~md~obsidian/Documents/投资知识库'
nickname, new_cutoff = sys.argv[1], sys.argv[2]

changed = []

# 1. 博主画像
profile = os.path.join(VAULT, '博主', nickname, f'{nickname}.md')
if os.path.exists(profile):
    with open(profile) as f:
        content = f.read()
    updated = False
    if re.search(r'^info_cutoff:.*$', content, re.M):
        content = re.sub(r'^info_cutoff:.*$', f'info_cutoff: {new_cutoff}', content, count=1, flags=re.M)
        updated = True
    if re.search(r'^updateDate:.*$', content, re.M):
        content = re.sub(r'^updateDate:.*$', f'updateDate: {new_cutoff[:10]}', content, count=1, flags=re.M)
    if updated:
        with open(profile, 'w') as f:
            f.write(content)
        changed.append(f'画像 {profile}')
else:
    changed.append(f'画像不存在（跳过）：博主/{nickname}/{nickname}.md')

# 2. 博主控制台
console = os.path.join(VAULT, '工作区', '博主控制台.md')
with open(console) as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('|') and nickname in line and '信息截止' not in line:
        # 表格行：| 编号 | 博主 | 别名 | 雪球ID | 是否雪球博主 | 是否特别关注 | 信息截止 |
        parts = line.rstrip('\n').split('|')
        # parts = ['', ' 编号 ', ' 博主 ', ' 别名 ', ' 雪球ID ', ' 是 ', ' 否 ', ' 信息截止 ', '']
        if len(parts) >= 8:
            parts[7] = f' {new_cutoff} '
            line = '|'.join(parts) + '\n'
            changed.append(f'控制台行 {nickname}')
    new_lines.append(line)

with open(console, 'w') as f:
    f.writelines(new_lines)

# 3. 控制台 updateDate
with open(console) as f:
    content = f.read()
content = re.sub(r'^updateDate:.*$', f'updateDate: {new_cutoff[:10]}', content, count=1, flags=re.M)
with open(console, 'w') as f:
    f.write(content)
changed.append(f'控制台 updateDate -> {new_cutoff[:10]}')

print('\n'.join(changed))
