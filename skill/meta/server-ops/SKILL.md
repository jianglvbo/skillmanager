---
name: server-ops
description: 云服务器（106.55.14.116）运维执行器。管理 Nginx HTTPS 入口（www.jianglvbo.site，80/443 反代）、问答网页「问」（8700）的部署/状态/重启，MySQL（investment_kb + fitness_plan）管理与备份。投资看板（investment-console）**仅本地运行**（本机 launchd 8698 + ~/Project/investment-console，vault=iCloud 绝对基准，2026-09-03 用户拍板服务器版已删）。fitness-console（8699）已退役全删（2026-09-21 用户拍板，服务器无残留）。触发词：「服务器」「部署到服务器」「服务器状态」「重启服务」「备份 MySQL」「HTTPS 证书」「106.55.14.116」「server-ops」。排除：本地 Obsidian 操作（走 investment-framework）、本地投资看板运维。
license: MIT
agent_created: true
metadata:
  version: "2.3.0"
  short-description: 云服务器运维（Nginx HTTPS + 问答 8700 + MySQL + Redis）
---

# 服务器运维（server-ops）

> **现状（2026-09-21）**：服务器承载 **Nginx HTTPS（www.jianglvbo.site，80 跳转 + 443 反代 8700）+ 问答「问」(8700) + MySQL（investment_kb / fitness_plan）+ Redis 缓存**。fitness-console（8699）已退役，unit/目录/`fitness` 库全部删除（2026-09-21 用户拍板，服务器无残留）。investment-console 仅本地运行（2026-09-03 拍板），数据批量同步到本服务器 MySQL，本 skill 不负责其部署。

## Default stance

### 核心原则
1. **统一账号**：所有操作默认用 `jianglb@106.55.14.116`（免密 sudo）；root 仅本地（SSH 已禁，勿尝试 root 登录）
2. **凭据零明文**：SKILL.md 与命令中一律不出现密码；需要凭据时读 `$HOME/.config/server-ops/credentials.md`（0600，通用位置，各 agent 共用）
3. **只读先于变更**：查状态/验证等只读操作直接执行；重启/同步/改配置等变更操作，先说明影响再执行
4. **脚本优于脑补**：状态检查有现成脚本（scripts/status.sh），执行脚本看输出，不手工拼命令

### 禁止行为
1. 禁止在输出/日志/命令回显中明文打印密码（用 `MYSQL_PWD`/`-p` 交互/`sudo mysql` 免密）
2. 禁止 `git clone` investment-notes 走 GitHub（已知 TLS 中断失败）——统一用本机 rsync 同步 vault（注：vault 推送服务器已随服务器版退役，此条仅限本地↔本机副本场景）
3. 禁止把 MySQL bind-address 从 127.0.0.1 改公网（当前已公网开放，属历史遗留；新部署一律本机 + SSH 隧道）
4. 禁止在服务器上直接编辑生产配置而不先备份（改前 `cp x x.bak-日期`）

## Workflow

### 第一步：确认连接
- 本机直接 `ssh 106.55.14.116`（**2026-08-31 已配 SSH 密钥免密**：`~/.ssh/config` 已登记 Host 106.55.14.116 / User jianglb / IdentityFile id_rsa，`~/.ssh/id_rsa.pub` 已装入服务器 authorized_keys）
- 需要密码兜底或远程跑命令：`expect scripts/sshrun.exp "<远程命令>"`（自动从 credentials.md ## SSH 段**按行**提取密码，密钥失效时兜底；勿用正则跨段抓密码——会抓到 MySQL 段）
- 服务器本机 MySQL 用 `sudo mysql`（root auth_socket 免密）或 `mysql -u jianglb -p`

### 第二步：查状态（只读，直接执行）
```bash
scripts/status.sh（skill 内相对路径；检查 fitness/qa/mysql + investment_kb 行数快检；[--json] 输出结构化）
# 等效 ssh 单行：ssh jianglb@106.55.14.116 "sudo systemctl status fitness-console qa mysql --no-pager | grep -E 'Active|●'"
```

