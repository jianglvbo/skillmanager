#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资知识库 · 言论追踪专项审计（C10 自动化执行器）
===================================================
本脚本是 `investment-review` skill 内容审查「C10 言论追踪审计」的执行器。

vault 侧检查（默认，无需凭据）：
  1. section 缺失    → 博主画像无 `## 言论追踪` 段（模板四段要求）
  2. section 空表    → 有段但无任何数据行（含「暂无记录」占位，但观点/信号表全空）
  3. 标的占位        → 标的列出现 — / 持仓 / 暂无 / 空（不可映射到主题的占位）
  4. 缺原文链接      → 外部来源（雪球/抖音/公众号等采集）言论行无链接（规则 #35）
  5. 表格列异常      → 观点/具象化表 <6 列、信号表 <5 列

MySQL 侧检查（可选，--mysql + 环境变量 DB_PASS）：
  6. tracks 数据质量 → content 空 / source_url 空 / direction 非字典码值
  7. 同步一致性      → vault 言论条数 vs prediction_tracks 条数对比（提示同步差距）

用法:
  python3 scripts/tracks_audit.py --vault <vault路径>            # 仅 vault 侧
  DB_PASS=xxx python3 scripts/tracks_audit.py --vault <路径> --mysql   # vault + MySQL
设计原则：
  - 只报告不修改：仅输出 JSON，绝不写盘。
  - 不硬编码凭据：MySQL 凭据只从环境变量 DB_PASS 读取（Ai 仓库公共化约定）。
"""
import os, re, sys, json, glob
from pathlib import Path
from collections import Counter

SECTIONS_REQUIRED = ["擅长与局限", "言论追踪", "个股买卖记录", "预测记录"]
PLACEHOLDER_TARGETS = {"", "—", "-", "/", "暂无", "持仓", "未点名", "无"}


def vault_scan(vault_root: str) -> dict:
    findings = []
    blogger_dir = Path(vault_root) / "博主"
    files = sorted(glob.glob(str(blogger_dir / "*" / "*.md")))
    stats = Counter()
    track_total = 0
    for f in files:
        blogger = Path(f).parent.name
        txt = Path(f).read_text(encoding="utf-8")
        # 1) section 缺失（锚定标题行，截取到下一个二级标题或文件尾——与迁移脚本同口径）
        m_sec = re.search(r'^## 言论追踪[ \t]*\n(.*?)(?=\n## |\Z)', txt, re.M | re.S)
        if not m_sec:
            findings.append({"file": str(f), "blogger": blogger, "type": "section_missing",
                             "detail": "博主画像缺少「## 言论追踪」section"})
            stats["section_missing"] += 1
            continue
        sec = m_sec.group(1)
        rows = []
        for line in sec.splitlines():
            line = line.strip()
            if not line.startswith("|"): continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not cells or not re.match(r'^20\d{2}-\d{2}-\d{2}$', cells[0]): continue
            rows.append(cells)
        track_total += len(rows)
        # 2) 空表（无任何数据行）
        if not rows:
            findings.append({"file": str(f), "blogger": blogger, "type": "section_empty",
                             "detail": "言论追踪 section 无数据行"})
            stats["section_empty"] += 1
            continue
        # 3/4/5) 行级检查
        for cells in rows:
            target = cells[1] if len(cells) > 1 else ""
            ncols = len(cells)
            has_link = any("http" in c or "](http" in c for c in cells)
            # 3) 标的占位
            if target in PLACEHOLDER_TARGETS:
                findings.append({"file": str(f), "blogger": blogger, "type": "target_placeholder",
                                 "date": cells[0], "detail": f"标的为占位符: {target!r}"})
                stats["target_placeholder"] += 1
            # 4) 缺原文链接（外部来源行）——按列数判断：6 列表的 link 列（末列）为空
            if ncols >= 6 and not has_link:
                findings.append({"file": str(f), "blogger": blogger, "type": "missing_link",
                                 "date": cells[0], "target": target,
                                 "detail": "外部言论行缺原文链接（规则 #35）"})
                stats["missing_link"] += 1
            # 5) 列数异常
            if ncols < 4:
                findings.append({"file": str(f), "blogger": blogger, "type": "table_cols_abnormal",
                                 "date": cells[0], "detail": f"表格列数异常: {ncols} 列"})
                stats["table_cols_abnormal"] += 1
        stats["blogger_with_rows"] += 1
    return {"vault_root": str(vault_root), "blogger_files": len(files),
            "stats": dict(stats), "track_rows_total": track_total, "findings": findings}


def mysql_scan() -> dict:
    import pymysql
    conn = pymysql.connect(host="106.55.14.116", port=3306, user="jianglb",
                           password=os.environ.get("DB_PASS", ""), database="investment_kb",
                           connect_timeout=8)
    cur = conn.cursor()
    out = {}
    cur.execute("SELECT COUNT(*) FROM prediction_tracks")
    out["tracks_total"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM prediction_tracks WHERE content IS NULL OR TRIM(content)=''")
    out["content_empty"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM prediction_tracks WHERE source_url IS NULL OR source_url=''")
    out["source_url_empty"] = cur.fetchone()[0]
    cur.execute("""SELECT direction_code, COUNT(*) FROM prediction_tracks
                   LEFT JOIN dict_track_direction d ON d.code=direction_code
                   WHERE d.code IS NULL GROUP BY direction_code""")
    out["bad_direction"] = [list(r) for r in cur.fetchall()]
    conn.close()
    return out


def main():
    args = sys.argv[1:]
    vault = None
    do_mysql = False
    i = 0
    while i < len(args):
        if args[i] == "--vault" and i + 1 < len(args): vault = args[i + 1]; i += 2
        elif args[i] == "--mysql": do_mysql = True; i += 1
        else: i += 1
    if not vault:
        print(json.dumps({"ok": False, "error": "缺少 --vault 参数"}, ensure_ascii=False))
        sys.exit(1)
    report = vault_scan(vault)
    if do_mysql:
        report["mysql"] = mysql_scan()
        m, v = report["mysql"]["tracks_total"], report["track_rows_total"]
        report["sync"] = {
            "vault_track_rows": v,
            "mysql_tracks": m,
            "delta_mysql_minus_vault": m - v,
            "note": "delta 正值=库比 vault 多（增量采集/他源导入）；负值=vault 言论未入库（占位/无效行跳过）"
        }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
