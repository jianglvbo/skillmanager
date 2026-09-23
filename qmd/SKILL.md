---
name: qmd
description: >
  QMD 本地文档索引与搜索工具。对本地 Markdown/文本文件建立全文索引、向量嵌入和语义搜索。
  支持 collection 管理、BM25 关键词搜索、向量语义搜索、混合查询（LLM 重排序）以及 MCP Server 模式。
  触发词：「搜索我的文档」「用qmd」「qmd search」「qmd query」「索引文档」「文档搜索」「语义搜索本地文件」。
  排除条件：搜索结果读取走 qmd get（qmd:// URI 转真实路径）；非本地文档检索（如网页/API）不归本 skill。
agent_created: true
---

# QMD — 本地文档索引与搜索

`qmd` 是本地命令行文档搜索引擎：全文检索（BM25）→ 向量语义搜索 → 混合查询 + LLM 重排序。完整命令清单见 `references/commands.md`。

## Default Stance

### 核心原则

- **先搜后读**：搜索返回 `qmd://` URI，读文件用 `qmd get` 或转真实路径——URI 不可直接用于文件操作
- **语义搜索先 embed**：`query`/`vsearch` 依赖向量嵌入，必须先 `qmd embed`；`search`（BM25）不依赖
- **Collection 为界**：搜索用 `-c <collection名>` 限定范围，避免跨库噪音
- **Agent 主动触发**：对话中需查本地文档/笔记时主动使用，无需等用户提「qmd」

### 禁止行为

- 绝不把 `qmd://` URI 当真实路径直接读/写（先 `qmd get` 或转换）
- 绝不跳过 `qmd embed` 直接用向量搜索（结果为空或报错）
- 绝不直接操作 `~/.cache/qmd/index.sqlite`（用 qmd 命令管理）
- 绝不修改用户文档内容——qmd 只读索引与搜索

---

## Workflow

### 第一步：识别意图（路由表）

| 用户意图 | 命令 | 说明 |
|:---|:---|:---|
| "搜索 XX"、"找一下 XX" | `qmd query` | 混合搜索+重排序（推荐，需先 embed） |
| "搜关键词 XX"、"精确搜" | `qmd search` | BM25 全文检索，不依赖 embedding |
| "语义搜索 XX" | `qmd vsearch` | 纯向量相似度搜索 |
| "看看索引状态" | `qmd status` | 查看索引统计 |
| "更新索引"、"同步文档" | `qmd update` | 重新扫描文件 |
| "跑 embedding" | `qmd embed` | 生成向量嵌入 |

### 第二步：关键词快速定位（模式一）

用户提到具体主题/股票/公司名时：

```bash
qmd search "关键词" -c obsidian --json -n 10   # 不依赖 embedding，立即可用
qmd get qmd://obsidian/旧文件/个股研究/xxx.md   # 读取内容
```

### 第三步：语义理解搜索（模式二）

用户描述概念/场景而非精确关键词时：

```bash
qmd embed   # 确保向量已生成
qmd query "语义查询" -c obsidian -n 10 --json
```

### 第四步：URI → 真实路径转换（模式三）

`qmd://` 前缀 URI 转真实路径规则：`qmd://obsidian/旧文件/个股研究/耀才证券.md` ↔ `{vault 路径}/旧文件/个股研究/耀才证券.md`。用 `qmd get` 直接输出内容，或用 shell 拼接真实路径。

### 第五步：检查索引新鲜度（模式四）

```bash
qmd status            # 确认文件已索引
qmd update && qmd embed   # 有新文件未索引时
```

---

## Output Format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| command_used | string | 实际执行的 qmd 命令 |
| results | list[string] | 搜索结果（`qmd://` URI 或内容片段） |
| collection | string | 搜索范围（如 obsidian） |
| files_read | list[string] | 通过 qmd get 读取的文件真实路径 |
| needs_embed | boolean | 是否需要先执行 qmd embed |

---

## Relative Files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| 查完整命令/参数 | references/commands.md | 索引管理/搜索/文档获取/MCP/工作流速查 | 读取 |
| 执行搜索 | qmd CLI（全局安装） | 实际查询命令 | **执行** |

---

## Source Hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户意图（路由表匹配） |
| 2 | qmd CLI 实际输出（索引状态、搜索结果） |
| 3 | references/commands.md（命令参数） |

---

## 自检

- [ ] 搜索前是否确认 embedding 状态（query/vsearch 需 embed）？
- [ ] 返回的 `qmd://` URI 是否已转换/用 qmd get 读取？
- [ ] 是否用 `-c` 限定了 collection？
- [ ] 索引是否最新（新文件是否需 update）？
