#!/usr/bin/env python3
"""批量从 Markdown 生成规范排版的本地 .docx（走本地 editor_sdk / tencent-local-office-edit 通道）。

用法：
    python3 build_docx.py jobs.json

jobs.json：
{
  "header_fill": "F1F5F9",                  # 表头底色，默认 F1F5F9
  "skip_table_indexes": [0],                # 不参与着色的表（如封面信息表）
  "label_table_labels": ["问题陈述"],        # 首格文字命中则整表着色、首列居中、其余列左对齐
  "default_text_style": {"font_family": "宋体", "font_size": 12},
  "default_paragraph_style": {"line_spacing": 1.5, "line_spacing_rule": 1},
  "page_style": {"page_width": 595.3, "page_height": 841.9,
                 "top_margin": 72, "bottom_margin": 72, "left_margin": 72, "right_margin": 72},
  "title": {"match": "智  能  体", "font_family": "Arial", "font_size": 28,
            "color": "1F2937", "spacing_after": 38},
  "jobs": [{"markdown": "/abs/a.md", "output": "/abs/a.docx"}]
}

约定：
- 每个作业都新建空白文档（不复用 file_id），避免内容重复插入
- 表头样式是硬门禁：非封面表必须完成着色，否则末行打印 WARN
"""
import json
import os
import re
import subprocess
import sys
import time

SKILL_DIR = os.environ.get(
    "LOCAL_OFFICE_EDIT_DIR",
    "/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/plugins/"
    "workbuddy-builtin/skills/tencent-local-office-edit",
)
DEFAULT_FILL = "F1F5F9"


def call(tool, **kw):
    """调用 edsdk.py；返回 dict（JSON 回包）或 str（文本回包）。"""
    args = ["python3", "edsdk.py", "call", tool]
    nested = {}
    for k, v in kw.items():
        # bool / None / 容器走 --json，避免 True 被当字符串（JSON 只认小写 true）
        if isinstance(v, (dict, list, bool)) or v is None:
            nested[k] = v
        else:
            args.append(f"{k}={v}")
    if nested:
        args += ["--json", json.dumps(nested, ensure_ascii=False)]
    r = subprocess.run(args, cwd=SKILL_DIR, capture_output=True, text=True)
    out = (r.stdout or "").strip()
    if r.returncode != 0 or out.startswith('{"ok": false'):
        raise RuntimeError(f"{tool} 调用失败: {out} {r.stderr.strip()}")
    if out.startswith(("{", "[")):
        return json.loads(out)
    m = re.search(r"file_id=([^\s,]+)", out)  # create_doc 返回自然语言文本
    return m.group(1) if m else out


def style_title(fid, spec):
    """封面标题：居中 + 字体字号 + 段后间距。

    注意：结构预览会把空白归一化并截断（标题类节点通常只回 ~4 字），
    因此 match 必须是短短语（如「智能」）；匹配失败时回退到首个非空文本节点。
    """
    if not spec:
        return False
    nodes = call("doc_resolve_document_structure", file_id=fid, limit=5).get("nodes", [])
    norm = lambda s: re.sub(r"\s+", "", s or "")
    target = norm(spec.get("match", ""))
    hit = None
    for n in nodes:
        if n.get("type") in ("Table",):
            continue
        if target and norm(n.get("text_preview")).startswith(target):
            hit = n
            break
    if hit is None and spec.get("fallback_first", True):
        for n in nodes:
            if n.get("type") in ("Heading", "Title", "Paragraph") and n.get("end_index", 0) > n.get("start_index", 0):
                hit = n
                break
    if hit is None:
        return False
    rng = [{"begin": hit["start_index"], "end": hit["end_index"]}]
    call("doc_modify_paragraph", file_id=fid, ranges=rng,
         jc="center", spacing_after=spec.get("spacing_after", 38))
    call("doc_update_text_property", file_id=fid, ranges=rng,
         font_family=spec.get("font_family", "Arial"),
         font_size=spec.get("font_size", 28),
         bold=True, color=spec.get("color", "1F2937"))
    return True