### 第三步：备份（定期做）
- MySQL 逻辑备份：
```bash
ssh jianglb@106.55.14.116 "sudo mysqldump investment_kb | gzip > /home/jianglb/backup/investment_kb-$(date +%Y%m%d).sql.gz"
```
- fitness 数据目录（JSON）：
```bash
ssh jianglb@106.55.14.116 "tar czf /home/jianglb/backup/fitness-data-$(date +%Y%m%d).tgz -C /home/jianglb fitness-console/data"
```
- 建议 cron 每周一执行（可后配）

### 第三步之二：Redis 缓存（2026-09-12 新装）
- **用途**：投资看板读 `investment_kb` 的缓存层。看板跑在本机 macOS，读库要跨公网 RTT，缓存把「N 次查询」压成「1 次 GET」。
- **安装位置**：`/home/jianglb/redis`（源码编译，v8.10.1；`bin/`、`conf/redis.conf`、`data/`、`log/` 全在 home 下，删除 = `rm -rf /home/jianglb/redis`）
- **服务**：systemd 单元 `redis-investment`（User=jianglb，`sudo systemctl {status,restart,stop} redis-investment`，已 enable 开机自启）
- **配置要点**：`bind 0.0.0.0` + `requirepass`（28 位 ≈167 bits）；`maxmemory 256mb` + `allkeys-lru`；**纯缓存不持久化**（`save ""`、`appendonly no`，所以**重启 Redis = 缓存全清**，看板会短暂回落到查库，属预期）
- **命令面加固（2026-09-12，公网可达后追加）**：改名禁用 `CONFIG/DEBUG/MONITOR/REPLICAOF/SLAVEOF/MODULE/SAVE/BGSAVE/BGREWRITEAOF/MIGRATE/CLIENT/ACL/FAILOVER/PSYNC/SYNC/REPLCONF` + 原有的 `FLUSHALL/FLUSHDB/KEYS/SHUTDOWN`。改前备份 `redis.conf.bak-20260912`；改动后重启 Redis 并复验常用命令（PING/GET/SET/SCAN/INFO/DBSIZE 正常）
- **性能实测（2026-09-12）**：单次 1KB GET 往返 **直连 61ms（中位） vs SSH 隧道 114ms** → **直连快约 1.8×**，故看板默认走直连；隧道保留为备用（加密、不依赖出口 IP）
- **迁移/换机提示**：Redis 里**没有任何独立数据**（纯缓存，随时可清空），换机或重装只需照本段重建实例 + 改 `config.json` 的 `redis` 段即可；数据真相始终在 MySQL（`investment_kb`）与 vault
- **接入点（2026-09-12 用户放开 6379 后）**：看板**直连 `106.55.14.116:6379`**（安全组入站 TCP:6379 已放行，曾因规则加错安全组导致不通——抓包 0 SYN + 外部节点探测可定位）。**备用通路**：SSH 隧道（launchd `com.investment-redis-tunnel`，本地 6379 → 服务器 127.0.0.1:6379），切回用 `bash ~/Project/investment-console/scripts/redis-endpoint.sh tunnel`
- **两条通路都验证过的命令**：`bash ~/Project/investment-console/scripts/redis-endpoint.sh check`（先探测再改配置）；`direct`/`tunnel` 一键切换并复验看板缓存连接
- **注意**：直连 RTT 实测中位 ~57ms（移动网到腾讯云一跳），与隧道相当；直连省掉 SSH 加密转发但**依赖本机出口 IP 会变**（移动网），隧道更稳
- **凭据**：`~/.config/server-ops/credentials.md` 的 `## Redis` 段（0600）；看板侧写在 `~/Project/investment-console/config.json` 的 `redis` 段（该文件已被 .gitignore）
- **一键体检**：`bash ~/Project/investment-console/scripts/cache-stats.sh`（看板侧进程统计 + 服务器 Redis 内存/键数 + 隧道状态）
- **查看存了什么（2026-09-12 新增，本机直连、不依赖 redis-cli/ssh）**：
  ```bash
  cd ~/Project/investment-console
  python3 scripts/redis-inspect.py keys               # 所有 key：键 / 大小 / 剩余 TTL / 值预览
  python3 scripts/redis-inspect.py keys 'ik:statements:*'  # 按 pattern 过滤
  python3 scripts/redis-inspect.py get '<key>'        # 单键的值（自动解压 gzip + 格式化 JSON）
  python3 scripts/redis-inspect.py raw '<key>'        # 原始值（看 g: 前缀）
  python3 scripts/redis-inspect.py info               # 键数 / epoch / 内存 / 上限 / keyspace
  python3 scripts/redis-inspect.py cmd TTL '<key>'    # 任意命令
  bash scripts/redis.sh                                # 交互式 redis-cli（要原生命令时用）
  ```
  ⚠️ **`KEYS *` 不可用**（已按加固策略改名禁用，阻塞式全库遍历）：取全量用 `SCAN` / `redis-inspect.py keys` / `redis-cli --scan`。
