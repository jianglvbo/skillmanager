---
name: server-ops
description: 云服务器（106.55.14.116）运维执行器。管理减脂塑形控制台（8699）、问答网页「问」（8700）的部署/状态/重启，MySQL（investment_kb + fitness）管理与备份。投资看板（investment-console）**仅本地运行**（本机 launchd 8698 + ~/Project/investment-console，vault=iCloud 绝对基准，2026-09-03 用户拍板服务器版已删），本 skill 不再负责其服务器部署。触发词：「服务器」「部署到服务器」「服务器状态」「重启服务」「备份 MySQL」「106.55.14.116」「server-ops」。排除：本地 Obsidian 操作（走 investment-framework）、本地投资看板运维。
license: MIT
agent_created: true
metadata:
  version: "2.2.0"
  short-description: 云服务器运维（fitness 8699 + 问答 8700 + MySQL）
---

# 服务器运维（server-ops）

> **2026-09-02/09-03 架构变更**：投资知识库看板 investment-console 不再部署在本服务器——服务器版已删（2026-09-03 用户拍板），改本地运行（`~/Project/investment-console`，launchd `com.investment-console`，端口 8698，读本地 iCloud vault、数据批量同步到本服务器 MySQL investment_kb）。服务器现承载 **fitness-console(8699) + 问答「问」(8700) + MySQL（investment_kb / fitness）**。原「vault 同步」「investment-console 服务器部署/重启」流程作废（相关段已标注/退役）。

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
- **接入点（2026-09-12 用户放开 6379 后）**：看板**直连 `106.55.14.116:6379`**（安全组入站 TCP:6379 已放行，曾因规则加错安全组导致不通——抓包 0 SYN + 外部节点探测可定位）。**备用通路**：SSH 隧道（launchd `com.investment-redis-tunnel`，本地 6379 → 服务器 127.0.0.1:6379），切回用 `bash ~/Project/investment-console/scripts/redis-endpoint.sh tunnel`
- **两条通路都验证过的命令**：`bash ~/Project/investment-console/scripts/redis-endpoint.sh check`（先探测再改配置）；`direct`/`tunnel` 一键切换并复验看板缓存连接
- **注意**：直连 RTT 实测中位 ~57ms（移动网到腾讯云一跳），与隧道相当；直连省掉 SSH 加密转发但**依赖本机出口 IP 会变**（移动网），隧道更稳
- **凭据**：`~/.config/server-ops/credentials.md` 的 `## Redis` 段（0600）；看板侧写在 `~/Project/investment-console/config.json` 的 `redis` 段（该文件已被 .gitignore）
- **一键体检**：`bash ~/Project/investment-console/scripts/cache-stats.sh`（看板侧进程统计 + 服务器 Redis 内存/键数 + 隧道状态）
- **安全提醒**：Redis 监听 0.0.0.0 时全靠 `requirepass` 兜底；若要收紧，把安全组规则限定到本机出口 IP，或维持 loopback + SSH 隧道（本 skill 的推荐姿势）

### 第四步：investment_kb 数据链路（2026-09-03 起本地直连）
- **架构**：本地看板（`~/Project/investment-console`，launchd 8698，vault=iCloud 绝对基准）→ buildIndex → `syncFilesToDb` **批量同步**（多行 upsert ~20 查询，串行队列）→ 服务器 MySQL investment_kb（远端唯一共享库）
- **vault 不再推送服务器**（`vault_sync.sh` 已随服务器版退役 2026-09-03；本机 `migrate_to_mysql.py` 2026-08-31 已退役）——MySQL 的 files/tags/bloggers 派生数据由本地实例维护
- 同步范围：只动 files/tags/bloggers 三张文件派生表；运营表（refine/review/coarse/trash/prediction 域）一律不碰
- 强制重建本地索引缓存：`POST http://127.0.0.1:8698/api/index/rebuild`
- 库表 DDL 权威：`~/Ai/tools/investment-kb/investment_kb.sql`（16 表，单 dict 表）
- **本地服务管理**：launchd 单元 `com.investment-console`（`launchctl kickstart -k gui/501/com.investment-console` 重启）；启动前置：config.json + vault 可达 + node_modules 含 mysql2
- 本地 MCP 端点：`http://127.0.0.1:8698/mcp`（token = config.json `mcpToken`，~/.workbuddy/mcp.json 已指向本地）

