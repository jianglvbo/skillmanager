---
name: server-ops
description: 云服务器（106.55.14.116）运维执行器。管理减脂塑形控制台（8699）的部署/状态/重启，以及 MySQL（investment_kb + fitness）管理与备份。⚠️ 投资知识库看板 investment-console 已于 2026-09-02 迁回本地运行（读本地 vault、连远程 MySQL），服务器不再部署它、不再同步 vault。触发词：「服务器」「部署到服务器」「服务器状态」「重启服务」「备份 MySQL」「106.55.14.116」「server-ops」。排除：本地 Obsidian 操作（走 investment-framework）、本地投资看板运维。
---

# 服务器运维（server-ops）

> **2026-09-02 架构变更**：投资知识库看板 investment-console 不再部署在本服务器，改本地运行（`~/Project/investment-console`，launchd `com.investment-console`，端口 8698，读本地 iCloud vault、连远程 MySQL `106.55.14.116:3306`）。服务器现仅承载 **MySQL（investment_kb / fitness）+ fitness-console(8699)**。原「vault 同步」「investment-console 部署/重启」流程作废（下方相关段已标注）。

## Default stance

### 核心原则
1. **统一账号**：所有操作默认用 `jianglb@106.55.14.116`（免密 sudo）；root 仅本地（SSH 已禁，勿尝试 root 登录）
2. **凭据零明文**：SKILL.md 与命令中一律不出现密码；需要凭据时读 `$HOME/.config/server-ops/credentials.md`（0600，通用位置，各 agent 共用）
3. **只读先于变更**：查状态/验证等只读操作直接执行；重启/同步/改配置等变更操作，先说明影响再执行
4. **脚本优于脑补**：vault 同步、状态检查有现成脚本（scripts/），执行脚本看输出，不手工拼命令

### 禁止行为
1. 禁止在输出/日志/命令回显中明文打印密码（用 `MYSQL_PWD`/`-p` 交互/`sudo mysql` 免密）
2. 禁止 `git clone` investment-notes 走 GitHub（已知 TLS 中断失败）——统一用本机 rsync 同步 vault
3. 禁止把 MySQL bind-address 从 127.0.0.1 改公网（当前已公网开放，属历史遗留；新部署一律本机 + SSH 隧道）
4. 禁止在服务器上直接编辑生产配置而不先备份（改前 `cp x x.bak-日期`）

## Workflow

### 第一步：确认连接
- 本机直接 `ssh 106.55.14.116`（**2026-08-31 已配 SSH 密钥免密**：`~/.ssh/config` 已登记 Host 106.55.14.116 / User jianglb / IdentityFile id_rsa，`~/.ssh/id_rsa.pub` 已装入服务器 authorized_keys）
- 需要密码兜底或远程跑命令：`expect scripts/sshrun.exp "<远程命令>"`（自动从 credentials.md ## SSH 段**按行**提取密码，密钥失效时兜底；勿用正则跨段抓密码——会抓到 MySQL 段）
- 服务器本机 MySQL 用 `sudo mysql`（root auth_socket 免密）或 `mysql -u jianglb -p`

### 第二步：查状态（只读，直接执行）
```bash
ssh jianglb@106.55.14.116 "sudo systemctl status fitness-console mysql --no-pager | grep -E 'Active|●'"
# 或执行脚本
scripts/status.sh（skill 内相对路径）
```

### 第三步：（已作废）vault 同步
- 投资看板已本地运行、直读本地 vault，**不再需要把 vault 同步到服务器**。`scripts/vault_sync.sh` 保留仅作历史参考。

### 第四步：备份（定期做）
- MySQL 逻辑备份：
```bash
ssh jianglb@106.55.14.116 "sudo mysqldump investment_kb | gzip > /home/jianglb/backup/investment_kb-$(date +%Y%m%d).sql.gz"
```
- 两站数据目录（JSON）：
```bash
ssh jianglb@106.55.14.116 "tar czf /home/jianglb/backup/data-$(date +%Y%m%d).tgz -C /home/jianglb fitness-console/data"
```
- 建议 cron 每周一执行（可后配）

### 第四步半：（已作废）服务器端 vault → MySQL 同步
- 现由**本地** investment-console（`syncFilesToDb`，`disableDbSync=false`）扫本地 vault 写远程 MySQL 派生表（files/tags/bloggers）；服务器不再有 investment-console 进程做这件事。
- 强制重建索引：本地 `POST http://127.0.0.1:8698/api/index/rebuild`。库表 DDL 仍见 `sql/investment_kb.sql` + `sql/investment_kb_consoles.sql`（预测域 4 业务表 + 4 字典）。

### 第五步：（已作废）investment-console 部署
- 投资看板不再部署到服务器，本地运行即可（launchd `com.investment-console`）。fitness-console 部署见下一节。

### fitness-console 部署执行（开发规范见 fitness-dev-workflow skill）
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
| 服务 | string | fitness-console / mysql（investment-console 已迁本地） |
| 状态 | string | active / failed / inactive |
| HTTP 码 | int | 8698/8699 本地 curl 验证 |
| 数据校验 | string | overview API 的 wikiTotal/bloggerCount 与预期对比 |
| 影响说明 | string | 变更操作前必须给出 |

## Relative files

| 场景 | 加载文件 | 方式 |
|:---|:---|:---|
| 服务器布局/端口/目录/数据库连接详表 | `references/layout.md` | 读取 |
| 需要凭据（密码等） | `$HOME/.config/server-ops/credentials.md` | 读取（注意不输出到对话） |
| 查两站 + MySQL 状态 | `scripts/status.sh` | 执行 |
| ~~本机 vault → 服务器同步~~（已作废，看板本地运行） | `scripts/vault_sync.sh` | 历史参考 |
| 远程执行命令（密码兜底） | `scripts/sshrun.exp "<远程命令>"` | 执行（expect；密钥失效时自动兜底） |
| ~~投资控制台部署~~（已作废，看板本地运行） | `scripts/rsyncrun.exp` | 历史参考 |

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
- [ ] 是否知悉 investment-console 已本地运行、服务器不再部署它/不再同步 vault（勿再对服务器跑 investment 部署或 vault_sync）？
- [ ] 变更操作（重启/改配置/rsync --delete）前是否说明了影响？
- [ ] 数据库查询是否走隧道/本机 sudo mysql，端口未直连公网？
- [ ] 踩坑规则（GitHub clone 失败、AppArmor、bind-address）是否遵守？
