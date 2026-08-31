# Investment Console MCP（投资知识库看板）

投资知识库看板（investment-console）的 MCP 服务，供任何 agent（WorkBuddy / 其他 agent）接入读写投资知识库派生数据。

## 连接信息

| 项 | 值 |
|---|---|
| 类型 | MCP **HTTP**（Streamable HTTP，JSON-RPC 2.0） |
| 端点 | `http://106.55.14.116:8698/mcp` |
| 鉴权 | Header `Authorization: Bearer <token>`（token 由服务器 owner 提供） |
| 请求 | `POST /mcp`，`Content-Type: application/json`，body = JSON-RPC 消息 |

## 前提

- 服务器 `investment-console` 服务运行中（端口 8698，systemd: `investment-console.service`）
- 数据源：Obsidian vault 派生 MySQL（`investment_kb` 库）——**vault 为绝对基准**，MySQL 为派生数据
- 服务器 config.json 含 `mcpToken`（与服务端鉴权一致）

## 工具清单（24 个）

| 类别 | 工具 |
|---|---|
| 知识库统计 | `overview`（全库统计：fileCount/bloggerCount/tags/files 树） |
| 文件操作 | `list_files`、`read_file`、`write_file`、`delete_file`、`unmark_delete`、`list_pending_delete`、`purge_pending_delete` |
| 回收站 | `list_trash`、`restore_file`、`purge_trash`、`empty_trash` |
| 博主 | `list_bloggers`、`get_blogger`、`add_blogger`、`remove_blogger`、`update_blogger` |
| 标签 | `list_tags` |
| 日志 | `get_logs`、`git_log`、`git_status`、`git_commit` |
| 流水线落库 | `refine_record`（提炼落库）、`review_record`（审查落库） |

## ⚠️ 枚举码硬约束（落库避坑 · 2026-08-31 实测）

`refine_record` / `review_record` 的 `layer`/`category`/`relation`/`type`/`sourceType`/`checks[].status` **优先传 MySQL 字典英文码，传中文会外键报错**（`foreign key constraint fails ... dict_*`）。全量对照见投资框架 skill 的 `investment-refine/references/refine-schema.md`「二B 字典码对照表」，要点：

- `layer`：`my`/`blogger`/`other`/`macro`/`workspace`（**2026-08-31 起兼容中文**：我的/博主/其他/宏观，服务端自动映射；`category`/`relation` 同样兼容中文）
- `category`：`analysis_framework`/`trading_system`/`investment_mentality`/`investment_insight`/`stock`/`industry`/`macro`
- `relation`：`new`/`append`/`complement`/`conflict_check`/`other`
- `type`：`wiki`/`blogger`/`macro`；`sourceType`：`raw`/`coarse`
- 审查 `checks[].status`：仅 `pass`/`warn`/`fail`（无 `info`）

**已知限制（2026-08-31 已修复）**：`refine_record` 此前不接受 `source`/`sourceType` 参数（原文链接不入库），现已支持——`source`=原文链接 markdown、`sourceType`=raw/coarse（缺省按 `from` 路径推断）。

## 调用示例（JSON-RPC）

```bash
# initialize
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  http://106.55.14.116:8698/mcp

# tools/list
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  http://106.55.14.116:8698/mcp

# tools/call（例：overview）
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"overview","arguments":{}}}' \
  http://106.55.14.116:8698/mcp
```

## 接入配置（各 agent 的 MCP 客户端）

```
mcpServers:
  investment-console:
    type: http
    url: http://106.55.14.116:8698/mcp
    headers:
      Authorization: Bearer <token>
```

## 职责边界

- 本 MCP = 控制台域（读 MySQL 派生数据 + vault 文件操作 + 提炼/审查落库）
- 知识库流水线（提炼/审查/粗加工的执行逻辑）走投资框架 skill（`investment-refine` / `investment-review`），落库调用本 MCP 的 `refine_record` / `review_record`（REST POST /api/refine/record、/api/review/record 兼容）
