---
name: wiki-review
description: |
  维基审查模块。扫描维基仓库，按指定维度生成审查报告。
  所有路径和模板由 pipeline 传入。
  触发词：「审查」「review」「检查」「健康度」
  区别：与 qa-ask 的区别在于产出是系统性批量审查，非单次问答。
version: 1.0.0
---

# 维基审查

## 输入（全部必填）

{target_dir, dimensions, output_dir, template_path}

## 流程

1. 读 {template_path}，获取报告格式
2. 扫描 target_dir 全部条目
3. 按 dimensions 逐项检查
4. 按 {template_path} 生成报告
5. 保存到 {output_dir}/YYYY年M月D日-审查.md

## 五维度速查

| 维度 | 检查内容 | 阈值 |
|:---|:---|:---|
| 矛盾检测 | 同板块/个股条目间矛盾观点 | 人工判断 |
| 时效检查 | time_sensitivity 对应周期 | 短期>30天/中期>90天/长期>180天 |
| 验证回溯 | validations 历史断言状态 | 存在待验证断言 |
| 孤立检测 | 无 backlinks 或从未被查询 | backlinks=0 或 queried=0 |
| 质量检查 | 缺必填字段/文件过小/分类不匹配 | 文件<200bytes |

## 审查频率

| 类型 | 频率 |
|:---|:---|
| 全量审查 | 每周 |
| 增量审查 | 每次提炼后 |

## 自检

- [ ] 报告覆盖所有传入的 dimensions？
- [ ] 每个问题条目标注了具体文件路径？
- [ ] 报告中无遗漏的条目？
