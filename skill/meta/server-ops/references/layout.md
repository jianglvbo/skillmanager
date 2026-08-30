# 服务器布局详表（106.55.14.116）

## 主机信息
- 系统: Ubuntu 22.04.5 LTS（4C4G 40G，上海）
- SSH: `jianglb@106.55.14.116:22`（免密 sudo；ubuntu 备用；root 仅本地）
- 防火墙: ufw inactive（仅云安全组控制公网入口）
- 公网开放端口: 22 / 8698 / 8699 / 3306（3306 为历史遗留，建议改隧道）

## 服务与端口
| 服务 | 端口 | systemd unit | 目录 |
|:---|:---|:---|:---|
| 投资控制台 | 8698 | investment-console.service | /home/jianglb/investment-console |
| 减脂塑形控制台 | 8699 | fitness-console.service | /home/jianglb/fitness-console |
| MySQL | 3306 | mysql.service | 数据 /home/jianglb/mysql |

## 数据与目录
| 路径 | 内容 |
|:---|:---|
| /home/jianglb/vault | 投资知识库 md 快照（659 个，rsync 自本机） |
| /home/jianglb/investment-console/data | 投资看板 JSON 备份（数据主源已迁移 MySQL investment_kb） |
| /home/jianglb/fitness-console/data | 健身 JSON（fitness-data/jlb/whx） |
| /home/jianglb/mysql | MySQL 数据目录（jianglb 用户运行） |
| /etc/systemd/system/*.service | 两站 systemd unit（User=jianglb, Restart=always） |

## 数据库连接
- host: 106.55.14.116:3306（**建议**改回 127.0.0.1 + 本机 SSH 隧道：`ssh -L 3306:127.0.0.1:3306 jianglb@106.55.14.116`）
- **业务库 investment_kb**：21 张表（10 码值 dict_* + 11 业务），DDL 在 ~/Project/investment-console/sql/investment_kb.sql；vault 为绝对基准，刷新=本机跑 scripts/migrate_to_mysql.py
- user: jianglb（@'%' 远程 + @localhost 本机），密码见 credentials/server.md
- root: 仅 localhost，auth_socket 免密（sudo mysql）
- 注意：**两站本身不用 MySQL**（JSON 文件存储）；MySQL 供外部数据管理/未来用途

## MCP 端点（2026-08-30 上线）
- investment-console 暴露 MCP Streamable HTTP 端点：`http://106.55.14.116:8698/mcp`（POST，JSON 单响应，无 SSE）
- 鉴权：Bearer Token，读环境变量 `MCP_TOKEN`（systemd drop-in `/etc/systemd/system/investment-console.service.d/mcp.conf`，0600；token 另存 credentials/server.md）
- 无 token / token 错 → 401；GET /mcp → 405；仅 POST
- 22 个工具（overview / vault 文件 CRUD / blogger CRUD / tags / logs / git_*）；tools/list 与 tools/call 共用 stdio 模式的 handleMcpMessage
- 代码：server.js 内 `handleMcpHttp` / `handleMcpMessage`；旧版备份 `server.js.bak-20260830`
- 改 server.js 后需 `sudo systemctl daemon-reload && sudo systemctl restart investment-console`
- MCP 连接方式由各 agent 环境配置（HTTP 端点 /api/mcp），不写死具体 agent 路径

## 已知坑（2026-08-30 实测）
1. **GitHub clone investment-notes 必失败**（GnuTLS TLS 中断）→ 一律本机 rsync
2. **Ubuntu mysqld.cnf 的 datadir 是注释行**（`# datadir`）→ 改需 sed 替换注释行本身
3. **改 MySQL datadir 必须同步 AppArmor**（/etc/apparmor.d/local/usr.sbin.mysqld）
4. **investment server.js 原监听 127.0.0.1** → 公网版已改 0.0.0.0（部署时已做）
5. 服务器版为只读展示：无 Obsidian/DeepSeek/skill，"打开 Obsidian/评分/加工/审查"按钮不可用
6. 云安全组入口（云控制台）：22/8698/8699/3306 已放行

## 待办
- [ ] SSH 密钥登录（禁密码）
- [ ] MySQL 3306 改回本机 + 隧道（或独立强密码）
- [ ] 密码分离（SSH/MySQL）
- [ ] 备份 cron（每周，mysqldump investment_kb）
- [x] 数据落地 MySQL（2026-08-30 完成：investment_kb 21 表 + 迁移脚本 + server.js MySQL 化）
