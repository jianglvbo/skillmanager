#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obsidian 投资知识库 · 结构审查自动扫描器
========================================
本脚本是 `investment-review` skill「结构审查」维度的自动化执行器。

覆盖维度（与 SKILL.md 结构审查一一对应）：
  - 归类正确性      → template_for() / unclassified
  - frontmatter 完整性 → REQUIRED / missing_fields（含 updateDate 必填）
  - 引号有效性      → check_quoting()（全局规则 #21）
  - wikilink 有效性 → resolve_link()（正文 + frontmatter `source` 字段）
  - 脚注格式        → empty_footnote_placeholder（空 ## 脚注 占位，规则 #20）
  - 标签匹配        → tag_issues（博主禁行业标签、标签禁 emoji）
  - 扩展检查        → 禁用 `## 来源` 段（规则 #23）、source 为 URL（应转 wikilink 数组）、空壳 junk 检测

设计原则
--------
- 只报告不修改：仅输出 JSON + 计数，绝不写盘（符合 skill「绝不直接修改文件」原则）。
- 规则镜像：下方 REQUIRED / EXPECTED_SECTIONS / SCOPE / template_for() 镜像自
  `investment-framework` 的 framework-rules.md 与 9 个模板文件。
  ⚠️ 若框架规则或模板调整（新增必填字段、改段落名），须同步更新本文件对应常量。
- 框架结构驱动：除 VAULT 路径外，不硬编码任何具体博主名 / 文件名 / URL。

用法
----
  python3 vault_review.py --vault "<vault路径>" [--out "<输出目录>"]
  # 不设 --vault 时：优先读环境变量 VAULT，否则退回 iCloud 默认路径
  # 不设 --out  时：结果输出到当前工作目录，文件名 vault_review_result.json

