#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资知识库迁移脚本：vault + JSON → 服务器 MySQL (investment_kb)
原则：本地 vault 为绝对基准，全量重建派生表；冲突以 vault 为准。
用法: DB_PASS=xxx python3 scripts/migrate_to_mysql.py [--dry-run]
"""
import os, re, sys, json, time
from pathlib import Path
import pymysql

VAULT = Path(os.path.expanduser("~/Library/Mobile Documents/iCloud~md~obsidian/Documents/投资知识库"))
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB = {
    "host": "106.55.14.116", "port": 3306, "user": "jianglb",
    "password": os.environ.get("DB_PASS", ""), "database": "investment_kb",
    "charset": "utf8mb4", "autocommit": True,
}
DRY = "--dry-run" in sys.argv

EXCLUDE_DIRS = {".obsidian", ".trash", ".plugin_data", ".space", "附件", "__visit_history"}

LAYER_MAP = {"我的": "my", "博主": "blogger", "其他": "other", "宏观": "macro", "工作区": "workspace", "附件": "attachment"}
CAT_MAP = {"分析框架": "analysis_framework", "交易体系": "trading_system", "投资心态": "investment_mentality",
           "投资心得": "investment_insight", "个股": "stock", "行业": "industry", "宏观": "macro"}
TYPE_MAP = {"帖子": "post", "长文": "article", "视频": "video", "视频整理": "video_summary",
            "文章": "article", "链接": "link", "帖子集": "post_collection", "其他": "other"}
STATUS_MAP = {"分析中": "analyzing", "已提炼": "refined", "待提炼": "pending"}
PLATFORM_MAP = {"雪球": "xueqiu", "抖音": "douyin", "小红书": "xiaohongshu"}
RELATION_MAP = {"new": "new", "append": "append", "complement": "complement", "conflict_check": "conflict_check"}
CHECK_MAP = {"pass": "pass", "ok": "ok", "warn": "warn", "fail": "fail"}

def parse_fm(text):
    """解析 frontmatter（--- 之间 YAML 键值，仅处理标量/数组/布尔）"""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_]+):\s*(.*)$", line.strip())
        if not kv:
            continue
        k, v = kv.group(1), kv.group(2).strip()
        if v.startswith("[") and v.endswith("]"):
            fm[k] = [x.strip().strip('"\'') for x in v[1:-1].split(",") if x.strip()]
        elif v.lower() in ("true", "false"):
            fm[k] = v.lower() == "true"
        elif re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            fm[k] = v
        else:
            fm[k] = v.strip('"\'')
    return fm

def infer_layer(rel):
    top = rel.split("/")[0]
    return LAYER_MAP.get(top, "")

def infer_category(rel):
    for c in CAT_MAP:
        if ("/" + c + "/") in rel or rel.startswith(c + "/"):
            return CAT_MAP[c]
    return None

def scan_vault():
    """递归扫描 vault .md，返回文件记录列表"""
    files = []
    for p in sorted(VAULT.rglob("*.md")):
        rel = str(p.relative_to(VAULT)).replace(os.sep, "/")
        if any(part in EXCLUDE_DIRS for part in rel.split("/")[:3]):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            st = p.stat()
        except Exception as e:
            print("  skip", rel, e)
            continue
        fm = parse_fm(text)
        files.append({
            "rel": rel,
            "title": fm.get("title") or rel.rsplit("/", 1)[-1][:-3],
            "layer_code": infer_layer(rel),
            "category_code": infer_category(rel),
            "author": fm.get("author") or "",
            "type_code": TYPE_MAP.get(fm.get("type") or "", None),
            "status_code": STATUS_MAP.get(fm.get("status") or "", None),
            "star": 1 if fm.get("star") else 0,
            "size_bytes": st.st_size,
            "mtime": int(st.st_mtime * 1000),
            "create_date": fm.get("createDate") or None,
            "update_date": fm.get("updateDate") or None,
            "tags": fm.get("tags") or [],
        })
    return files

def load_json(name, default):
    p = DATA / name
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))

def main():
    print(f"== vault 扫描: {VAULT}")
    files = scan_vault()
    print(f"   扫描到 {len(files)} 个 .md")
    idx = load_json("index.json", {})
    bloggers_src = idx.get("bloggers", [])
    refine = load_json("refine.json", {}).get("records", [])
    review = load_json("review.json", {}).get("records", [])
    coarse = load_json("coarse.json", {})
    print(f"   bloggers={len(bloggers_src)} refine={len(refine)} review={len(review)} coarse={len(coarse)}")

    if DRY:
        print("[dry-run] 不写库"); return

    conn = pymysql.connect(**DB)
    cur = conn.cursor()

    # 1. 重置业务表（子表先删，外键约束）
    for t in ["file_tag_rel", "refine_targets", "review_checks", "files", "bloggers", "tags",
              "refine_records", "review_records", "coarse_records", "trash_records", "sync_state"]:
        cur.execute(f"DELETE FROM {t}")
    print("== 业务表已重置")

    # 2. bloggers
    blogger_id = {}
    for b in bloggers_src:
        cur.execute(
            "INSERT INTO bloggers (name, dir, alias, xueqiu_id, platform_code, special, summary, info_cutoff, file_count) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (b.get("name"), b.get("dir") or b.get("name"), b.get("alias"), b.get("xueqiuId"),
             PLATFORM_MAP.get(b.get("platform") or ("xueqiu" if b.get("isXueqiu") else ""), None),
             1 if b.get("special") else 0, b.get("summary"), b.get("infoCutoff"), b.get("fileCount") or 0))
        blogger_id[b["name"]] = cur.lastrowid
    print(f"== bloggers 插入 {len(blogger_id)}")

    # 3. tags + files + file_tag_rel
    tag_id = {}
    cur.execute("SELECT id, name FROM tags")  # 空表，跳过
    for f in files:
        # 博主层归属：rel 第二段 = 博主名
        bid = None
        parts = f["rel"].split("/")
        if f["layer_code"] == "blogger" and len(parts) >= 2:
            bid = blogger_id.get(parts[1])
        cur.execute(
            "INSERT INTO files (rel, title, layer_code, category_code, blogger_id, author, type_code, status_code, star, size_bytes, mtime, create_date, update_date) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (f["rel"], f["title"], f["layer_code"], f["category_code"], bid, f["author"] or None,
             f["type_code"], f["status_code"], f["star"], f["size_bytes"], f["mtime"],
             f["create_date"], f["update_date"]))
        fid = cur.lastrowid
        for tname in f["tags"]:
            if tname not in tag_id:
                cur.execute("INSERT INTO tags (name) VALUES (%s)", (tname,))
                tag_id[tname] = cur.lastrowid
            cur.execute("INSERT IGNORE INTO file_tag_rel (file_id, tag_id) VALUES (%s,%s)", (fid, tag_id[tname]))
    print(f"== files 插入 {len(files)} / tags {len(tag_id)}")

    # 4. refine_records + refine_targets
    n_rec, n_tgt = 0, 0
    for r in refine:
        steps = r.get("steps") or None
        ver = r.get("verify") or {}
        cur.execute(
            "INSERT INTO refine_records (source_url, source_type_code, from_rel, blogger_name, blogger_updated, reason, steps, verify_ok, verify_detail, verification_hints, at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (r.get("source"), "coarse" if r.get("sourceType") == "coarse" else "raw", r.get("from") or "",
             r.get("bloggerName"), 1 if r.get("bloggerUpdated") else 0, r.get("reason"),
             json.dumps(steps, ensure_ascii=False) if steps else None,
             (1 if ver.get("ok") else 0) if ver.get("ok") is not None else None, ver.get("detail"),
             json.dumps(r.get("verificationHints") or [], ensure_ascii=False), r.get("at") or 0))
        rid = cur.lastrowid
        n_rec += 1
        for t in r.get("targets") or []:
            rel_txt = t.get("path") or ""
            rel_code = "other"
            note = t.get("relation") or ""
            for k in ("new", "append", "complement"):
                if k in note:
                    rel_code = k
                    break
            if "矛盾" in note or "冲突" in note:
                rel_code = "conflict_check"
            # layer/category 原文 → 码值（兼容已映射值）
            raw_layer = t.get("layer") or ""
            layer_code = LAYER_MAP.get(raw_layer) or (raw_layer if raw_layer in LAYER_MAP.values() else "") or infer_layer(rel_txt) or "other"
            raw_cat = t.get("category") or ""
            cat_code = CAT_MAP.get(raw_cat) or (raw_cat if raw_cat in CAT_MAP.values() else None) or infer_category(rel_txt)
            cur.execute(
                "INSERT INTO refine_targets (record_id, target_rel, target_type_code, layer_code, relation_code, relation_note, category_code, tags, thinking, basis) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (rid, rel_txt, t.get("type") or "wiki", layer_code,
                 rel_code, note[:1000] or None, cat_code,
                 json.dumps(t.get("tags") or [], ensure_ascii=False),
                 json.dumps(t.get("thinking") or [], ensure_ascii=False) if t.get("thinking") else None,
                 t.get("basis") or None))
            n_tgt += 1
    print(f"== refine_records {n_rec} / refine_targets {n_tgt}")

    # 5. review_records + review_checks
    n_rev, n_chk = 0, 0
    for r in review:
        cur.execute(
            "INSERT INTO review_records (review_date, title, method, main_problems, summary, saved_at) VALUES (%s,%s,%s,%s,%s,%s)",
            (r.get("date"), r.get("title") or r.get("date"), r.get("method"),
             json.dumps(r.get("mainProblems") or [], ensure_ascii=False),
             r.get("summary"), r.get("savedAt") or 0))
        rid = cur.lastrowid
        n_rev += 1
        for c in r.get("checks") or []:
            cur.execute(
                "INSERT INTO review_checks (review_id, item_name, result, compare, status_code) VALUES (%s,%s,%s,%s,%s)",
                (rid, c.get("item"), str(c.get("result") or ""), str(c.get("compare") or ""),
                 CHECK_MAP.get(str(c.get("status")).lower(), "pass")))
            n_chk += 1
    print(f"== review_records {n_rev} / review_checks {n_chk}")

    # 6. coarse_records（历史 meta + vault 粗制品队列，vault 为准）
    n_coarse = 0
    # 6a. 历史 meta
    for rel, m in coarse.items():
        if not isinstance(m, dict):
            continue
        cur.execute(
            "INSERT INTO coarse_records (rel, status_code, score, score_reason, scored_at, title, processed_at, processed_to, output_preview) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (rel, m.get("status") or "pending", int(m["score"]) if m.get("score") is not None else None,
             m.get("scoreReason"), m.get("scoredAt"), m.get("title"), m.get("processedAt"),
             m.get("processedTo"), (m.get("outputPreview") or "")[:600]))
        n_coarse += 1
    # 6b. vault 粗制品队列（目录现存文件，vault 为准；meta 已处理的跳过）
    coarse_dir = VAULT / "工作区" / "粗制品"
    if coarse_dir.exists():
        for p in sorted(coarse_dir.glob("*.md")):
            rel = "工作区/粗制品/" + p.name
            if rel in coarse:
                continue  # 已有 meta 记录
            try:
                st = p.stat()
            except Exception:
                continue
            cur.execute(
                "INSERT INTO coarse_records (rel, status_code) VALUES (%s,'pending')",
                (rel,))
            n_coarse += 1
    print(f"== coarse_records {n_coarse}")

    # 7. trash_records + sync_state
    trash = load_json("trash.json", [])
    n_trash = 0
    for t in (trash if isinstance(trash, list) else []):
        cur.execute("INSERT IGNORE INTO trash_records (rel, status, deleted_at) VALUES (%s,%s,%s)",
                    (t.get("rel") or t.get("path") or "", "pending", t.get("at") or t.get("deletedAt")))
        n_trash += 1
    cur.execute("INSERT INTO sync_state (sync_key, sync_value) VALUES ('last_scan_mtime', %s) "
                "ON DUPLICATE KEY UPDATE sync_value=VALUES(sync_value)", (str(int(time.time() * 1000)),))
    print(f"== trash_records {n_trash} / sync_state 已写")

    # 汇总
    cur.execute("SELECT (SELECT COUNT(*) FROM files), (SELECT COUNT(*) FROM bloggers), (SELECT COUNT(*) FROM tags), (SELECT COUNT(*) FROM refine_records), (SELECT COUNT(*) FROM review_records), (SELECT COUNT(*) FROM coarse_records)")
    row = cur.fetchone()
    print(f"\n== 迁移完成：files={row[0]} bloggers={row[1]} tags={row[2]} refine={row[3]} review={row[4]} coarse={row[5]}")
    cur.close(); conn.close()

if __name__ == "__main__":
    main()
