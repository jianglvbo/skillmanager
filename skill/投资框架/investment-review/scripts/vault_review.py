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
  - 脚注格式        → legacy_footnote_heading（遗留 ## 脚注 标题，新格式改用 --- 分隔线，规则 #20）
  - 标签匹配        → tag_issues（博主禁行业标签、标签禁 emoji）
  - 扩展检查        → 禁用 `## 来源` 段（规则 #23）、source 为 URL（应转 wikilink 数组）、空壳 junk 检测
  - 博主画像三表    → blogger_table_no_link_col（言论追踪/个股买卖/预测 三表是否都含「原文链接」列）、
                     blogger_empty_link_row（三表是否存在空原文链接行 `-`/空，规则 #35）
  - 个股代码        → stock_code_missing（规则 #28：个股文件名须含 (代码)）
  - 博主层登记校验  → blogger_not_registered（规则 #12：博主文件夹名须在博主控制台登记）

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

# 博主控制台登记名（镜像 framework-rules #12；改控制台时同步）
# 用于博主层登记校验：博主文件夹名必须在控制台登记，否则属误挂（应迁移其他层）
def load_blogger_console():
    p = os.path.join(VAULT, "工作区", "博主控制台.md")
    names = set()
    if not os.path.isfile(p):
        return names
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 2:
            nm = cells[1]
            if nm and nm not in ("博主名", "") and not set(nm) <= set("- "):
                names.add(nm)
    return names
BLOGGERS = load_blogger_console()

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
        # 直接放在 博主/*/分析框架/ 下（无 方法论/分析档案 子目录）的条目：
        # 上面带子目录的关键词都不匹配，须在此兜底归类，避免误判为博主画像
        if "分析框架" in rel: return "分析档案" if "标的" in fm else "方法论"
        return "博主画像"
    if rel.startswith("宏观/"):
        # 顶层宏观通用框架（无 event/时效状态/时间范围）用标准 6 字段；
        # 仅「归属层/宏观/」下的具体事件分析才带三事件字段（事件型）
        return "宏观" if ("event" in fm or "时效状态" in fm or "时间范围" in fm) else "宏观通用"
    if rel.startswith("我的/") or rel.startswith("其他/"):
        if "分析框架" in rel: return "分析档案" if "标的" in fm else "方法论"
        for kw,tp in [("交易体系","交易体系"),("投资心态","投资心态"),("投资心得","投资心得"),
                     ("行业","行业"),("个股","个股")]:
            if kw in rel: return tp
    return "未知"

# 必填字段（镜像模板 frontmatter 硬约束；改模板时同步）
# 注意：博主画像自身即博主，无 author 字段
REQUIRED={
 "博主画像":["title","platform","platform_id","special_following","createDate","updateDate"],
 "宏观":["title","event","时效状态","时间范围","createDate","updateDate","author","tags","source"],
 "分析档案":["title","标的","createDate","updateDate","author","status","tags","source"],
}
for t in ["方法论","交易体系","投资心态","投资心得","行业","个股"]:
    REQUIRED[t]=["title","createDate","updateDate","author","tags","source"]
REQUIRED["宏观通用"]=["title","createDate","updateDate","author","tags","source"]  # 顶层宏观通用框架，无 event 三字段

# canonical 字段顺序（镜像 framework-rules #27；改模板时同步）
# 用于检测字段顺序漂移——仅比对 canonical 中实际存在的字段
CANON={
 "方法论":["title","createDate","updateDate","author","tags","source"],
 "交易体系":["title","createDate","updateDate","author","tags","source"],
 "投资心态":["title","createDate","updateDate","author","tags","source"],
 "投资心得":["title","createDate","updateDate","author","tags","source"],
 "行业":["title","createDate","updateDate","author","tags","source"],
 "个股":["title","createDate","updateDate","author","tags","source"],
 "分析档案":["title","标的","createDate","updateDate","author","status","tags","source"],
 "宏观":["title","event","时效状态","时间范围","createDate","updateDate","author","tags","source"],
 "宏观通用":["title","createDate","updateDate","author","tags","source"],
 "博主画像":["title","platform","platform_id","special_following","summary","info_cutoff","createDate","updateDate"],  # 笔记属性 8 字段 canonical 顺序（含 platform_id，见规则 #36）
}

