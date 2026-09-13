---
name: tradingagents-deploy
description: 国内环境部署与运行 TradingAgents 多智能体投研框架。覆盖 colima+Docker 安装踩坑（代理/DNS/镜像加速）、原版 pip 安装、yfinance Yahoo 限流 curl_cffi 修复、CN 版 Docker compose 部署（清华 apt 源+GitHub 下载重试+build-arg 代理）、DeepSeek/Tushare 配置、一键分析脚本。触发词：「跑 tradingagents」「TradingAgents 分析」「多智能体分析 XX」「ta 分析」「tradingagents 部署」「CN 版」「TradingAgents-CN」。排除：仅问框架原理不落地时不触发。
---

# TradingAgents 国内部署与运行

## 0. 双版本选型（2026-08-09 状态：CN 版为主，原版已删）

| 版本 | 形态 | 数据源 | 现状 |
|:---|:---|:---|:---|
| CN 版（主推） | Docker compose 全家桶 | Tushare/AKShare/BaoStock（A股专业） | ✅ 在用，Web UI http://localhost:3000 |
| 原版 | 纯 Python CLI | yfinance | ❌ 已删（用户决定不需要，Yahoo 限流是硬伤） |

- **默认走 CN 版**（第 6 节）
- 原版部署方法保留在第 3-5 节供参考（若未来需要轻量 CLI 可复用）

## 1. 什么时候用我？

- 用户要跑 TradingAgents 分析股票（A股/美股/港股，如「分析茅台」「ta 跑一下 600519」）
- 需要在国内网络环境部署/修复 TradingAgents（代理、Docker、Yahoo 限流）
- 用户机器上 TradingAgents 环境损坏需要重装/修复

## 2. 核心结论（先读）

- **用原版** `TauricResearch/TradingAgents`（pip 装，2 分钟），**不用 CN 版**（backend Docker 构建太重 + 核心闭源）
- 运行需同时设两个环境变量：`HTTPS_PROXY=http://127.0.0.1:7890`（Yahoo 数据源）+ `DEEPSEEK_API_KEY=...`（LLM）
- Yahoo 429 限流是 IP 级封禁，**curl_cffi 浏览器指纹可绕过**（已修复进数据层，见第 4 步）

## 3. 部署路径

**前提**：Python ≥3.10、git、Clash 代理 7890（国内必需，GitHub/Yahoo 直连均超时）

### 第一步：clone 原版（必须走代理）

```bash
git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 clone --depth 1 https://github.com/TauricResearch/TradingAgents.git
```

### 第二步：venv + 清华镜像安装

```bash
cd TradingAgents
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
.venv/bin/pip install --prefer-binary . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 第三步：配置 DeepSeek

```bash
cp .env.example .env
# 编辑 .env 填 DEEPSEEK_API_KEY
# 验证: curl -s https://api.deepseek.com/models -H "Authorization: Bearer <key>" 应返回 200
```

### 第四步：修复 Yahoo 限流（关键）

修改 `tradingagents/dataflows/y_finance.py`：
1. 顶部加 `import os`
2. `ticker = yf.Ticker(canonical)` → `ticker = _make_yfinance_ticker(canonical)`
3. 新增函数 `_make_yfinance_ticker()`：用 curl_cffi `Session(impersonate="chrome")` 伪装浏览器指纹，读 `HTTPS_PROXY` 环境变量走代理，异常时回退默认 session

要点：Yahoo 对 yfinance 默认 requests 客户端做 TLS 指纹封禁（429），**换代理 IP 无效、加浏览器头无效**，只有 curl_cffi impersonate 有效。环境变量 `TRADINGAGENTS_YFINANCE_CURL_CFFI=0` 可关闭。

### 第五步：一键分析脚本

在项目根目录建 `run_analysis.py`（复制自仓库内同名脚本，参数为 ticker + 日期）：

```bash
HTTPS_PROXY=http://127.0.0.1:7890 DEEPSEEK_API_KEY=... .venv/bin/python run_analysis.py 600519.SS 2026-08-07
# 输出: reports/<ticker>_<date>.md（完整中文报告，含 分析师→多空辩论→交易员→风控→组合管理）
```

- 脚本要点：`config["llm_provider"]="deepseek"`、`deep_think_llm/quick_think_llm="deepseek-v4-flash"`、`output_language="Chinese"`；报告从 state 的 `market_report/fundamentals_report/investment_plan/final_trade_decision` 等字段拼装（**不是** `state["final_report"]`，该字段不存在）
- 耗时：7-10 分钟（DeepSeek 多轮调用）

## 6. CN 版部署（TradingAgents-CN Web 平台）

### 前置：Docker 环境（colima）就绪
- colima 代理配置用 `host.lima.internal:7890`（VM 内访问宿主），**不要用 127.0.0.1**（VM 内指向自身）
- VM 内 `/etc/resolv.conf` 需静态 DNS（114.114.114.114），否则 buildkit DNS 失败
- docker daemon.json 配置 registry-mirrors（docker.m.daocloud.io 等），否则拉基础镜像卡死

### 第一步：clone + 配置 .env
```bash
git -c http.proxy=http://127.0.0.1:7890 clone --depth 1 https://github.com/hsliuping/TradingAgents-CN.git
cd TradingAgents-CN && cp .env.example .env
# 填: DEEPSEEK_API_KEY, TUSHARE_TOKEN, DEEPSEEK_ENABLED=true, TUSHARE_ENABLED=true
```

### 第二步：改 Dockerfile.backend（国内网络必须）
1. apt 源切清华镜像：`sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g'`（deb.debian.org 国内慢）
2. pandoc/wkhtmltopdf 的 GitHub 下载加 `--tries=5 --timeout=30` 重试
3. （可选）更稳的方案：构建时注入 VM 内可达代理

