---
name: link-ingest
description: |
  链接收集与抓取。将 URL 转为可存档的 Markdown，存入指定目录。
  不负责后续加工——只抓原文、写 frontmatter。所有路径由调用方传入，全部必填。
  触发词：「链接收集」「抓取」「存链接」「ingest link」
  区别：与 coarse-processor 的区别在于不做 metadata 补全和归档。
version: 1.0.0
---

# 链接收集

## 输入（全部必填）

{url, source_type, output_dir}

## 流程

1. 按 source_type 选工具（见决策表）
2. 抓取原文，不抓评论
3. 写 frontmatter：title, source, date
4. 保存到 {output_dir}/{标题}.md

### 抓取决策表

| source_type | 工具 |
|:---|:---|
| 雪球 | autocli read |
| 公众号 | WebFetch + 微信 UA |
| 抖音 | API → ffmpeg → whisper |
| 直接 | 不抓取，直接写 |

## 自检

- [ ] 文件是否成功写入 {output_dir}？
- [ ] frontmatter 的 title, source, date 非空？
- [ ] 原文内容不为空？
