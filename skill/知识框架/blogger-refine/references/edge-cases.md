# 边界情况

> `blogger-refine` 按需引用。遇到以下场景时加载。

## 输入缺失必填字段

报错格式：`缺少必填字段: {字段名}。需要提供 source_path, config_snapshot, profile_path, template_path。`

## 原文 > 5000 字

分段提炼策略：
1. 按 `## ` 标题拆段，每段独立定档评分
2. 每段单独计算 post_score 增量
3. 汇总为一次 profile_content 输出
4. sources 只追加一次

## 已有画像不存在（新建）

1. 按 template_path 生成完整 frontmatter，`post_score: 0`
2. `sources` 追加当前 source_path
3. `createDate` = 当前日期，`updateDate` = 当前日期

## 源文件类型无法识别

标记 `[类型待确认]`，按「观点评论」（6 分）处理，走完提炼流程。

## 同一文章重复提炼

检查 `sources` 列表是否已包含当前 source_path。若已存在 → 跳过提炼，不重复计分。

## post_score 计算结果为负数

正常写入画像 frontmatter，不加限制。审查阶段会标记关注。

## 质量系数无法判断时

按「正常」（×1.0）处理，不做扣分。宁可漏扣，不可误扣。
