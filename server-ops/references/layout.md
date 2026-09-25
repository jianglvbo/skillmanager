# 服务器布局详表（106.55.14.116）

## 主机信息
- 系统: Ubuntu 22.04.5 LTS（4C4G 40G，上海）
- SSH: `jianglb@106.55.14.116:22`（免密 sudo；ubuntu 备用；root 仅本地）
- 防火墙: ufw inactive（仅云安全组控制公网入口）
- 公网开放端口: 22 / 8700 / 3306（3306 为历史遗留，建议改隧道）；**80/443 = Nginx HTTPS（2026-09-21 部署，安全组待用户放行）**；8699/8698 已无服务，安全组规则可关

## 服务与端口
| 服务 | 端口 | systemd unit | 目录 |
|:---|:---|:---|:---|
| Nginx HTTPS 入口（www.jianglvbo.site） | 80/443 | nginx.service | 配置 /etc/nginx/sites-available/jianglvbo.site；证书 /etc/nginx/ssl（**2026-12-20 到期**） |
| MySQL | 3306 | mysql.service | 数据 /home/jianglb/mysql |
| 另一半问答（问） | 8700 | qa.service | /home/jianglb/qa |
| ~~投资控制台~~ | ~~8698~~ | （unit 已删 2026-09-03） | **仅本地运行**：本机 launchd `com.investment-dashboard` + `~/Project/investment-dashboard`（vault=iCloud 绝对基准，数据批量同步到本服务器 MySQL investment-dashboard） |
| ~~减脂塑形控制台~~ | ~~8699~~ | fitness-console 退役全删（2026-09-21 用户拍板：unit/目录/fitness 库无残留） | — |

## 数据与目录
| 路径 | 内容 |
|:---|:---|
| /etc/nginx/ssl | jianglvbo.site_bundle.pem（644）+ .key（600）；TrustAsia DV，SAN=裸域+www，2026-12-20 到期 |
| /home/jianglb/mysql | MySQL 数据目录（jianglb 用户运行） |
| /home/jianglb/qa | 问答网页「问」静态站（index.html + server.js，纯静态 node 托管，无数据库；本地源 ~/WorkBuddy/2026-08-26-23-11-26/另一半问答.html） |
| /home/jianglb/backup | 备份目录（mysqldump/tgz，按日期命名） |

## 数据库连接
- host: 106.55.14.116:3306（**建议**改回 127.0.0.1 + 本机 SSH 隧道：`ssh -L 3306:127.0.0.1:3306 jianglb@106.55.14.116`）
- **业务库 investment-dashboard**：**38 表 + 1 只读视图**（表名一律单数；单 dict 表存全部码值；2026-08-31 dict 14→1 整合，2026-09-13 表名/列名规范化），DDL 权威在 `investment-framework/references/investment-dashboard.sql`（由 `~/Project/investment-dashboard/scripts/export-schema.js` 从实库生成，可跑 `verify-schema-replay.js` 校验一致性）
- **数据链路（2026-09-03 起，服务器版已下线）**：本地看板（vault=iCloud 绝对基准）→ buildIndex → 批量同步到本服务器 MySQL investment-dashboard（远端唯一共享库；vault→MySQL 同步已批量化 ~20 查询，串行队列防并发）；`vault_sync.sh` 已随服务器版退役
- user: jianglb（@'%' 远程 + @localhost 本机），密码见 credentials/server.md
- root: 仅 localhost，auth_socket 免密（sudo mysql）
- 现役库：investment-dashboard（投资看板）+ fitness_plan（中文健身动作数据集，属本地 ~/Project/fitness-plan 仓库 db/schema.sql；`fitness`/`fitness_dev` 已随 fitness-console 退役删除）
- 注意：investment-dashboard **重度使用 MySQL**（博主表 blogger + 运营表 refine/review/coarse/prediction 等）

