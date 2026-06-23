---
name: blogger-refine
description: |
  博主画像提炼模块。纯数据加工——不碰任何文件 I/O。
  输入 config_snapshot + 原文 + 已有画像，返回 profile_content 和 console_delta。
  由 pipeline 负责实际文件读写。所有路径和模板由 pipeline 传入。
  触发词：「博主提炼」「博主画像」「blogger refine」「画像更新」
  区别：与 wiki-refine 的区别在于产出是人物画像。纯内存操作。
version: 2.0.0
---

# 博主画像提炼（纯内存）

## 输入（全部必填）

{source_path, config_snapshot, profile_path, template_path}

config_snapshot 结构：
```json
{
  "name": "博主名",
  "aliases": ["别名1", "别名2"],
  "is_xueqiu": "是 | 否",
  "is_following": "是 | 否",
  "is_starred": "是 | 否"
}
```

---

## 默认行为与禁止

| 场景 | 行为 |
|:---|:---|
| 输入缺失必填字段 | 报错，写明缺少哪个字段，停止执行 |
| 已有画像不存在 | 新建画像，template_path 决定结构 |
| 已有画像存在 | 增量追加，不覆盖已有章节 |
| 源文件类型无法识别 | 标记为「待确认」，走默认提炼流程 |
| 原文 > 5000 字 | 分段提炼，每段独立定档评分 |
| post_score 计算结果为负数 | 正常写入，不强制归零 |

### 禁止行为

- 绝不修改 pipeline 传入的路径常量
- 绝不覆盖已有画像的历史章节（仅追加新日期段落）
- 绝不在未读到原文时生成观点
- 绝不自行决定跳过 post_score 计算
- 绝不添加原文中没有的信息

---

## 核心流程

```
读模板 → 读原文 → 读已有画像（可选）
                  ↓
           【决策点】is_xueqiu = 是？
            ├─ 是 → 按需加载 references/xueqiu-data-pipeline.md
            │        拉取雪球数据（xq_id、粉丝、近帖）
            │        将平台数据注入 frontmatter
            └─ 否 → 跳过
                  ↓
          提炼观点/风格/语录 → 计算 post_score
                           （规则见 references/post-scoring.md）
                  ↓
          生成 profile_content + console_delta
```

### 详细步骤

1. 读 {template_path}，获取画像章节结构（见 `assets/blogger-profile.md`）
2. 读 source_path 原文内容
3. 读 profile_path 已有画像（不存在则为空，新建）
4. **决策：是否需要平台数据？**
   - `is_xueqiu = 是` → 加载 `references/xueqiu-data-pipeline.md`，获取 xq_id / followers / 近期帖子
   - `is_xueqiu = 否` → 跳过平台数据步骤
5. 按模板结构增量提炼：定位、风格、观点、标的、语录
6. **计算 post_score 并累加**（见下方评分规则）
7. 生成 profile_content（完整 Markdown，含 frontmatter）
8. 生成 console_delta（仅实际变化的字段）

---

## 输出（纯数据，不碰文件）

```json
{
  "profile_content": "完整的画像 Markdown 字符串",
  "console_delta": {
    "aliases?": "更新后的别名数组",
    "is_xueqiu?": "是 | 否",
    "is_following?": "是 | 否",
    "is_starred?": "是 | 否"
  }
}
```

---

## 提炼要求

### 内容规则
- 忠于原文，不添加原文没有的观点
- 增量追加而非覆盖已有内容
- 保持画像的历史演变记录（「演变轨迹」章节）
- 新增内容标注来源日期

### Frontmatter 必填规则

| 字段 | 规则 | 来源 |
|:---|:---|:---|
| `summary` | 一句定位描述（平台+风格+代表作），≤一行 | 从原文提炼 |
| `sources` | 每次提炼追加 source_path | pipeline 传入 |
| `aliases` | 从控制台别名列获取 | config_snapshot |
| `following` | 控制台「雪球关注=是」→ true | config_snapshot |
| `xq_id` | 雪球数字 ID，雪球博主才有 | xueqiu-data-pipeline |
| `followers` | 粉丝数，雪球博主才有 | xueqiu-data-pipeline |
| `post_score` | 帖子质量加权累计分 | 见评分规则 |

### 语录动态更新

画像底部代表性语录需在每次提炼新内容时重新审视：
- 新内容中出现比旧语录更能代表博主当前风格的金句 → 替换或追加
- 确保语录始终是博主表达 DNA 的最佳切片

---

## 帖子质量评分

提炼每篇文章时，按 `references/post-scoring.md` 的完整规则计算 post_score 增量。

### 快速公式

```
本轮增量 = 内容类型基础分 × 来源权重 × 质量系数
post_score = 已有 post_score + 本轮增量（四舍五入）
```

### 速查

| 维度 | 快速参考 |
|:---|:---|
| 方法论/投资体系 | 10 分 |
| 案例分析/个股深度 | 8 分 |
| 观点评论 | 6 分 |
| 数据解读 | 5 分 |
| 市场综述/行情复盘 | 3 分 |
| 生活随笔 | 1 分 |
| 原创 | ×1.0 |
| 深度转述 | ×0.7 |
| 转载 | ×0.5 |
| 纯引用 | ×0.3 |
| 偏水 | ×0.5 |
| 短篇无观点 | ×-0.5 |
| 标题党 | ×-0.8 |
| 风格漂移 | ×-0.8 |
| 注水严重 | ×-1.0 |

> 详细定档逻辑、平台特殊规则、扣分条件详解 → 见 `references/post-scoring.md`

---

## 控制台字段默认值

| 字段 | 默认值 |
|:---|:---|
| is_xueqiu | 是 |
| is_following | 是 |
| is_starred | 否 |

---

## 规则来源

| 优先级 | 来源 | 涉及内容 |
|:---|:---|:---|
| 1 | 用户显式约定 | 画像结构、语录更新、post_score 倒扣机制、质量系数 |
| 2 | Obsidian 规范 | wikilink 格式、frontmatter 字段类型、文件命名 |
| 3 | knowledge-pipeline | 路径常量、模板结构、config_snapshot 格式 |
| 4 | 工程实践验证 | 增量更新模式、评分公式设计 |

---

## 测试用例

| # | 场景 | 输入 | 期望输出 |
|:---|:---|:---|:---|
| 1 | 新建雪球画像 | 重组专家 config + 中广核深度 + 空画像 | post_score=8, xq_id 写入, 含完整章节 |
| 2 | 增量更新 | FIRE青年已有画像 + 新观点文 | 追加不覆盖, sources+1, post_score 累加 |
| 3 | 非雪球 | 寒叔聊投资（is_xueqiu=否）+ 综述 | 跳过数据管道, post_score=3, xq_id 不写 |
| 4 | 注水文章 | 纯行情复述无判断 | post_score 增量为负, 画像标注「低质量」 |
| 5 | 空已有画像 | 首次提炼某博主 | 按模板新建，所有必填字段非空 |

---

## 语言约定

- 输入：中文（主要）/ 英文
- 输出：默认中文
- 日期格式：YYYY年M月D日（如 2026年6月23日）
- 文件命名：完整中文标题

---

## 自检

- [ ] profile_content 包含模板所有必须章节？
- [ ] summary / sources / post_score 三个字段非空？
- [ ] 新增内容有来源标注？
- [ ] 语录是否需要替换/更新？
- [ ] console_delta 只含实际变化的字段？
- [ ] 未执行任何文件读写操作？
- [ ] 雪球博主 → 已加载 xueqiu-data-pipeline 并注入平台数据？
