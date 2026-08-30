# Investment Console MCP（投资知识库控制台）

投资知识库控制台（investment-console）的 MCP 服务，供任何 agent（WorkBuddy / 其他 agent）接入读写投资知识库派生数据。

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

## 工具清单（22 个）

| 类别 | 工具 |
|---|---|
| 知识库统计 | `overview`（全库统计：fileCount/bloggerCount/tags/files 树） |
| 文件操作 | `list_files`、`read_file`、`write_file`、`delete_file`、`unmark_delete`、`list_pending_delete`、`purge_pending_delete` |
| 回收站 | `list_trash`、`restore_file`、`purge_trash`、`empty_trash` |
| 博主 | `list_bloggers`、`get_blogger`、`add_blogger`、`remove_blogger`、`update_blogger` |
| 标签 | `list_tags` |
| 日志 | `get_logs`、`git_log`、`git_status`、`git_commit` |

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

- 本 MCP = 控制台域（读 MySQL 派生数据 + vault 文件操作）
- 知识库流水线（提炼/审查/粗加工）走投资框架 skill 的 API 契约（`/api/refine/record` 等），不在本 MCP 内
