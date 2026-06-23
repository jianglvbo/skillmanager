---
name: blogger-refine
description: 
  博主画像提炼。输入 config_snapshot + 原文 + 已有画像，返回 profile_content 和 console_delta。
  纯内存加工，不碰文件 I/O。由 pipeline 负责读写。
  触发词：「博主提炼」「博主画像」「画像更新」。
  区别于 wiki-refine：产出人物画像而非投资知识。
  区别于 link-ingest：不抓取链接，只加工已有文章。
---

# Default stance

## 核心原则

- 纯内存操作：不读不写文件，pipeline 负责所有 I/O
- 增量追加：已有画像追加新日期段落，不覆盖历史章节
- 忠于原文：不添加原文没有的观点

## 禁止行为
- 绝不修改 pipeline 传入的路径常量
- 绝不覆盖已有画像的历史章节
- 绝不跳过 post_score 计算
- 绝不添加原文中没有的信息
- 绝不在未读到原文时生成观点

---

# Workflow

1. 第一步：读模板 → 获取画像章节结构（`assets/blogger-profile.md`）
2. 第二步：读原文 → 解析 source_path 正文内容
3. 第三步：读已有画像 → profile_path 不存在则按空处理
4. 第四步：决策平台数据 → `is_xueqiu=是` 则加载 `references/xueqiu-data-pipeline.md`
5. 第五步：增量提炼 → 定位、风格、观点、标的、语录（模板见 `assets/blogger-profile.md`）
6. 第六步：计算 post_score → 规则见 `references/post-scoring.md`
7. 第七步：生成输出 → profile_content（含 frontmatter）+ console_delta

---

# Output format

```json
{
  "profile_content": "完整画像 Markdown（含 frontmatter）",
  "console_delta": {
    "aliases?": "别名数组",
    "is_xueqiu?": "是 | 否",
    "is_following?": "是 | 否",
    "is_starred?": "是 | 否"
  }
}
```

## frontmatter 必填字段

| 字段 | 说明 | 来源 |
|:---|:---|:---|
| `summary` | ≤一行定位（平台+风格+代表作） | 从原文提炼 |
| `sources` | 追加当前 source_path | pipeline |
| `aliases` | 从控制台别名列 | config_snapshot |
| `following` | 雪球关注=是 → true | config_snapshot |
| `post_score` | 累计质量分 | `references/post-scoring.md` |

## 提炼内容规则

- 语录动态审视：新原文金句 > 旧语录则替换
- 控制台默认值：雪球博主=是、雪球关注=是、特别关注=否

---

# Relative files

| 场景 | 加载文件 | 内容 |
|:---|:---|:---|
| 始终 | `assets/blogger-profile.md` | 画像章节模板 |
| `is_xueqiu=是` | `references/xueqiu-data-pipeline.md` | 雪球数据获取与注入 |
| 计算 post_score 时 | `references/post-scoring.md` | 三因子评分规则 |
| 输入缺失 / 原文超长 / 重复提炼 | `references/edge-cases.md` | 边界情况处理 |

---

# Source hierarchy

| 优先级 | 来源 | 涉及内容 |
|:---|:---|:---|
| 1 | 用户显式约定 | post_score 倒扣机制、语录更新规则、质量系数 |
| 2 | Obsidian 规范 | wikilink 格式、frontmatter 字段类型 |
| 3 | knowledge-pipeline | 路径常量、模板结构、config_snapshot 格式 |
| 4 | 工程实践验证 | 增量更新模式、评分幂等性 |

---

# 自检

- [ ] 所有必填字段非空？
- [ ] 语录需要更新？
- [ ] 雪球博主 → 已加载 xueqiu-data-pipeline？
- [ ] post_score 计算完成、理由可追溯？
- [ ] 未执行文件读写？