依赖：Python 3.8+，仅标准库（os/re/json/argparse）。
"""
import os, re, json, argparse

DEFAULT_VAULT = os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/投资知识库"
)
ap = argparse.ArgumentParser(description="Obsidian 投资知识库结构审查扫描器")
ap.add_argument("--vault", default=os.environ.get("VAULT", DEFAULT_VAULT),
                help="vault 根目录路径（默认环境变量 VAULT 或 iCloud 默认路径）")
ap.add_argument("--out", default=os.getcwd(),
                help="结果 JSON 输出目录（默认当前工作目录）")
_args = ap.parse_args()
VAULT = os.path.expanduser(_args.vault)
OUT = _args.out
if not os.path.isdir(VAULT):
    ap.error(f"vault 路径不存在: {VAULT}")
os.makedirs(OUT, exist_ok=True)

# 框架归属层（镜像 investment-framework 路径表；改框架时同步）
SCOPE = ["我的", "博主", "其他", "宏观"]

# emoji：保留彩色表情块，排除箭头/符号箭头（→ ← ↑ ↓ ➡ 等，属合法标题字符）
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF"
    "\U00002600-\U000026FF"   # ☀⚠✅ 等杂项符号（保留）
    "\U0001F1E6-\U0001F1FF"   # 区域指示符
    "\U0001F900-\U0001F9FF"
    "\U00002700-\U000027BF]+" # 装饰符号 ✅❌（保留）
)
def has_emoji(s):
    return bool(EMOJI_RE.search(s))
def strip_emoji(s):
    return EMOJI_RE.sub("", s)
def norm_path(p):
    return strip_emoji(p).replace('"', "").replace("'", "").strip()

# ---------- 索引 ----------
index=set(); index_norm={}; index_lower={}; basename_map={}
for root,dirs,files in os.walk(VAULT):
    rel_root=os.path.relpath(root,VAULT); parts=rel_root.split("/")
    if parts[0] in (".obsidian",".trash",".space",".smart-env",".makemd","附件"):
        dirs[:]=[]; continue
    for f in files:
        if not f.endswith(".md"): continue
        link=os.path.relpath(os.path.join(root,f),VAULT)[:-3]
        index.add(link)
        index_norm.setdefault(norm_path(link),set()).add(link)
        index_lower.setdefault(link.lower(),set()).add(link)
        basename_map.setdefault(os.path.basename(link),set()).add(link)

def resolve_link(target):
    t=target.split("|")[0].split("#")[0].strip()
    if t in index: return ("ok","")
    if norm_path(t) in index_norm:
        return ("emoji_or_quote","实际: "+", ".join(sorted(index_norm[norm_path(t)])))
    if t.lower() in index_lower:
        return ("case","实际: "+", ".join(sorted(index_lower[t.lower()])))
    bn=t.split("/")[-1]
    if bn in basename_map:
        return ("short_path","实际: "+", ".join(sorted(basename_map[bn])))
    return ("broken","")

# ---------- frontmatter ----------
def parse_frontmatter(text):
    if not text.startswith("---"): return ({},"",False,None)
    m=re.match(r"^---\s*\n(.*?)\n---\s*\n?",text,re.DOTALL)
    if not m: return ({},"",False,"frontmatter 未闭合")
    raw=m.group(1); fm={}; lines=raw.split("\n"); i=0; n=len(lines)
    while i<n:
        line=lines[i]
        if not line.strip() or line.strip().startswith("#"): i+=1; continue
        m2=re.match(r"^([A-Za-z_\u4e00-\u9fff][\w\u4e00-\u9fff]*):\s*(.*)$",line)
        if not m2: i+=1; continue
        key=m2.group(1); val=m2.group(2).strip()
        if val=="":
            items=[]; j=i+1
            while j<n and re.match(r"^\s*-\s+",lines[j]):
                items.append(re.match(r"^\s*-\s+(.*)$",lines[j]).group(1).strip()); j+=1
            fm[key]=items if items else ""
            i=j; continue
        if val.startswith("[") and val.endswith("]"):
            inner=val[1:-1].strip()
            fm[key]=[] if inner=="" else [x.strip().strip('"').strip("'") for x in inner.split(",")]
            i+=1; continue
        fm[key]=val; i+=1
    return (fm,raw,True,None)

# 模板推断（镜像 investment-framework 路径表 + 六大分类）
def template_for(rel,fm):
    if rel.startswith("博主/"):
        for kw,tp in [("分析框架/方法论","方法论"),("分析框架/分析档案","分析档案"),
                     ("交易体系","交易体系"),("投资心态","投资心态"),("投资心得","投资心得"),
                     ("行业","行业"),("个股","个股"),("宏观","宏观")]:
            if kw in rel: return tp
        return "博主画像"
    if rel.startswith("宏观/"): return "宏观"
    if rel.startswith("我的/") or rel.startswith("其他/"):
        if "分析框架" in rel: return "分析档案" if "标的" in fm else "方法论"
        for kw,tp in [("交易体系","交易体系"),("投资心态","投资心态"),("投资心得","投资心得"),
                     ("行业","行业"),("个股","个股")]:
            if kw in rel: return tp
    return "未知"

# 必填字段（镜像模板 frontmatter 硬约束；改模板时同步）
REQUIRED={
 "博主画像":["title","platform","createDate","updateDate","tags"],
 "宏观":["title","event","时效状态","时间范围","createDate","updateDate","tags","source"],
 "分析档案":["title","标的","createDate","updateDate","status","tags","source"],
}
for t in ["方法论","交易体系","投资心态","投资心得","行业","个股"]:
    REQUIRED[t]=["title","createDate","updateDate","tags","source"]

# 期望段落（镜像模板 body 最小必要结构；改模板时同步）
EXPECTED_SECTIONS={
 "博主画像":["博主画像","学到的东西"],
 "方法论":["适用场景","方法步骤","关键指标","案例"],
 "分析档案":["使用的方法论","核心结论","分析过程","估值判断","决策","结果跟踪"],
 "交易体系":["规则","适用条件"],
 "投资心态":["场景","问题","根因","应对策略"],
 "投资心得":["背景","经验教训","借鉴意义"],
 "行业":["行业概况","关键数据"],
 "个股":["基本信息","分析汇总"],
 "宏观":["事件概述","影响分析","传导路径"],
}
WL_RE=re.compile(r"(!?)\[\[([^\]]+)\]\]")
def extract_wikilinks(body): return [m.group(2) for m in WL_RE.finditer(body)]
def check_quoting(raw):
    issues=[]
    for line in raw.split("\n"):
        m=re.match(r'^([\w\u4e00-\u9fff]+):\s*"(.*)"\s*$',line)
        if m and re.search(r'(?<!\\)"',m.group(2)): issues.append((m.group(1),line.strip()))
        m2=re.match(r"^([\w\u4e00-\u9fff]+):\s*'(.*)'\s*$",line)
        if m2 and re.search(r"(?<!\\)'",m2.group(2)): issues.append((m2.group(1),line.strip()))
    return issues

# ---------- 扫描 ----------
F={"no_fm":[],"fm_error":[],"missing_fields":[],"quoting":[],"tag_issues":[],
   "empty_footnote_placeholder":[],"forbidden_source_section":[],"blogger_has_source":[],
   "missing_core_sections":[],"wikilink_issues":[],"unclassified":[],"macro_template_mismatch":[],
   "source_as_url":[],"junk_files":[]}
summary={"total":0,"by_template":{}}

files=[]
for scope in SCOPE:
    for root,dirs,fs in os.walk(os.path.join(VAULT,scope)):
        rr=os.path.relpath(root,VAULT)
        if rr.split("/")[0] in (".trash",".space",".smart-env",".makemd"): dirs[:]=[]; continue
        for f in fs:
            if f.endswith(".md"): files.append(os.path.relpath(os.path.join(root,f),VAULT))

for rel in sorted(files):
    summary["total"]+=1
    full=os.path.join(VAULT,rel)
    text=open(full,encoding="utf-8").read()
    fm,raw_fm,has_fm,err=parse_frontmatter(text)
    if not has_fm: F["no_fm"].append(rel); continue
    if err: F["fm_error"].append((rel,err))
    tpl=template_for(rel,fm)
    summary["by_template"][tpl]=summary["by_template"].get(tpl,0)+1
    if tpl=="未知":
        F["unclassified"].append(rel); continue

    # 未归类（不在六大分类文件夹内，且非博主画像）
    parts=rel.split("/")
    if (rel.startswith("我的/") or rel.startswith("其他/")) and len(parts)<=2:
        F["unclassified"].append(rel)

    # 必填字段
    miss=[k for k in REQUIRED[tpl] if k not in fm or fm[k] in ("",None,[])]
    if miss:
        if tpl=="宏观" and set(miss)=={"event","时效状态","时间范围"}:
            F["macro_template_mismatch"].append((rel,"通用宏观框架使用了宏观事件模板（缺 event/时效状态/时间范围）"))
        else:
            F["missing_fields"].append((rel,tpl,miss))

    # 引号
    for k,l in check_quoting(raw_fm): F["quoting"].append((rel,k,l))

    # 标签
    tags=fm.get("tags",[])
    if isinstance(tags,list):
        if len(tags)==0 and tpl!="博主画像":
            F["tag_issues"].append((rel,"tags 为空"))
        if tpl=="博主画像":
            bad=[tg for tg in tags if str(tg).startswith("行业/")]
            if bad: F["tag_issues"].append((rel,"博主带行业标签(违规): "+", ".join(map(str,bad))))
        for tg in tags:
            if has_emoji(str(tg)): F["tag_issues"].append((rel,"标签含emoji: "+str(tg)))

    # 段落
    h2=[h.strip() for h in re.findall(r"^##\s+(.+)$",text,re.MULTILINE)]
    # 空 ## 脚注 占位（规则#20 禁止）
    if "脚注" in h2:
        m=re.search(r"^##\s+脚注\s*$(.*?)(?=^##\s|\Z)",text,re.MULTILINE|re.DOTALL)
        if m and not m.group(1).strip():
            F["empty_footnote_placeholder"].append(rel)
    # 禁止 ## 来源（精确匹配标题，避免误伤"## 数据来源"等合法标题）
    if re.search(r"^##\s+来源\s*$", text, re.MULTILINE):
        F["forbidden_source_section"].append((rel,h2))
    # 博主画像
    if tpl=="博主画像":
        if "source" in fm: F["blogger_has_source"].append((rel,"博主画像不应含 source"))
        if "学到的东西" not in h2: F["missing_core_sections"].append((rel,"博主画像",["学到的东西"]))
    # 缺核心段（非脚注）
    miss_sec=[s for s in EXPECTED_SECTIONS.get(tpl,[]) if s not in h2]
    if miss_sec and tpl!="博主画像":
        F["missing_core_sections"].append((rel,tpl,miss_sec))

    # source 为 URL（非 wikilink）
    src=fm.get("source")
    if isinstance(src,str) and src.startswith("http"):
        F["source_as_url"].append((rel,src))
    # wikilink
    wl_sources=[]
    if isinstance(src,list):
        for s in src: wl_sources.extend(extract_wikilinks(str(s)))
    elif isinstance(src,str): wl_sources.extend(extract_wikilinks(src))
    for wl in extract_wikilinks(text)+wl_sources:
        target=wl.split("|")[0].split("#")[0].strip()
        if not target: continue
        if has_emoji(target):
            F["wikilink_issues"].append((rel,wl,"wikilink含emoji","")); continue
        st,sug=resolve_link(target)
        if st=="broken": F["wikilink_issues"].append((rel,wl,"失效链接",sug))
        elif st=="emoji_or_quote": F["wikilink_issues"].append((rel,wl,"路径含emoji/引号不匹配",sug))
        elif st=="case": F["wikilink_issues"].append((rel,wl,"大小写不匹配",sug))
        elif st=="short_path": F["wikilink_issues"].append((rel,wl,"路径不完整(仅basename)",sug))

# junk：缺全部字段的空壳
for rel,tpl,miss in F["missing_fields"][:]:
    if set(miss)=={"title","event","时效状态","时间范围","createDate","updateDate","tags","source"}:
        F["junk_files"].append(rel)

out_path=os.path.join(OUT,"vault_review_result.json")
json.dump({"summary":summary,"findings":F},open(out_path,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(f"vault: {VAULT}")
print(f"结果已写入: {out_path}")
print("总文件:",summary["total"],"| 模板分布:",json.dumps(summary["by_template"],ensure_ascii=False))
print("\n=== 问题计数 ===")
for k,v in F.items(): print(f"{k}: {len(v)}")