- **缓存内容是什么**：全部是看板读接口的结果（`ik:statements|subject|subjects|trades|bloggerProfile|bloggerCounts:v<epoch>:<hash>`）+ 一个 `ik:epoch` 版本号键；
  **无持久化 → 重启 Redis 即全空**；键都带 300s TTL（仅 `ik:epoch` 无 TTL）。
- **客户端健壮性（2026-09-12，公网链路的三个坑）**：① **空闲连接会被 NAT 静默掐死** → 命令超时即判定连接已死并重连 + **15s 心跳保活**（实测空闲 45s 后首次读仍命中）；② 失败退避为**指数**（1s→15s，成功后归零）；③ `ik:epoch` 键若被 LRU 淘汰，**读取端不回落成固定值**（那会读到本该失效的老键）而是生成随机 epoch + `SET NX`，`cacheBump` 用 `SET` 而非 `INCR`。
- **安全提醒**：Redis 监听 0.0.0.0 时全靠 `requirepass` 兜底；若要收紧，把安全组规则限定到本机出口 IP，或维持 loopback + SSH 隧道（本 skill 的推荐姿势）

### 第四步：investment_kb 数据链路（2026-09-03 起本地直连）
- **架构**：本地看板（`~/Project/investment-console`，launchd 8698，vault=iCloud 绝对基准）→ buildIndex → `syncFilesToDb` **批量同步**（多行 upsert ~20 查询，串行队列）→ 服务器 MySQL investment_kb（远端唯一共享库）
- **vault 不再推送服务器**（`vault_sync.sh` 已随服务器版退役 2026-09-03；本机 `migrate_to_mysql.py` 2026-08-31 已退役）——MySQL 的 blogger 表由本地实例维护（files/tags 已退役，改为内存索引）
- 同步范围：只动 blogger 表（files/tags 已退役，改为内存索引）；运营表（refine/review/coarse/trash/prediction 域）一律不碰
- 强制重建本地索引缓存：`POST http://127.0.0.1:8698/api/index/rebuild`
- 库表 DDL 权威：`~/Ai/tools/investment-kb/investment_kb.sql`（**实况 38 表 + 1 只读视图**：六张 `statement_*` 类型表 + `statement` UNION 视图 + 关联表 + `post_history` 等；单 `dict` 表承载全部码值。2026-09-13 表名/列名规范化后由 `scripts/export-schema.js` 从实库生成）
- **本地服务管理**：launchd 单元 `com.investment-console`（`launchctl kickstart -k gui/501/com.investment-console` 重启）；启动前置：config.json + vault 可达 + node_modules 含 mysql2
- 本地 MCP 端点：`http://127.0.0.1:8698/mcp`（token = config.json `mcpToken`；MCP 客户端配置里指向本地端点即可）