## MCP 端点（investment-dashboard，本地化 2026-09-03）
- 端点：`http://127.0.0.1:8698/mcp`（本机 server.js 内置 handleMcpHttp/handleMcpMessage；POST，JSON 单响应，无 SSE）
- 鉴权：Bearer Token，server.js 读 config.json `mcpToken` 字段（无 token 401 / 带 token 200）
- ~/.workbuddy/mcp.json 的 investment-dashboard 条目已从服务器 URL 切换到 127.0.0.1:8698（2026-09-03）
- 22 个工具（overview / vault 文件 CRUD / blogger CRUD / tags / logs / git_*）
- 服务器版 MCP 已随服务器版下线删除；本地项目留有旧版备份 server.js.bak-20260830

## 已知坑（2026-08-30 实测）
1. **GitHub clone investment-notes 必失败**（GnuTLS TLS 中断）→ 一律本机 rsync
2. **Ubuntu mysqld.cnf 的 datadir 是注释行**（`# datadir`）→ 改需 sed 替换注释行本身
3. **改 MySQL datadir 必须同步 AppArmor**（/etc/apparmor.d/local/usr.sbin.mysqld）
4. **investment server.js 原监听 127.0.0.1** → 公网版已改 0.0.0.0（部署时已做）
5. 服务器版为只读展示：无 Obsidian/DeepSeek/skill，"打开 Obsidian/评分/加工/审查"按钮不可用
6. 云安全组入口（云控制台）：22/8698/8699/8700/3306 已放行。**新端口一律须在云控制台安全组手动放行**（服务器上无 tccli、无云 API 凭据，自动加不了，只能用户去控制台点）——服务器内 ufw/firewalld 均 inactive、iptables 仅有 YJ-FIREWALL-INPUT（只拉黑特定 IP，不挡端口）。**新静态/新服务部署完公网 curl 超时（HTTP 000）时，99% 是安全组没放行**，别去折腾服务器防火墙

## 已知坑（2026-09-03 重建实测，当日服务器版已下线，留档防复发）
1. **investment-dashboard 启动前置条件缺一即循环崩溃退出**（exit 1 + Restart=always 刷屏）：① config.json 存在且 vaultRoot 指向的 vault 已同步；② node_modules 含 mysql2（`npm install mysql2`）；③ web/ 子目录布局（WEB_DIR=ROOT/web，app.js/index.html/style.css/assets 必须在 web/ 下）——此坑同样适用于本地 launchd 部署
2. ~~服务器重建配方~~（2026-09-03 晚用户拍板仅本地运行，服务器 unit/目录/vault 已删，备份 /home/jianglb/backup/investment-dashboard-data-20260903.tgz；若日后再上服务器版按当日工作日志配方可复活）
3. **vault→MySQL 同步已批量化**（2026-09-03）：多行 upsert ~20 查询（原逐行 ~1500 次串行往返曾占满连接池导致全站接口 3-7 分钟超时）；若日后改回逐行逻辑务必重新评估连接池压力
4. 服务器 web/ 为子目录布局（与本地一致）；rsync 多源时源写 `web/`（带斜杠）= 拷贝目录**内容**到目标根

## 已知坑（2026-09-21 Nginx 实测）
1. **Nginx 1.18 不支持 `http2 on;` 独立指令**（1.25+ 语法，nginx -t 报 unknown directive）→ 用 `listen 443 ssl http2;`
2. `systemctl reload nginx` 偶现旧 worker 未退（配置已新、行为仍旧）→ 疑似不生效时 `sudo systemctl restart nginx` 兜底

## 待办
- [ ] 用户在云控制台安全组放行 80/443（HTTPS 公网生效前置）；顺手关 8699/8698 规则
- [ ] 2026-12-20 证书到期前续期（腾讯云重申请 → 覆盖 /etc/nginx/ssl → nginx -t + reload）
- [ ] SSH 密钥登录（禁密码）
- [ ] MySQL 3306 改回本机 + 隧道（或独立强密码）
- [ ] 密码分离（SSH/MySQL）
- [ ] 备份 cron（每周，mysqldump investment-dashboard）
- [x] 数据落地 MySQL（2026-08-30 完成：investment-dashboard 21 表 + 迁移脚本 + server.js MySQL 化）
