#!/usr/bin/env python3
"""提取本地 .docx 全文（含表格），用于读取参考文档。

为什么需要它：editor_sdk 的结构/查询接口只回「文本预览」，会归一化空白并截断
（标题类节点常只剩 ~4 字），无法支撑「照着某份 docx 复刻结构」的读取需求。
本脚本直接解析 OOXML，输出完整段落与表格文本，作为读取通道的补充。

用法：
    python3 extract_docx_text.py /abs/path.docx
"""
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def para_text(p):
    parts = []
    for node in p.iter():
        if node.tag == W + "t" and node.text:
            parts.append(node.text)
        elif node.tag == W + "tab":
            parts.append("\t")
        elif node.tag == W + "br":
            parts.append("\n")
    return "".join(parts).strip()


def style_of(p):
    pr = p.find(W + "pPr")
    if pr is None:
        return ""
    st = pr.find(W + "pStyle")
    return st.get(W + "val") if st is not None else ""


def walk(body, out):
    for el in body:
        if el.tag == W + "p":
            txt = para_text(el)
            st = style_of(el)
            if re.match(r"Heading|Title", st or "", re.I):
                lvl = re.sub(r"\D", "", st) or "1"
                out.append(f"\n{'#' * min(int(lvl), 6)} {txt}")
            elif txt:
                out.append(txt)
        elif el.tag == W + "tbl":
            out.append("\n[TABLE]")
            for tr in el.findall(W + "tr"):
                out.append("| " + " | ".join(para_text(tc) for tc in tr.findall(W + "tc")) + " |")
            out.append("[/TABLE]\n")


def main(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    out = []
    walk(root.find(W + "body"), out)
    print("\n".join(out))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1])