### 第三步：构建（关键命令）
```bash
docker compose build --build-arg http_proxy=http://192.168.5.2:7890 --build-arg https_proxy=http://192.168.5.2:7890 backend
```
- **192.168.5.2 是 colima VM 内可达宿主 Clash 的网关 IP**（`host.lima.internal` 在 buildkit 会话解析失败，必须用 IP）
- 不用 build-arg 时，Dockerfile 内 wget GitHub 会因直连 CDN 不稳而挂死
- 构建耗时约 15 分钟（apt + pandoc + pip 全家桶）

### 第四步：启动 + 修复数据库连接
```bash
docker compose up -d
# ⚠️ 必改：.env 中 MONGODB_HOST=localhost / REDIS_HOST=localhost
#    → 改为 mongodb / redis（容器名），否则 backend 连不上库反复重启
# ⚠️ 必改：.env 中 MONGODB_CONNECTION_STRING 独立变量也要指向 mongodb:27017
```

### 第五步：创建默认账号（启动逻辑不会自动建！）
```bash
docker exec tradingagents-backend python -c "import asyncio; from app.services.user_service import user_service; asyncio.run(user_service.create_admin_user())"
# 默认账号: admin / admin123
```

### 第六步：修复前端 nginx /api 代理（登录 405 的根因！）
浏览器请求 `http://localhost:3000/api/...` 走前端 nginx，但默认 nginx **没有 /api 代理**，POST 返回 405。在 frontend 容器 `default.conf` 的 `location /` 前插入：
```nginx
location /api/ {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 300s;
    client_max_body_size 100m;
}
```
然后 `nginx -s reload`。⚠️ 容器内无 python3 用 sed 插入；⚠️ 该修改在容器重建后丢失，需改 Dockerfile.frontend 持久化。

验证：`curl -X POST http://localhost:3000/api/auth/login -d '{"username":"admin","password":"admin123"}'` 应返回 200

### CN 版日常使用
- 前端：http://localhost:3000（账号 admin/admin123）
- 重启：`cd TradingAgents-CN && docker compose up -d`（重启后需重做第六步 nginx 配置，除非已持久化）
- 停止：`docker compose down`

## 4. 常见问题

| 症状 | 根因 | 解法 |
|:---|:---|:---|
| GitHub clone 卡死 | 直连超时 | 必须走 7890 代理 |
| Yahoo 429（所有标的） | TLS 指纹封禁 | curl_cffi impersonate（第 4 步） |
| Yahoo 429（仅某 IP） | IP 级封禁 | 换 Clash 节点重试 |
| 分析报 FRED_API_KEY 缺失 | 宏观数据可选 | 忽略，不影响主流程 |
| CN 版 backend 构建卡 apt | deb.debian.org 慢 | 换清华源（第 6 节第二步） |
| CN 版 backend 反复重启 | MONGODB_HOST 指向 localhost | 改为 mongodb 容器名（第 6 节第四步） |

## 5. 我的边界

- CN 版核心代码闭源 + 商业使用需授权（个人研究可用）
- 不提供实盘交易建议，分析结果仅研究参考
- 不修改 tradingagents 核心逻辑（只加数据层兼容函数）

---

# 自检

- [ ] clone/安装是否走清华镜像+代理？
- [ ] DeepSeek key 是否验证连通（HTTP 200）？
- [ ] y_finance.py 是否已加 curl_cffi 修复（不修必 429）？
- [ ] 运行命令是否同时带 HTTPS_PROXY + DEEPSEEK_API_KEY？
- [ ] 报告是否从 section 字段拼装（非 final_report）？
