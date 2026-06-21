# link-analysis

### 链接分析工作流

收集用户发送的链接（雪球、公众号、抖音等），存入每日收集队列（~/.qoderworkcn/daily-links/），18:00 定时任务统一抓取内容、生成分析文档存入熊掌记，并通过飞书发送浓缩摘要。

## 它能做什么

- **链接收集**：接收用户发送的各平台链接，按日汇总到 JSON 队列
- **内容抓取**：自动抓取链接正文（支持多层降级策略）
- **文档生成**：将当日所有链接整合为结构化分析文档
- **多端分发**：文档存入熊掌记，浓缩版通过飞书发送

## 安装

```bash
# 符号链接安装到 QoderWork CN skills 目录
ln -s ~/Ai/skill/link-analysis ~/.qoderworkcn/skills/link-analysis
```

## 依赖

- **xiongzhangji**：熊掌记笔记创建
- **飞书**：消息发送（需飞书连接器）
- **autocli**：部分网站内容抓取（可选）

## 目录结构

```text
link-analysis/
├── SKILL.md          ← Agent 加载入口
├── README.md         ← 本文件
├── CHANGELOG.md      ← 版本记录
└── scripts/
    └── add_link.py   ← 链接收集工具
```

## 使用

### 手动收集链接

```bash
python3 ~/Ai/skill/link-analysis/scripts/add_link.py "https://xueqiu.com/..." "雪球" "备注"
```

### 定时执行分析

由 QoderWork CN 的定时任务（每日 18:00）触发，完整执行协议见 `~/.qoderworkcn/daily-links/protocol.md`。

## License

MIT
