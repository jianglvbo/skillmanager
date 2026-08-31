---
name: server-ops
description: 云服务器（106.55.14.116）运维执行器。管理投资知识库看板（8698）与减脂塑形控制台（8699）的部署、状态、重启，vault 知识库同步，MySQL 管理与备份。触发词：「服务器」「部署到服务器」「同步 vault」「服务器状态」「重启服务」「备份 MySQL」「投资知识库看板」「106.55.14.116」「server-ops」。排除：本地 Obsidian 操作（走 investment-framework）、不涉及服务器的部署。
---

# 服务器运维（server-ops）

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
ssh jianglb@106.55.14.116 "sudo systemctl status investment-console fitness-console --no-pager | grep -E 'Active|●'"
# 或执行脚本
scripts/status.sh（skill 内相对路径）
```

### 第三步：vault 同步（从本机推送）
- 本机执行（不要在服务器上做）：
```bash
scripts/vault_sync.sh（skill 内相对路径）
```
- 同步内容：vault 全部 md（排除 附件/.obsidian/.plugin_data/.space/.DS_Store/__visit_history）
- 同步后服务器 index 自动重建（server 检测 mtime）；如需强制：重启 investment-console

### 第四步：备份（定期做）
- MySQL 逻辑备份：
```bash
ssh jianglb@106.55.14.116 "sudo mysqldump investment_kb | gzip > /home/jianglb/backup/investment_kb-$(date +%Y%m%d).sql.gz"
```
- 两站数据目录（JSON）：
```bash
ssh jianglb@106.55.14.116 "tar czf /home/jianglb/backup/data-$(date +%Y%m%d).tgz -C /home/jianglb investment-console/data fitness-console/data"
```
- 建议 cron 每周一执行（可后配）

### 第四步半：vault → MySQL 同步（投资知识库看板数据刷新，vault 为绝对基准）
- 架构：vault（.md 本机绝对基准）→ 本机迁移脚本 → 服务器 MySQL（investment_kb）→ 看板只读 MySQL
- **vault 变更后刷新**（本机执行，全量重建，vault 为准）：
```bash
cd ~/Project/investment-console && DB_PASS='<见 credentials>' python3 scripts/migrate_to_mysql.py
```
- 刷新后看板缓存：调用 `POST http://127.0.0.1:8698/api/index/rebuild` 或重启 investment-console（本机测试连公网 MySQL；服务器连 127.0.0.1）
- 库表 DDL：`sql/investment_kb.sql`（21 张：10 码值表 + 11 业务表，全 COMMENT + 外键）；码值枚举一律引用 dict_* 表

### 第五步：部署更新（代码变更后推送）
```bash
# 方式一（推荐）：expect scripts/rsyncrun.exp —— 包装了下方 rsync 命令（排除配置+密码兜底）
# 方式二（直接）：本机 rsync 项目 → 服务器 —— ⚠️ investment 必须排除 config.json / data / node_modules
#   （服务器 config 是生产配置：vaultRoot=/home/jianglb/vault + mysql 段 host=127.0.0.1；
#     data/ 是服务器运营备份；node_modules 由服务器 npm install mysql2 维护）
#   2026-08-30 教训：漏排 config.json 导致服务器 vaultRoot 被本地 iCloud 路径覆盖、服务崩溃循环
rsync -az --exclude ".DS_Store" --exclude "config.json" --exclude "data" --exclude "node_modules" -e "ssh -p 22" ~/Project/investment-console/ jianglb@106.55.14.116:/home/jianglb/investment-console/
# fitness 部署见下方「fitness-console 部署执行」（开发规范走 fitness-dev-workflow skill）
# 重启（服务器若缺 mysql2：cd /home/jianglb/investment-console && npm install mysql2）
ssh jianglb@106.55.14.116 "sudo systemctl restart investment-console fitness-console"
```
- **决策点**：若改的是 server.js 或 config.json → 必须重启；只改 web/ 静态文件 → 不需重启
- **决策点**：服务器 config 若被误覆盖 → 立即修复 vaultRoot 并重启：
```bash
ssh jianglb@106.55.14.116 "python3 -c \"import json;p='/home/jianglb/investment-console/config.json';c=json.load(open(p));c['vaultRoot']='/home/jianglb/vault';json.dump(c,open(p,'w'),ensure_ascii=False,indent=2)\" && sudo systemctl restart investment-console"
```

### fitness-console 部署执行（开发规范见 fitness-dev-workflow skill）
- **职责边界**：本 skill 只负责服务器侧运维与**部署执行**；开发规范（环境边界/双库隔离/本地工作流/git/配置双轨/部署触发规则）→ 调用 **fitness-dev-workflow** skill，两 skill 由 agent 按任务自判断调用
- **双库双用户（生产侧）**：服务器 config.json 指向 `fitness` 库 / `jianglb` 用户（host=127.0.0.1 本机）；开发库 fitness_dev/jianglb_dev 只供本地开发，服务器生产进程不碰开发库
- **rsync 部署命令（等用户明确说「部署」后才执行）**：
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
| 服务 | string | investment-console / fitness-console / mysql |
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
| 本机 vault → 服务器同步 | `scripts/vault_sync.sh` | 执行（本机跑） |
| 远程执行命令（密码兜底） | `scripts/sshrun.exp "<远程命令>"` | 执行（expect；密钥失效时自动兜底） |
| 投资知识库看板部署（rsync 推送） | `scripts/rsyncrun.exp` | 执行（排除 config.json/data/node_modules；部署后仍需手动重启） |

## Source hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式约定（默认 jianglb、MySQL 数据目录 /home/jianglb/mysql、vault 用 rsync） |
| 2 | 部署实测经验（2026-08-30：AppArmor/注释行 datadir/GitHub clone 失败） |
| 3 | 通用运维最佳实践（变更前备份、只读先于变更、凭据隔离） |

## 自检

- [ ] 连接是否用 jianglb 且无明文密码出现在命令/输出？
- [ ] 数据库操作是否区分 dev/生产库？生产库 DDL/DML 是否先经 fitness_dev 验证并说明影响？
- [ ] fitness 部署是否等用户明确说「部署」才执行（开发规范走 fitness-dev-workflow）？
- [ ] vault 同步是否在本机跑 scripts/vault_sync.sh（而非服务器 git clone）？
- [ ] 变更操作（重启/改配置/rsync --delete）前是否说明了影响？
- [ ] 数据库查询是否走隧道/本机 sudo mysql，端口未直连公网？
- [ ] 踩坑规则（GitHub clone 失败、AppArmor、bind-address）是否遵守？
