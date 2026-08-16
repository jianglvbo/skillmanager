# 审查落库模板（data/review.json · schema）

> 由 investment-review SKILL.md 的 Output Format 引用。**2026-08-16 起审查不再产出 md 报告文件**，改为直落库：审查完成后按本模板规定的结构化字段，`POST http://127.0.0.1:8698/api/review/record` 写入投资看板本地数据 `data/review.json`（看板唯一数据源）。
> 历史 md 报告（2026-08-09/14）不迁移、不回退依赖；看板仅在无落库记录时回退解析旧 md 兼容展示。

---

## 一、落库对象结构（单次审查 = 一条 record）

```json
{
  "date": "YYYY-MM-DD",
  "title": "审查报告 YYYY-MM-DD",
  "meta": {
    "审查范围": "博主/、其他/、宏观/（「我的」层按规则 #15 不审查不触碰）",
    "扫描文件数": "386 个（全库）",
    "工具": "vault_review.py 六维自动预扫 + verify-format.py 段落布局预扫 + 子代理深度内容审查",
    "对比基线": "2026-08-09",
    "原则": "只报告不修改（除 #26 授权的回收执行）"
  },
  "method": "审查方法简述（结构 S1-S8 + 内容 C3-C8 判定口径）",
  "mainProblems": "总体结论：结构强项 + 主要问题清单",
  "checks": [
    { "item": "wikilink_issues", "result": "🔴 13", "compare": "8/9 为 0（新增）", "status": "fail" },
    { "item": "no_fm", "result": "✅ 0", "compare": "—", "status": "pass" }
  ],
  "groups": [
    {
      "title": "归类错误（S2）",
      "severity": "fail",
      "tag": "S2",
      "headers": ["文件", "建议"],
      "rows": [["博主/景风长赢/景风长赢.md", "迁 `其他/` 层"]],
      "text": "叙述性补充（核心问题说明、决策依据），无表格时的兜底"
    }
  ],
  "recycle": {
    "done": "0", "cooling": "5", "doneHist": "1",
    "rows": [["其他/交易体系/马丁与反马丁策略", "2026-08-09", "5", "待回收（剩 2 天）", "冷静期内保留；1 处入链"]]
  },
  "actions": [
    { "num": "1", "text": "裁决 9 处框架内部矛盾", "status": "🔴 待用户裁决" }
  ],
  "summary": "总结与建议全文（含强项、建议动作说明）"
}
```

---

## 二、字段规范（必须遵守）

| 字段 | 必填 | 类型 | 说明 |
|:---|:---|:---|:---|
| `date` | ✅ | string | 审查日期 `YYYY-MM-DD`；**幂等覆盖**——同日期重复审查覆盖旧记录 |
| `title` | ✅ | string | 报告标题 `审查报告 {YYYY-MM-DD}` |
| `meta` | 建议 | object | 审查范围/扫描文件数/工具/对比基线/原则（key-value） |
| `method` | 建议 | string | 审查方法简述 |
| `mainProblems` | 建议 | string | 总体结论（结构强项 + 主要问题） |
| `checks` | ✅ | array | **脚本指标检查项**（vault_review.py 输出表逐行）：每项 `{item, result, compare, status}` |
| `groups` | ✅ | array | **通用审查分组**：结构问题 S 小节 + 内容审查 C 小节 + **未来任意新审查项**。每项 `{title, severity, tag, headers, rows, text}` |
| `recycle` | 建议 | object | 待回收处置：`{done, cooling, doneHist, rows[]}`（rows = 条目/标记日期/冷静天数/处置/理由） |
| `actions` | 建议 | array | 建议动作表：`{num, text, status}` |
| `summary` | 建议 | string | 总结与建议 |

---

## 三、`status` / `severity` 取值规范

| 值 | 含义 | 看板徽章 |
|:---|:---|:---|
| `pass` / `✅ 0` | 合规 | PASS 绿 |
| `warn` / `⚠️ n` | 注意（需关注，可修复） | WARN 黄 |
| `fail` / `🔴 n` / `❌` | 严重（必须处理，可 AI 修复） | FAIL 红 |
| `info` / 其他 | 信息 | 中性 |

`groups[].severity` 独立于 `checks[].status`：分组级别用 `fail/warn/info`（从标题 🔴/⚠️ 推断）；检查项级别用 `pass/warn/fail/info`。

---

## 四、落库调用规范

1. **端点**：`POST http://127.0.0.1:8698/api/review/record`，`Content-Type: application/json`
2. **请求体**：上述完整 record 对象
3. **校验**：服务端校验 `date/title/checks/groups` 必填；失败返回 `{ok:false, error}`，**必须补全后重试**，禁止跳过落库
4. **幂等**：同 `date` 覆盖写入（自动处理）
5. **失败处理**：看板未启动/网络异常 → 落库失败不阻断审查主流程，但汇报中明确提示「审查数据未落入看板，需补录」
6. **写入时机**：审查全部完成（含回收处置计算）后一次性提交，不中途分批

---

## 五、审查项扩展机制（未来新审查项）

- **任何新的审查维度** = `groups` 数组新增一条：`{title, severity, tag, headers, rows, text}`
- **看板零代码适配**：前端按 `groups` 通用渲染（有 `headers+rows` 出表格、有 `text` 出文本卡），新增分组自动展示
- **检查项新增** = `checks` 数组新增一行（vault_review.py 新指标自动纳入）
- 禁止：修改 schema 结构（新增字段需与看板协商）、跳过落库、用 md 替代

---

## 六、修复记录（仍为 md 执行日志）

**修复动作不落库**：用户授权修复后仍写 `修复记录-{YYYY-MM-DD}.md`（执行日志，vault `工作区/审查报告/` 目录），记录修复动作与结果。对应审查通过 `date` 关联（不再有审查报告 md 可 wikilink，改用「对应审查：2026-08-14」文字引用）。
