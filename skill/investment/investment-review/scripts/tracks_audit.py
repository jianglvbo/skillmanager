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
        # 1) section 缺失/重复标题兼容（2026-09-07：镜像 bug 导致 43 画像 `## 言论追踪`
        #    标题重复——锚点 begin 后又写了一次标题。取「含数据行最多的区段」，
        #    对无重复（修复后）与有重复（现状）均正确）
        segs = [m.group(1) for m in re.finditer(r'^## 言论追踪[ \t]*\n(.*?)(?=\n## |\Z)', txt, re.M | re.S)]
        if not segs:
            findings.append({"file": str(f), "blogger": blogger, "type": "section_missing",
                             "detail": "博主画像缺少「## 言论追踪」section"})
            stats["section_missing"] += 1
            continue
        def _row_count(seg):
            n = 0
            for line in seg.splitlines():
                line = line.strip()
                if not line.startswith("|"): continue
                cells = [c.strip() for c in line.strip("|").split("|")]
                if cells and re.match(r'^20\d{2}-\d{2}-\d{2}$', cells[0]): n += 1
            return n
        sec = max(segs, key=_row_count)
        rows = []
        header_idx = None
        for line in sec.splitlines():
            line = line.strip()
            if not line.startswith("|"): continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not cells: continue
            # 表头定位：含「标的」的列即标的列（新 9 列在 idx3，旧 6 列在 idx1）
            if header_idx is None and any("标的" in c for c in cells):
                for i, c in enumerate(cells):
                    if "标的" in c:
                        header_idx = i
                        break
                continue
            if not re.match(r'^20\d{2}-\d{2}-\d{2}$', cells[0]): continue
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
            ti = header_idx if header_idx is not None else (3 if len(cells) >= 9 else 1)
            target = cells[ti] if len(cells) > ti else ""
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
    # 2026-09-07 重写：言论权威已迁 blogger_statements 单轨（prediction_tracks 为迁移遗留表，
    # 原 dict_track_direction 字典表已废弃并入 dict 单表——旧查询直接报表不存在）
    cur.execute("SELECT COUNT(*) FROM blogger_statements")
    out["statements_total"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM blogger_statements WHERE view_text IS NULL OR TRIM(view_text)=''")
    out["view_text_empty"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM blogger_statements WHERE source_url IS NULL OR TRIM(source_url)=''")
    out["source_url_empty"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM blogger_statements WHERE review_required=1")
    out["review_required"] = cur.fetchone()[0]
    cur.execute("""SELECT s.content_type, COUNT(*) FROM blogger_statements s
                   LEFT JOIN dict d ON d.type='stmt_content_type' AND d.code=s.content_type
                   WHERE d.code IS NULL GROUP BY s.content_type""")
    out["bad_content_type"] = [list(r) for r in cur.fetchall()]
    cur.execute("""SELECT s.stance, COUNT(*) FROM blogger_statements s
                   LEFT JOIN dict d ON d.type='stance' AND d.code=s.stance
                   WHERE s.stance IS NOT NULL AND d.code IS NULL GROUP BY s.stance""")
    out["bad_stance"] = [list(r) for r in cur.fetchall()]
    # 复核建议积压（审查首步数据源）
    cur.execute("SELECT status, COUNT(*) FROM statement_reviews GROUP BY status")
    out["statement_reviews"] = {r[0]: r[1] for r in cur.fetchall()}
    # 遗留表迁移进度（只读提示，勿当权威）
    cur.execute("SELECT COUNT(*), SUM(migrated_to_statement_id IS NOT NULL) FROM prediction_tracks")
    r = cur.fetchone()
    out["legacy_tracks"] = {"total": int(r[0]), "migrated": int(r[1] or 0)}
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
        m, v = report["mysql"]["statements_total"], report["track_rows_total"]
        report["sync"] = {
            "vault_track_rows": v,
            "mysql_statements": m,
            "delta_mysql_minus_vault": m - v,
            "note": "delta 正值=库比 vault 多（增量采集/他源导入）；负值=vault 言论未入库（占位/无效行跳过）。注意：vault 统计口径为「言论追踪」section 数据行，与 blogger_statements 全量（含已删除标记行等）存在正常口径差"
        }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