# 期望段落（镜像模板 body 最小必要结构；改模板时同步）
EXPECTED_SECTIONS={
 "博主画像":["博主画像"],
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

# 博主画像三表「原文链接」检查（framework-rules #35）
# 解析 markdown 表格，按最近 ## 标题归类（言论追踪 / 个股买卖记录 / 预测记录）
def parse_blogger_tables(text):
    tables=[]  # (category, header, rows)
    lines=text.split("\n")
    last_h2=None
    i=0
    while i<len(lines):
        line=lines[i]
        m2=re.match(r'^##\s+(.*)',line)
        if m2: last_h2=m2.group(1).strip()
        if line.strip().startswith("|") and i+1<len(lines) and re.match(r'^\s*\|[\s:|-]+\|\s*$',lines[i+1]):
            hdr=[c.strip() for c in line.strip().strip("|").split("|")]
            cat=None
            if last_h2 and "言论追踪" in last_h2: cat="言论追踪"
            elif last_h2 and "个股买卖记录" in last_h2: cat="个股买卖记录"
            elif last_h2 and "预测记录" in last_h2: cat="预测记录"
            rows=[]
            j=i+2
            while j<len(lines) and lines[j].strip().startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j+=1
            if cat: tables.append((cat,hdr,rows))
            i=j
            continue
        i+=1
    return tables

EMPTY_LINK={"","—","-","无"}
def check_blogger_tables(text,rel):
    no_col=[]; empty_row=[]
    for cat,hdr,rows in parse_blogger_tables(text):
        if "原文链接" not in hdr:
            no_col.append((rel,cat)); continue
        li=hdr.index("原文链接")
        for r in rows:
            if li<len(r) and r[li] in EMPTY_LINK:
                ctx=r[0] if r else ""
                empty_row.append((rel,cat,ctx))
    return no_col,empty_row

# ---------- 扫描 ----------
F={"no_fm":[],"fm_error":[],"missing_fields":[],"quoting":[],"tag_issues":[],
   "legacy_footnote_heading":[],"forbidden_source_section":[],"blogger_has_source":[],
   "missing_core_sections":[],"wikilink_issues":[],"unclassified":[],"macro_template_mismatch":[],
   "source_as_invalid":[],"stray_date":[],"field_order":[],"junk_files":[],
   "stock_code_missing":[],"blogger_not_registered":[],
   "blogger_table_no_link_col":[],"blogger_empty_link_row":[],
   "info_cutoff_mismatch":[],
   "footnote_links_workspace":[]}
summary={"total":0,"by_template":{}}

files=[]
for scope in SCOPE:
    for root,dirs,fs in os.walk(os.path.join(VAULT,scope)):
        rr=os.path.relpath(root,VAULT)
        # 排除隐藏/系统目录（任意层级，含子层 .space/templates 等）
        dirs[:]=[d for d in dirs if d not in (".trash",".space",".smart-env",".makemd")]
        if rr.split("/")[0] in (".trash",".space",".smart-env",".makemd"): continue
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

    # 流浪 date（层间边界硬约束 framework-rules #27：条目层禁止 date）
    if "date" in fm:
        F["stray_date"].append((rel,"条目层含禁止字段 date（应为原始资源层发布日）"))

    # 字段顺序 canonical（framework-rules #27）
    canon=CANON.get(tpl)
    if canon:
        expected=[k for k in canon if k in fm]
        actual=[k for k in fm.keys() if k in canon]
        if actual!=expected:
            F["field_order"].append((rel,tpl,actual))

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
    # 遗留 ## 脚注 标题（规则#20：新格式改用 --- 分隔线，不允许 ## 脚注 标题）
    if "脚注" in h2:
        F["legacy_footnote_heading"].append(rel)
    # 禁止 ## 来源（精确匹配标题，避免误伤"## 数据来源"等合法标题）
    if re.search(r"^##\s+来源\s*$", text, re.MULTILINE):
        F["forbidden_source_section"].append((rel,h2))
    # 博主画像
    if tpl=="博主画像":
        if "source" in fm: F["blogger_has_source"].append((rel,"博主画像不应含 source"))
        if "博主画像" not in h2: F["missing_core_sections"].append((rel,"博主画像",["博主画像"]))
        # 三表「原文链接」检查（framework-rules #35）
        nc,er=check_blogger_tables(text,rel)
        F["blogger_table_no_link_col"].extend(nc)
        F["blogger_empty_link_row"].extend(er)
    # 缺核心段（非脚注）
    miss_sec=[s for s in EXPECTED_SECTIONS.get(tpl,[]) if s not in h2]
    if miss_sec and tpl!="博主画像":
        F["missing_core_sections"].append((rel,tpl,miss_sec))

    # source 形态校验（framework-rules #23：内部→wikilink，外部→[标题](URL)，二选一）
    src=fm.get("source")
    def source_shape_invalid(item):
        """返回 None=合法；否则返回原因字符串"""
        s=str(item).strip()
        # 剥掉 YAML 引号（单双引号）
        if len(s)>=2 and s[0] in ('"',"'") and s[-1]==s[0]:
            s=s[1:-1].strip()
        # 合法形态1：内部 wikilink
        if s.startswith("[[") and s.endswith("]]"):
            return None
        # 合法形态2：外部 markdown 链接 [标题](URL)
        if re.match(r'^\[[^\]\n]+\]\(https?://[^)\s]+\)$', s):
            return None
        # 裸 URL（无标题）→ 违规
        if re.match(r'^https?://', s):
            return "裸URL（应改为 [标题](URL) 或 wikilink，见 #23）"
        # 其他形态
        return f"非法source形态（见 #23）：{s[:40]}"
    if isinstance(src,list):
        for s in src:
            reason=source_shape_invalid(s)
            if reason: F["source_as_invalid"].append((rel,str(s)[:60],reason))
    elif isinstance(src,str):
        reason=source_shape_invalid(src)
        if reason: F["source_as_invalid"].append((rel,src[:60],reason))
    # wikilink 可追溯性
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

    # 脚注 wikilink 目标仅限 wiki 产物（footnote-taxonomy 禁止行为 #6）：仅检查脚注定义行
    # （[^x-N]: ... 格式，位于文末 --- 脚注区）中的 wikilink，禁止指向 工作区/ 下任何文件
    for line in text.splitlines():
        if re.match(r"^\[\^[a-z]*-[0-9]+\]:", line.strip()):
            for wl in extract_wikilinks(line):
                target=wl.split("|")[0].split("#")[0].strip()
                if target.startswith("工作区/"):
                    F["footnote_links_workspace"].append((rel, wl, "脚注指向工作区文件（仅限wiki产物间引用，见 footnote-taxonomy 禁止行为#6）"))

    # 个股代码（framework-rules #28）：文件名须含 {名称}({代码})，代码后可附加描述后缀
    if tpl=="个股":
        bn=os.path.basename(rel)[:-3]
        if not re.search(r"\([A-Za-z0-9]{4,6}\)",bn):
            F["stock_code_missing"].append((rel,"个股文件名缺股票代码，应为 {名称}({代码})，见规则#28"))

    # 博主层作者登记校验（framework-rules #12）：博主文件夹名须在博主控制台登记
    if rel.startswith("博主/") and BLOGGERS:
        bname=parts[1]
        if bname not in BLOGGERS:
            F["blogger_not_registered"].append((rel,bname))

# junk：缺全部字段的空壳
for rel,tpl,miss in F["missing_fields"][:]:
    if set(miss)=={"title","event","时效状态","时间范围","createDate","updateDate","tags","source"}:
        F["junk_files"].append(rel)

# 信息截止一致性校验：博主控制台「信息截止」列 vs 画像 info_cutoff
def load_console_cutoffs():
    p = os.path.join(VAULT, "工作区", "博主控制台.md")
    cutoffs = {}
    if not os.path.isfile(p):
        return cutoffs
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 7 and cells[0] not in ("编号", "") and not set(cells[0]) <= set("- :"):
            name = cells[1]
            cutoff = cells[6]  # 第7列 = 信息截止
            if name and cutoff and re.match(r"\d{4}-\d{2}-\d{2}", cutoff):
                cutoffs[name] = cutoff
    return cutoffs

CONSOLE_CUTOFFS = load_console_cutoffs()
if CONSOLE_CUTOFFS:
    for rel in sorted(files):
        if not rel.startswith("博主/"):
            continue
        parts_r = rel.split("/")
        if len(parts_r) < 3 or parts_r[2] != parts_r[1] + ".md":
            continue  # 只看 博主/{name}/{name}.md
        bname = parts_r[1]
        if bname not in CONSOLE_CUTOFFS:
            continue
        full = os.path.join(VAULT, rel)
        text = open(full, encoding="utf-8").read()
        m = re.search(r"info_cutoff:\s*(\d{4}-\d{2}-\d{2})", text)
        profile_cutoff = m.group(1) if m else ""
        console_cutoff = CONSOLE_CUTOFFS[bname]
        if profile_cutoff and console_cutoff and profile_cutoff != console_cutoff:
            F["info_cutoff_mismatch"].append((rel, f"画像={profile_cutoff} vs 控制台={console_cutoff}"))

out_path=os.path.join(OUT,"vault_review_result.json")
json.dump({"summary":summary,"findings":F},open(out_path,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(f"vault: {VAULT}")
print(f"结果已写入: {out_path}")
print("总文件:",summary["total"],"| 模板分布:",json.dumps(summary["by_template"],ensure_ascii=False))
print("\n=== 问题计数 ===")
for k,v in F.items(): print(f"{k}: {len(v)}")