### 第五步：fitness-console 部署执行（开发规范见 fitness-dev-workflow skill）
- **职责边界**：本 skill 只负责服务器侧运维与**部署执行**；开发规范（环境边界/双库隔离/本地工作流/git/配置双轨/部署触发规则）→ 调用 **fitness-dev-workflow** skill，两 skill 由 agent 按任务自判断调用
- **双库双用户（生产侧）**：服务器 config.json 指向 `fitness` 库 / `jianglb` 用户（host=127.0.0.1 本机）；开发库 fitness_dev/jianglb_dev 只供本地开发，服务器生产进程不碰开发库
- **rsync 部署命令（2026-09-07 用户指示：代码改完默认直接部署，无需等「部署」指令；变更前仍须说明影响，部署后要做线上验收）**：
```bash
rsync -az --exclude ".DS_Store" --exclude "config.json" --exclude "keys.json" --exclude "data" --exclude "node_modules" --exclude "web/exercise-media" -e "ssh -p 22" ~/Project/fitness-console/ jianglb@106.55.14.116:/home/jianglb/fitness-console/
ssh jianglb@106.55.14.116 "sudo systemctl restart fitness-console"
```
- **决策点**：改的是 server.js 或 config.json → 必须重启；只改 web/ 静态文件 → 不需重启
- **生产库 DDL/DML**：需先在 fitness_dev 验证 → 说明影响 → 执行（或随部署告知）
- **SSH 密码**：凭据文件 `$HOME/.config/server-ops/credentials.md`（注意该文件可能有多行「密码」，SSH 密码取第 7 行；expect heredoc 必须用引号 `<< 'EOF'`，否则 `\r` 被 shell 吃掉致密码错误）

### 第六步：MySQL 管理
- **双库双用户（2026-08-30 起）**：
  - `fitness_dev` = 开发库（用户 `jianglb_dev`，仅 fitness_dev 权限）——本地开发/验证用，**操作随便改**
  - `fitness` = 生产库（用户 `jianglb`）——生产数据，**DDL/DML 需先在 fitness_dev 验证 → 说明影响 → 执行**（或随部署告知）
- 本机远程连：先建隧道 `ssh -L 3306:127.0.0.1:3306 jianglb@106.55.14.116`（另开终端），再连 `127.0.0.1:3306`；或直连公网 3306（pymysql/mysql 客户端）
- 或服务器本机：`sudo mysql`（root 免密）/ `mysql -u jianglb -p`
- 建库：`CREATE DATABASE IF NOT EXISTS xxx DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
- 开发库从生产同步：`SHOW CREATE TABLE fitness.x` 建表 + `INSERT INTO fitness_dev.x SELECT * FROM fitness.x`

## Output format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| 服务 | string | fitness-console / qa / mysql（investment-console 服务器版已删，本地管理不在本 skill 范围） |
| 状态 | string | active / failed / inactive |
| HTTP 码 | int | 8699/8700 本地 curl 验证（服务器侧）；8698 仅本地验证 |
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
- [ ] 数据库操作是否区分 dev/生产库？生产库 DDL/DML 是否先经 fitness_dev 验证并说明影响？
- [ ] 代码改动后是否已默认部署并做线上验收（2026-09-07 起无需等「部署」指令；变更前仍说明影响，重启只在 server.js/config 变更时做）？
- [ ] investment-console 是否按「仅本地」处理（不做服务器部署/同步，误触服务器残留引用能识别为已退役）？
- [ ] 变更操作（重启/改配置/rsync --delete）前是否说明了影响？
- [ ] 数据库查询是否走隧道/本机 sudo mysql，端口未直连公网？
- [ ] 踩坑规则（AppArmor、bind-address、安全组放行）是否遵守？
