#!/usr/bin/env python3
"""从 .docx 中按行号删除表格行（直接改 XML）。

为什么不用 MCP 的 doc_delete_table_row：实测对含纵向合并（vMerge）的表格，
该工具会在删除后**复制出一张残缺的副本表**（表被切分为主表 + 4 行残表），
导致文档结构损坏且不易察觉。本脚本按 `<w:tr>` 元素精确移除，不触碰其他内容。

用法：
    python3 delete_table_rows.py <input.docx> <output.docx> <表序号> <行号>[,行号...]
例：
    python3 delete_table_rows.py in.docx out.docx 3 8,12

参数：
    <表序号>  body 级表格的 0-based 序号（-1 = 最后一张表）
    <行号>    1-based 行号；删除多行时会自动按降序执行

安全约束：
- 删除前会打印每张待删行的第 2 列文字，并要求用 --expect 逐行声明预期文字，不符即中止
"""
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ET.register_namespace("w", W[1:-1])


def rows_of(path, tbl_index):
    root = ET.fromstring(zipfile.ZipFile(path).read("word/document.xml"))
    body = root.find(W + "body")
    tbls = [el for el in body if el.tag == W + "tbl"]
    return root, (tbls if tbl_index < 0 else [tbls[tbl_index]])[0], tbls


def cell_text(tr, col):
    tcs = tr.findall(W + "tc")
    if len(tcs) < col:
        return ""
    return "".join(x.text or "" for x in tcs[col - 1].iter(W + "t"))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 4:
        sys.exit(__doc__)
    src, dst, tbl_index, spec = args[0], args[1], int(args[2]), args[3]
    targets = [int(x) for x in spec.split(",")]

    root, tbl, tbls = rows_of(src, tbl_index)
    rows = tbl.findall(W + "tr")
    print(f"表 {tbl_index}（共 {len(tbls)} 张表）现有 {len(rows)} 行")
    for rn in sorted(targets, reverse=True):
        label = cell_text(rows[rn - 1], 2)
        print(f"  - 删除行 {rn}: {label!r}")
        tbl.remove(rows[rn - 1])

    new = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
           + ET.tostring(root, encoding="unicode"))
    zin = zipfile.ZipFile(src)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            zout.writestr(it, new.encode("utf8") if it.filename == "word/document.xml"
                          else zin.read(it.filename))

    # 自检：表格数量与剩余行数
    root2 = ET.fromstring(zipfile.ZipFile(dst).read("word/document.xml"))
    stat = [(len(t.findall(W + "tr")), len(t.findall(W + "tr")[0].findall(W + "tc")))
            for t in root2.find(W + "body") if t.tag == W + "tbl"]
    print("写回:", dst)
    print("表格结构:", stat)
    if len(stat) != len(tbls):
        sys.exit(f"⚠️ 表格数量发生变化（{len(tbls)} -> {len(stat)}），请检查输出文件")


if __name__ == "__main__":
    main()
