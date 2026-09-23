#!/usr/bin/env python3
# 存量雪球批次净化（2026-09-06《博主言论设计》§采集2 纯文本规则回溯）
# 场景：2026-08-26 及更早按旧 skill 采集的 帖子集 粗制品，含表情图片引用/空引用噪声。
# 作用：把旧批次清洗到"新纯文本规则"基线，供 #29 直接提炼；只删该删的，正文语义不动。
# 用法：python3 clean_legacy_batches.py [--dry-run] [--dir 工作区/粗制品路径]
import re, os, sys, glob

DEFAULT_DIR = "/Users/jianglb/Library/Mobile Documents/iCloud~md~obsidian/Documents/投资知识库/工作区/粗制品"
DRY = "--dry-run" in sys.argv
DIR = sys.argv[sys.argv.index("--dir") + 1] if "--dir" in sys.argv else DEFAULT_DIR

# 1) Obsidian 图片/表情嵌入：![[名]](url "[名]") 或 ![[名]]
RE_IMG_OBS = re.compile(r'!\[\[[^\]]*\]\]\([^)]*\)|!\[\[[^\]]*\]\]')
# 2) 标准 markdown 图片：![alt](url.图片后缀)
RE_IMG_MD = re.compile(r'!\[[^\]]*\]\([^)]*\.(?:png|jpe?g|gif|webp|bmp|svg)[^)]*\)', re.I)
# 3) 空引用行：> * [](javascript:;) / * [](javascript:;)
RE_JS_LINE = re.compile(r'^\s*>?\s*\*\s*\[\]\(javascript:;\)\s*$', re.M)
# 4) 行内残留 [](javascript:;)（行级处理已覆盖主要形态，此处兜底单行清理）
RE_JS_INLINE = re.compile(r'\s*\[\]\(javascript:;\)')

def clean(text):
    text = RE_IMG_OBS.sub('', text)
    text = RE_IMG_MD.sub('', text)
    text = RE_JS_LINE.sub('', text)
    text = RE_JS_INLINE.sub('', text)
    # 清理可能产生的连续空行（保留段落结构，最多折叠到 2 个连续空行）
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def main():
    files = sorted(glob.glob(os.path.join(DIR, "雪球采集-*.md")))
    tot_img = tot_js = tot_files = 0
    for f in files:
        s = open(f, encoding='utf-8').read()
        n_img = len(RE_IMG_OBS.findall(s)) + len(RE_IMG_MD.findall(s))
        n_js = len(RE_JS_LINE.findall(s))
        if n_img or n_js:
            tot_files += 1
            tot_img += n_img; tot_js += n_js
            if not DRY:
                open(f, 'w', encoding='utf-8').write(clean(s))
                print(f"  已净化: {os.path.basename(f)}（图片 {n_img} / 空引用 {n_js}）")
    print(f"{'[dry-run] ' if DRY else ''}扫描 {len(files)} 个批次；需处理 {tot_files} 个（表情图片引用 {tot_img} / 空引用 {tot_js}）")

if __name__ == '__main__':
    main()