### 第五步：Nginx HTTPS 入口（www.jianglvbo.site，2026-09-21 上线）
- **架构**：Nginx 监听 80/443（default_server）——443 按 SNI 反代本机 `127.0.0.1:8700`（问答「问」），80 一律 `301` → `https://www.jianglvbo.site`；default 站点已删，全站唯一 server 配置在 `/etc/nginx/sites-available/jianglvbo.site`（软链 sites-enabled）
- **证书**：`/etc/nginx/ssl/jianglvbo.site_bundle.pem`（644）+ `.key`（600），腾讯云 TrustAsia DV，SAN = jianglvbo.site + www.jianglvbo.site，**2026-12-20 到期**；续期 = 腾讯云控制台重新申请 → 下载 Nginx 版 → 覆盖 ssl 目录两个文件 → `sudo nginx -t && sudo systemctl reload nginx`
- **坑：服务器 Nginx 1.18 不支持 `http2 on;` 独立指令**（1.25+ 语法），必须写 `listen 443 ssl http2;`
- **公网访问 80/443 须腾讯云安全组放行**（只能用户在控制台点；服务器 ufw/firewalld 均 inactive）
- 改配置流程：`sudo cp x x.bak-日期` → 改 → `sudo nginx -t` → `sudo systemctl reload nginx`

### 第六步：MySQL 管理
- **现役库**：`investment_kb`（投资看板远端唯一共享库）+ `fitness_plan`（中文健身动作数据集，属本地 `~/Project/fitness-plan` 仓库 db/schema.sql）；`fitness`/`fitness_dev` 已随 fitness-console 退役删除（2026-09-21 确认不存在）
- 本机远程连：先建隧道 `ssh -L 3306:127.0.0.1:3306 jianglb@106.55.14.116`（另开终端），再连 `127.0.0.1:3306`；或直连公网 3306（pymysql/mysql 客户端）
- 或服务器本机：`sudo mysql`（root 免密）/ `mysql -u jianglb -p`
- 建库：`CREATE DATABASE IF NOT EXISTS xxx DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`

## Output format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| 服务 | string | nginx / qa / mysql / redis-investment（investment-console 服务器版已删，本地管理不在本 skill 范围） |
| 状态 | string | active / failed / inactive |
| HTTP 码 | int | 8700 本地 curl；443 用本机 SNI curl（--resolve）验证（服务器侧）；8698 仅本地验证 |
| 数据校验 | string | investment_kb 行数快检 / overview API 与预期对比 |
| 影响说明 | string | 变更操作前必须给出 |

## Relative files

| 场景 | 加载文件 | 方式 |
|:---|:---|:---|
| 服务器布局/端口/目录/数据库连接详表 | `references/layout.md` | 读取 |
| 需要凭据（密码等） | `$HOME/.config/server-ops/credentials.md` | 读取（注意不输出到对话） |
| 查服务器各站 + MySQL 状态 | `scripts/status.sh` | 执行 |
| 远程执行命令（密码兜底） | `scripts/sshrun.exp "<远程命令>"` | 执行（expect；密钥失效时自动兜底） |
| ~~vault_sync.sh / rsyncrun.exp~~ | 已退役（本地 .retired-20260903 留档；仓库版保留为历史参考） | 投资看板服务器版已删，勿再使用 |

## Source hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式约定（默认 jianglb、MySQL 数据目录 /home/jianglb/mysql、vault 用 rsync） |
| 2 | 部署实测经验（2026-08-30：AppArmor/注释行 datadir/GitHub clone 失败） |
| 3 | 通用运维最佳实践（变更前备份、只读先于变更、凭据隔离） |

## 自检

- [ ] 连接是否用 jianglb 且无明文密码出现在命令/输出？
- [ ] 变更操作（重启/改配置/删数据）前是否备份并说明影响？
- [ ] investment-console 是否按「仅本地」处理（不做服务器部署/同步，误触服务器残留引用能识别为已退役）？
- [ ] fitness-console 相关引用能识别为已退役（2026-09-21 全删），不尝试重启/部署？
- [ ] 新端口公网访问是否提醒安全组放行（服务器防火墙不挡端口）？
- [ ] 改 Nginx 后是否 `nginx -t` 再 reload？证书是否在有效期内（到期 2026-12-20）？
