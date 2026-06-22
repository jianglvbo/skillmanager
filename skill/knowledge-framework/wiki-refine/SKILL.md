---
name: wiki-refine
description: |
  投资知识提炼。将原始资源提炼为维基仓库的结构化条目。使用三维分类，按传入模板填充内容。
  触发词：「提炼」「refine」「分类」「结构化」「wiki refine」
  区别：与 coarse-processor 的区别在于产出是结构化知识条目。
        与 blogger-refine 的区别在于产出是投资知识而非人物画像。
version: 1.0.0
---

# 投资知识提炼

## 前置

提炼前先读 **仪表盘/待处理队列.md**，Dataview 查询 `FROM "原始资源仓库" WHERE status = "待提炼"` 直接获取待提炼文件列表，**不要逐个扫目录读 frontmatter**。

## 输入（全部必填）

{source_path, target_dir, category, content_type, time_sensitivity, template_path}

## 流程

1. 读 source_path 全文
2. 读 {template_path}，获取输出章节结构
3. 判断目标：更新已有条目 or 创建新条目
4. 按 {template_path} 指定的结构填充内容
5. 自动验证标记：识别方向性断言 → 写入 validations
6. 交叉链接：关联条目与被关联条目双向 wikilink
7. 清理原始资源的 _ 前缀字段
8. 保存到 {target_dir}/{category}/{标题}.md，更新源 status=已提炼

## 六条提炼原则

1. 忠于原文——不添加原文没有的观点
2. 结构化输出——使用模板格式
3. 来源可溯——每个观点标注来源
4. 增量更新——已有条目追加不覆盖
5. 多维度提炼——一篇可能产出多条维基条目
6. 交叉链接——关联条目双向互链

### 决策表：category → 子目录

| category | 子目录 |
|:---|:---|
| 投资理念 | {target_dir}/投资理念/ |
| 概念 | {target_dir}/概念/ |
| 板块 | {target_dir}/板块/ |
| 个股-港股 | {target_dir}/个股/港股/ |
| 个股-A股 | {target_dir}/个股/A股/ |
| 个股-美股 | {target_dir}/个股/美股/ |
| 宏观 | {target_dir}/宏观/ |

## 自检

- [ ] frontmatter category/content_type/time_sensitivity 齐全？
- [ ] 文件位置与 category 对应？
- [ ] 关联条目双向互链？
- [ ] _ 前缀字段已清除？
- [ ] validations 字段存在（如有方向性断言）？
