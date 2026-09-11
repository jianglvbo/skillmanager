#!/usr/bin/env python3
"""把内容填入既有 Word 模板（保留模板格式），走本地 editor_sdk 通道。

用法：
    python3 fill_template.py fill.json

fill.json：
{
  "template": "/abs/空白模板.docx",
  "output":   "/abs/成品.docx",
  "edits":    [{"match": "占位原文片段", "text": "替换后的全文"}],
  "anchor_inserts": [{"after_match": "工作流步骤", "texts": ["1）…", "2）…", "图：…"]}],
  "images":   [{"match": "图：XXX", "path": "/abs/a.png", "w": 600, "h": 317}],
  "tables":   [{"index": 1, "cells": [{"row": 2, "col": 2, "text": "值"}]}],
  "drops":    [{"match": "（如果有多个场景，可以自行添加）"}]
}

关键纪律（详见 SKILL.md）：
- 只替换文本，不调用任何字体/字号/对齐/页面设置类工具 → 格式天然不变
- edits 必须在**任何编辑之前**一次性定位，再按 begin 降序替换 → 坐标不漂移
- 表用「当前顺序」解析 table_id，不用旧 id（多次编辑后旧 id 失效）
- anchor_inserts 的位置在 edits 完成后**重新解析文档**得到
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

SKILL_DIR = os.environ.get(
    "LOCAL_OFFICE_EDIT_DIR",
    "/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/plugins/"
    "workbuddy-builtin/skills/tencent-local-office-edit",
)


def call(tool, **kw):
    args = ["python3", "edsdk.py", "call", tool]
    js = {}
    for k, v in kw.items():
        if isinstance(v, (dict, list, bool)) or v is None:
            js[k] = v
        else:
            args.append(f"{k}={v}")
    if js:
        args += ["--json", json.dumps(js, ensure_ascii=False)]
    r = subprocess.run(args, cwd=SKILL_DIR, capture_output=True, text=True)
    out = (r.stdout or "").strip()
    if r.returncode != 0 or out.startswith('{"ok": false'):
        raise RuntimeError(f"{tool} 失败: {out} {r.stderr.strip()}")
    return json.loads(out) if out.startswith(("{", "[")) else out


def open_clean(path):
    try:
        call("close_file", file_id=path, force=True)
    except Exception:
        pass
    call("open_file", file_path=path)
    time.sleep(4)


def locate(fid, text):
    """返回 (begin, end)；未命中返回 None。doc_find 的返回键是 locations。"""
    hits = (call("doc_find", file_id=fid, text=text).get("locations") or [])
    return (hits[0]["begin"], hits[0]["end"]) if hits else None


def main():
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    tpl, out_path = cfg["template"], cfg["output"]
    if os.path.abspath(tpl) != os.path.abspath(out_path):
        shutil.copyfile(tpl, out_path)  # 模板本身保持不动
    open_clean(out_path)
    file_id = out_path

    # 1) 一次性定位全部替换目标（此刻坐标有效），再按 begin 降序替换
    #    edits 条目二选一：{"match": "唯一短串"} 或 {"range": [begin, end]}（取自编辑前的结构快照）
    planned = []
    for e in cfg.get("edits", []):
        if "range" in e:
            loc = tuple(e["range"])
        else:
            loc = locate(file_id, e["match"])
            if not loc:
                raise RuntimeError(f"未找到待替换占位: {e['match']}")
        planned.append((loc[0], loc[1], e["text"]))
    for begin, end, text in sorted(planned, key=lambda x: -x[0]):
        call("doc_replace_text", file_id=file_id,
             ranges=[{"begin": begin, "end": end}], text=text)
    print(f"文本替换 {len(planned)} 处")

    # 2) 锚点后插入：编辑完成后重新解析，取锚点之后连续空段落的真实坐标
    for ins in cfg.get("anchor_inserts", []):
        nodes = call("doc_resolve_document_structure", file_id=file_id,
                     mode="compact", limit=0)["nodes"]
        # compact 模式 text_preview 仅约 4 字，锚点串必须短
        i = next(k for k, n in enumerate(nodes)
                 if ins["after_match"] in (n.get("text_preview") or ""))
        need = len(ins["texts"])
        slots = []
        for n in nodes[i + 1:]:          # 只取锚点之后**连续**的空段落
            if len(slots) >= need or n["start_index"] != n["end_index"]:
                break
            slots.append(n["start_index"])
        if len(slots) < need:
            raise RuntimeError(f"锚点后空段落不足: 需 {need} 个，找到 {len(slots)} 个")
        shift = 0
        for pos, text in zip(slots, ins["texts"]):
            call("doc_insert_text", file_id=file_id, idx=pos + shift, text=text)
            shift += len(text)
        print(f"锚点 {ins['after_match']} 后插入 {len(ins['texts'])} 段")

    # 3) 图片：插到题注之前
    for im in cfg.get("images", []):
        loc = locate(file_id, im["match"])
        if not loc:
            raise RuntimeError(f"未找到题注: {im['match']}")
        kw = {"file_id": file_id, "idx": loc[0], "image_path": im["path"]}
        if im.get("w"):
            kw["w"] = im["w"]
        if im.get("h"):
            kw["h"] = im["h"]
        call("doc_insert_image", **kw)
        print(f"插图 → {im['match']} 之前")

    # 4) 删除提示行：文本置空，不删段落（避免坐标与结构变动）
    for d in cfg.get("drops", []):
        loc = locate(file_id, d["match"])
        if loc:
            call("doc_replace_text", file_id=file_id,
                 ranges=[{"begin": loc[0], "end": loc[1]}], text="")

    # 5) 表格：按当前顺序取 table_id（旧 id 在多次编辑后会失效）
    if cfg.get("tables"):
        ids = [t["table_id"] for t in call("doc_list_tables", file_id=file_id)["tables"]]
        for t in cfg["tables"]:
            call("doc_set_table_cells", file_id=file_id,
                 table_id=ids[t["index"]], cells=t["cells"])
        print(f"表格填写 {len(cfg['tables'])} 张")

    call("save_file", file_id=file_id)
    print("已保存:", out_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main()