def style_tables(fid, cfg):
    """表头着色（硬门禁）；标签表整表着色。返回 (已着色表数, 命中表数)。"""
    fill = cfg.get("header_fill", DEFAULT_FILL)
    skip = set(cfg.get("skip_table_indexes", []))
    labels = set(cfg.get("label_table_labels", []))
    tables = call("doc_list_tables", file_id=fid)["tables"]
    shaded = eligible = 0
    for t in tables:
        if t["index"] in skip:
            continue
        eligible += 1
        first = (t["first_row_texts"] or [""])[0]
        rows, cols = t["row_count"], t["col_count"]
        if first in labels:  # 标签表：整表着色，首列居中、其余列左对齐
            cells = [{"row": r, "col": 1, "horizontal_align": "center"} for r in range(1, rows + 1)]
            cells += [{"row": r, "col": c, "horizontal_align": "left"}
                      for r in range(1, rows + 1) for c in range(2, cols + 1)]
            call("doc_set_table_cells", file_id=fid, table_id=t["table_id"], cells=cells,
                 common_cell_properties={"property": {"background_color": fill}})
        else:  # 普通表：仅表头行着色 + 居中
            call("doc_set_table_cells", file_id=fid, table_id=t["table_id"],
                 cells=[{"row": 1, "col": c} for c in range(1, cols + 1)],
                 common_cell_properties={"property": {"background_color": fill},
                                         "horizontal_align": "center"})
        shaded += 1
    return shaded, eligible


def create_blank():
    """新建空白文档，返回 (file_id, file_path)。

    create_doc 的回包形态不稳定：有时是自然语言文本（含 file_id=/file_path=），
    有时只回一个裸 id。两种都要认。
    """
    out = call("create_doc")
    fid = re.search(r"file_id=([^\s,]+)", out)
    path = re.search(r"file_path=([^\s,]+)", out)
    if fid:
        return fid.group(1), (path.group(1) if path else None)
    if re.fullmatch(r"[\w.\-]+", out):  # 裸 id 形态
        return out, None
    raise RuntimeError(f"create_doc 未返回可识别的 file_id: {out}")


def insert_markdown(fid, path_hint, md_path, attempts=3):
    """插入全文；空闲服务上首次插入偶发 `document is not open`，此处重开并重试。"""
    for i in range(attempts):
        try:
            return call("doc_insert_markdown", file_id=fid, idx=0, markdown=f"file://{md_path}")
        except RuntimeError as e:
            if "not open" not in str(e) or i == attempts - 1:
                raise
            time.sleep(1.5)
            if path_hint:
                try:
                    call("open_file", file_path=path_hint, open_with_existing=True)
                except Exception:
                    pass


def insert_images(fid, cfg):
    """按 `images` 配置插图：以「图：…」题注段落的起始坐标为锚点，把图片插到题注之前。

    配置项：{"match": "图：XXX", "path": "/abs/a.png", "w": 600, "h": 317}
    w/h 为像素（96 DPI）；A4 + 72pt 页边距下正文宽度约 600px。
    """
    specs = cfg.get("images") or []
    done = 0
    for sp in specs:
        found = call("doc_find", file_id=fid, text=sp["match"])
        # doc_find 返回 {"locations":[{begin,end,...}], total:N}
        hits = found.get("locations") or found.get("matches") or found.get("results") or []
        if not hits:
            continue
        idx = hits[0]["begin"]
        kw = {"file_id": fid, "idx": idx, "image_path": sp["path"]}
        if sp.get("w"):
            kw["w"] = sp["w"]
        if sp.get("h"):
            kw["h"] = sp["h"]
        call("doc_insert_image", **kw)
        done += 1
    return done


def build(job, cfg):
    md_path, out_path = job["markdown"], job["output"]
    try:  # 清掉同路径旧实例，避免读到带重复内容的缓存
        call("close_file", file_id=out_path)
    except Exception:
        pass

    fid, tmp_path = create_blank()
    insert_markdown(fid, tmp_path, md_path)

    style_kw = {}
    for key in ("default_text_style", "default_paragraph_style", "page_style"):
        if cfg.get(key):
            style_kw[key] = cfg[key]
    if style_kw:
        call("doc_set_document_style", file_id=fid, **style_kw)

    titled = style_title(fid, cfg.get("title"))
    shaded, eligible = style_tables(fid, cfg)
    images = insert_images(fid, cfg)
    call("save_file", file_id=fid, file_path=out_path)
    return {"output": out_path, "tables": eligible, "shaded": shaded,
            "title": titled, "images": images, "file_id": fid}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    for job in cfg["jobs"]:
        res = build(job, cfg)
        ok = (res["shaded"] == res["tables"] and (res["title"] or not cfg.get("title"))
              and res["images"] == len(cfg.get("images") or []))
        print(f"{'OK  ' if ok else 'WARN'} {res['output']}  "
              f"tables={res['tables']} shaded={res['shaded']} "
              f"title={res['title']} images={res['images']}")


if __name__ == "__main__":
    main()
