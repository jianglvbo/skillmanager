# 投资看板（investment-console）联动指南

> 本文件描述流水线（提炼/审查/粗制品）与投资看板的数据契约与渲染约定。看板完整交接文档在用户桌面 `投资知识库看板交接文档.md`（含架构/API/踩坑/设计铁律全量），本文件只保留**执行流水线时必须知道**的部分。

## 1. 看板是什么

纯前端 + 零依赖 Node 轻服务（`~/WorkBuddy/2026-08-09-16-58-44/investment-console/`，端口 8698，launchd 托管 com.investment-console）。内容在 vault（Markdown），结构在 `data/*.json`。**看板不产生知识，只呈现流水线结果。**

## 2. 数据契约（流水线写入）

| 写入方 | 端点 | 数据 | 看板呈现 |
|:---|:---|:---|:---|
| investment-refine 第四步 | `POST /api/refine/record` | targets[]（含 thinking 5 步/basis/why/relation） | 提炼时间轴 + 决策链路图 |
| investment-review 第四步 | `POST /api/review/record` | 结构化审查（checks/groups/recycle） | 审查模块（2026-08-16 起不再产出 md 审查报告） |
| 粗制品评分/加工 | `POST /api/coarse/score` `/process` | 调本地 dsh | 粗制品模块 |

失败处理：API 失败（看板未启动）不阻断主流程，汇报提示「看板数据未写入」。

## 3. refine/record 请求体（决策链路图数据源）

```json
{
  "from": "工作区/原始资源/<源文件>.md",
  "sourceType": "raw",            // raw / coarse（帖子集#29、直投#30）
  "source": "[原文](url)",
  "targets": [{
    "path": "博主/雪月霜/分析框架/xxx.md",
    "type": "wiki",               // wiki / blogger（言论追踪）/ macro
    "layer": "博主",              // 归属层判断（我的/博主/其他/宏观）
    "category": "分析框架",
    "tags": ["分析框架/估值"],     // 挂一级前缀，禁裸标签
    "basis": "原文「关键句」",      // 依据（必填，从原文哪句提炼）
    "thinking": [                 // 标准 5 步：识别/价值/归类/关系/生成
      "识别：…", "价值：…", "归类：…", "关系：…", "生成：…"
    ],
    "why": "决策一句话",
    "relation": "新建/追加/互补/矛盾预检"
  }],
  "reason": "整体拆分决策说明",
  "steps": ["读取原文", "归属层判断", "创建条目", "更新博主档案", "校验"],
  "bloggerUpdated": true,
  "bloggerName": "雪月霜",
  "verify": { "ok": true, "detail": "verify-format.py 0 问题" },
  "verificationHints": []
}
```

- 一对多：一篇拆多条，targets 全写，每条必填 basis + thinking + why
- thinking 每步来自第一步分析的真实判断（归属层铁律/标签体系/模板选择/同作者预检），**禁止事后编撰**
- 涉及已登记博主：targets 同时含 `type:"blogger"` 画像条目 + `bloggerUpdated:true`
- 旧数据 `to[]` 字符串数组自动兼容归一化

## 4. 决策链路图 10 节点规范（2026-08-17 用户拍板）

```
源(起止符圆角) → 识别(处理矩形·公共节点) → ◆归属层判断◆(菱形)
→ 拆分决策(处理矩形) → 分叉 3 列，每列: 价值→归类→◆关系判断◆(菱形)→生成→产物卡(圆角卡片+点击跳转)
→ 汇合 → 校验(终止符)
```

- **判断只留给有真实分叉数据的节点**（归属层、关系）；价值/拆分/校验是说明或收尾，画菱形会引入死分支
- **关系判断职责边界（保持现状）**：提炼时关系判断 = 生成决策（新建/追加/互补 + 写前矛盾预警）→ thinking[3]；审查 C3/C7 = 写后质检。分工「写对 vs 查对」，不重复
- **分叉口对齐**：水平分叉线两端对齐上游节点左右下角，引导线从节点底边中点出、长度 ≥20px；三列中心嵌套在上游节点宽度范围内

## 5. 产物展示约定（2026-08-17 最新）

- **单产物**：`源 ⟶ 产物` 链
- **多产物**：`源 ⟶` 后产物徽章**横向并联**（flex gap 分隔、产物间无箭头、自动换行）——体现「一个源分出多个并列产物」；**不用 SVG 分叉图**（用户试用后否决，改回纯 CSS 并联）
- 产物徽章 title = 完整路径；blogger 类型粉色标记

## 6. 前端实现要点（改渲染必读）

- 决策链路图：`buildFlowMermaid(r)` 生成 mermaid flowchart TD，mermaid **v10.9.1 本地 vendor**（web/vendor/mermaid.min.js，不归 git），`curve:'stepAfter'`（正交折线）、dagre 布局（去 ELK）、nodeSpacing 48 / rankSpacing 45
- 5 类 classDef 动态读 CSS 变量：proc(accent)/dec(warn)/rel(accent-2)/product(accent 粗边 2.5px)/ver(good)
- 产物卡 3 行：文件名 / `[类型]分类·层` / 依据摘要；`g.product` 绑 click → `openInObsidian(path)`（外部事件委托，绕 mermaid click 单引号坑）
- 交互：全屏覆盖层 + 滚动条定位（inner = max(svgW*scale, 视口)+2×150px 留白）、中心锚点缩放（按钮 ±5%、Ctrl+滚轮 ±2%）、初始 100%、上一篇/下一篇导航

## 7. 设计铁律（改任何前端必须遵守）

- 持续动画默认禁止；backdrop-filter 仅浮层（≤10，当前 5）；无粒子/Canvas 背景动画；无 setInterval UI 轮询
- **监听器模块级单例**：持久元素重渲染时重复绑定的监听器必须只绑一次（0.11.1 教训：scroll 监听器累积泄漏 → 越用越卡）
- 自检：backdrop-filter ≤10、持续动画 0、定时器 0
- 教训：粒子 + blur(80px) + 82 个 backdrop-filter → Renderer CPU 107%（v0.8-v0.9.5 五轮清干净）

## 8. 其他

- 主题：10 主题 × 深浅 2 模式，CSS 变量实现；决策链路图颜色 getComputedStyle 动态读 + hex 校验兜底
- 看板数据在 `data/`，**别手动改 JSON**，一律走 API（否则操作日志/索引不同步）
- 验证：playwright + 系统 Chrome（`executable_path` 指定）；`node --check web/app.js`；jsdom 只能看逻辑不能信布局
