---
name: blogger-refine
description: |
  博主画像提炼模块。纯数据加工——不碰任何文件 I/O。
  输入 config_snapshot + 原文 + 已有画像，返回 profile_content 和 console_delta。
  由 pipeline 负责实际文件读写。所有路径和模板由 pipeline 传入。
  触发词：「博主提炼」「博主画像」「blogger refine」「画像更新」
  区别：与 wiki-refine 的区别在于产出是人物画像。纯内存操作。
version: 1.0.0
---

# 博主画像提炼（纯内存）

## 输入（全部必填）

{source_path, config_snapshot, profile_path, template_path}

config_snapshot 结构：
```json
{
  "name": "博主名",
  "aliases": "别名1, 别名2",
  "is_xueqiu": "是 | 否",
  "is_following": "是 | 否",
  "is_starred": "是 | 否"
}
```

## 流程

1. 读 {template_path}，获取画像章节结构
2. 读 source_path 原文
3. 读 profile_path 已有画像内容（不存在则为空）
4. 按 {template_path} 结构，增量提炼
5. 生成 profile_content（完整 Markdown，含 frontmatter）
6. 生成 console_delta（仅实际变化的字段）

## 输出（纯数据，不碰文件）

```json
{
  "profile_content": "完整的画像 Markdown 字符串",
  "console_delta": {
    "aliases?": "更新后的别名字符串",
    "is_xueqiu?": "是 | 否",
    "is_following?": "是 | 否",
    "is_starred?": "是 | 否"
  }
}
```

## 提炼要求

- 忠于原文，不添加原文没有的观点
- 增量追加而非覆盖已有内容
- 保持画像的历史演变记录
- 新增内容标注来源日期

## 控制台字段默认值

| 字段 | 默认值 |
|:---|:---|
| is_xueqiu | 是 |
| is_following | 是 |
| is_starred | 否 |

## 自检

- [ ] profile_content 包含模板所有必须章节？
- [ ] 新增内容有来源标注？
- [ ] console_delta 只含实际变化的字段？
- [ ] 未执行任何文件读写操作？
