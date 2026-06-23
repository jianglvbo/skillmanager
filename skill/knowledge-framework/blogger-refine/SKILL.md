---
name: blogger-refine
description: |
  博主画像提炼。纯内存加工——不碰文件 I/O。
  触发词：「博主提炼」「博主画像」「画像更新」。区别于 wiki-refine（产出投资知识）。
version: 2.1.0
---

# 博主画像提炼

## 输入

{source_path, config_snapshot, profile_path, template_path}

```json
{
  "name": "博主名",
  "aliases": ["别名"],
  "is_xueqiu": "是 | 否",
  "is_following": "是 | 否",
  "is_starred": "是 | 否"
}
```

## 默认行为

| 场景 | 行为 |
|:---|:---|
| 输入缺字段 / 原文 > 5000 字 / 已有画像不存在 | 见 `references/edge-cases.md` |
| post_score 负数 | 保留，不归零 |

**禁止**：覆盖已有章节 · 跳过评分 · 添加原文无的观点 · 改 pipeline 传入的路径

---

## 工作流

1. 读 template_path → 获取章节结构
2. 读 source_path 原文
3. 读 profile_path（不存在则新建）
4. **决策**：`is_xueqiu=是` → 加载 `references/xueqiu-data-pipeline.md`，拉取雪球数据注入 frontmatter
5. 按模板增量提炼：（定位 → 风格 → 观点 → 标的 → 语录）
6. **计算 post_score**（规则：`references/post-scoring.md`）
7. 输出 profile_content + console_delta

---

## 提炼规则

### 内容
- 忠于原文 · 增量追加 · 保留演变轨迹
- 语录动态审视：新金句 > 旧金句则替换

### frontmatter 必填

| 字段 | 说明 | 来源 |
|:---|:---|:---|
| `summary` | ≤一行定位（平台+风格+代表作） | 从原文提炼 |
| `sources` | 追加 source_path | pipeline |
| `aliases` | 从控制台别名列 | config_snapshot |
| `following` | 雪球关注=是 → true | config_snapshot |
| `post_score` | 质量加权累计分 | post-scoring.md |

---

## Post Score 速查

```
本轮 = 内容类型基础分 × 来源权重 × 质量系数（取整）
```

| 类型 | 分 | 来源 | 权重 | 质量 | 系数 |
|:---|:---:|:---|:---:|:---|:---:|
| 方法论 | 10 | 原创 | 1.0 | 正常 | 1.0 |
| 案例/个股 | 8 | 深度转述 | 0.7 | 偏水 | 0.5 |
| 观点评论 | 6 | 转载 | 0.5 | 短篇无观点 | -0.5 |
| 数据解读 | 5 | 纯引用 | 0.3 | 标题党 | -0.8 |
| 市场综述 | 3 | | | 风格漂移 | -0.8 |
| 生活随笔 | 1 | | | 注水严重 | -1.0 |

> 质量系数扫描顺序：注水→漂移→标题党→短篇→偏水→正常，命中即停。

---

## 控制台默认值

空 = 雪球博主「是」· 雪球关注「是」· 特别关注「否」

---

## 自检

- [ ] 所有必填字段非空？语录需更新？
- [ ] 雪球博主 → 已加载 xueqiu-data-pipeline？
- [ ] post_score 计算完成、理由可追溯？
- [ ] 未执行文件读写？
