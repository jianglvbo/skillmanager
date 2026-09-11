#!/usr/bin/env python3
"""批量从 Markdown 生成带样式的本地 .docx（走本地 editor_sdk / tencent-local-office-edit 通道）。

用法：
    python3 build_docx.py jobs.json

jobs.json：
{
  "header_fill": "F1F5F9",            # 可选，表头底色，默认 F1F5F9
  "center_header": true,              # 可选，表头是否居中，默认 true
  "jobs": [
    {"markdown": "/abs/a.md", "output": "/abs/a.docx"},
    {"markdown": "/abs/b.md", "output": "/abs/b.docx", "header_fill": "EAF2FF"}
  ]
}

约定：
- 每个作业都新建空白文档（不复用 file_id），避免内容重复插入
- 生成后打印标题数/表格数，供与草稿比对
"""
import json
import os
import re
import subprocess
import sys

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
        if isinstance(v, (dict, list)):
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


def build(md_path, out_path, header_fill=DEFAULT_FILL, center_header=True):
    try:  # 清掉同路径旧实例，避免读到带重复内容的缓存
        call("close_file", file_id=out_path)
    except Exception:
        pass

    fid = call("create_doc")
    call("doc_insert_markdown", file_id=fid, idx=0, markdown=f"file://{md_path}")

    tables = call("doc_list_tables", file_id=fid)["tables"]
    cell_props = {"property": {"background_color": header_fill}}
    if center_header:
        cell_props["horizontal_align"] = "center"
    for t in tables:
        call(
            "doc_set_table_cells",
            file_id=fid,
            table_id=t["table_id"],
            cells=[{"row": 1, "col": c} for c in range(1, t["col_count"] + 1)],
            common_cell_properties=cell_props,
        )

    call("save_file", file_id=fid, file_path=out_path)
    return {"output": out_path, "tables": len(tables), "file_id": fid}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    fill = cfg.get("header_fill", DEFAULT_FILL)
    center = cfg.get("center_header", True)
    for job in cfg["jobs"]:
        res = build(job["markdown"], job["output"], job.get("header_fill", fill), center)
        print(f"OK  {res['output']}  tables={res['tables']}")


if __name__ == "__main__":
    main()
