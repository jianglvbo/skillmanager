---
name: qa-ask
description: |
  知识检索与问答模块。查询维基仓库和/或博主画像，生成结构化问答产物。
  支持 source 参数控制检索范围（wiki/blogger/both），可独立使用，也可作为财报分析等链路的背景检索前置步骤。
  所有搜索目录和输出路径由 pipeline 传入。
  触发词：「问答」「提问」「qa」「根据框架」「怎么看」「财报分析」「结合框架分析」
  区别：与 wiki-review 的区别在于产出是一次性问答，非批量审查报告。
version: 1.1.0
---

# 知识检索与问答

## 输入（全部必填）

{question, source, output_dir, template_path}

## source → 目录映射

| source | 搜索目录 |
|:---|:---|
| wiki | WIKI_TARGET（维基仓库/投资分析） |
| blogger | BLOGGER_PROFILE（维基仓库/博主画像） |
| both | 并行搜索 WIKI_TARGET + BLOGGER_PROFILE，合并结果 |

## 流程

1. 读 {template_path}，获取输出格式
2. 解析 question，确定查询策略
3. 按 source 映射确定搜索目录，在目标目录中搜索相关条目
4. 按 {template_path} 格式输出
5. 保存到 {output_dir}/YYYY年M月D日-主题.md
6. 更新被引用条目的 queried 计数和 last_queried

## 查询原则

1. 先全貌后详情：先列表目录获取全貌，再深入具体条目
2. 多维度交叉：从概念、板块、个股、宏观多角度获取信息
3. 来源可溯：查询结果标注引用的维基条目
4. 关注时效性：优先引用最近更新的内容

## 输出要求

- 独立视角
- 三维评估：逻辑成立度 / 证据充分度 / 风险盲区
- 紧凑排版，分隔线分区块
- 数据优先表格

## 自检

- [ ] source 值是否为 wiki / blogger / both 之一？
- [ ] 文件保存到正确路径？
- [ ] 引用条目路径存在？
- [ ] queried 计数已更新？
