# 审查落库模板（data/review.json · schema）

> 由 investment-review SKILL.md 的 Output Format 引用。**2026-08-16 起审查不再产出 md 报告文件**，改为直落库：审查完成后按本模板规定的结构化字段，`MCP 工具 `review_record`（REST POST /api/review/record 兼容，连接见 Ai/tools/investment-console-mcp/README.md）` 写入投资看板本地数据 `data/review.json`（看板唯一数据源）。
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
    { "item": "wikilink_issues", "result": "13", "compare": "8/9 为 0（新增）", "status": "fail" },
    { "item": "no_fm", "result": "0", "compare": "—", "status": "pass" }
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
    { "num": "1", "text": "裁决 9 处框架内部矛盾", "status": "待用户裁决" }
  ],
  "summary": "总结与建议全文（含强项、建议动作说明）"
}
```

---

## 二、字段规范（必须遵守）

| 字段 | 必填 | 类型 | 说明 |
|:---|:---|:---|:---|
| `date` | 必填 | string | 审查日期 `YYYY-MM-DD`；**幂等覆盖**——同日期重复审查覆盖旧记录 |
| `title` | 必填 | string | 报告标题 `审查报告 {YYYY-MM-DD}` |
| `meta` | 建议 | object | 审查范围/扫描文件数/工具/对比基线/原则（key-value） |
| `method` | 建议 | string | 审查方法简述 |
| `mainProblems` | 建议 | string | 总体结论（结构强项 + 主要问题） |
| `checks` | 必填 | array | **脚本指标检查项**（vault_review.py 输出表逐行）：每项 `{item, result, compare, status}` |
| `groups` | 必填 | array | **通用审查分组**：结构问题 S 小节 + 内容审查 C 小节 + **未来任意新审查项**。每项 `{title, severity, tag, headers, rows, text}` |
| `recycle` | 建议 | object | 待回收处置：`{done, cooling, doneHist, rows[]}`（rows = 条目/标记日期/冷静天数/处置/理由） |
| `actions` | 建议 | array | 建议动作表：`{num, text, status}` |
| `summary` | 建议 | string | 总结与建议 |

---

## 三、`status` / `severity` 取值规范

| 值 | 含义 | 看板徽章 |
|:---|:---|:---|
| `pass` | 合规（result 存纯数值如 `0`，勿带徽章） | PASS 绿 |
| `warn` | 注意（需关注，可修复） | WARN 黄 |
| `fail` | 严重（必须处理，可 AI 修复） | FAIL 红 |
| ~~`info`~~ | **非法**：dict_check_status 无此码，落库会外键报错 | — |

`groups[].severity` 独立于 `checks[].status`：分组级别用 `fail/warn/info`（从分组标题/严重度推断）；**检查项级别只能传 `pass/warn/fail`**（字典 dict_check_status 合法码，2026-08-31 实测；`ok` 为旧数据遗留、新写入不用）。落库报外键错误时按 refine-schema.md 二B 字典表核对码值。

---

## 四、落库调用规范

1. **端点**：`MCP 工具 `review_record`（REST POST /api/review/record 兼容，连接见 Ai/tools/investment-console-mcp/README.md）`，`Content-Type: application/json`
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

## 六、`groups[].tag` 分区硬约束（2026-09-07 实测补录）

看板前端按 `tag` 把分组拆成「结构问题 / 内容审查」两个大区：`isStructG = g.tag === 'S' || 标题含「结构」`——**精确匹配单字母 `S`**。

- **结构类分组**（归类错误 / 段落缺失 / 脚注格式 / 空链接行 / 重复标题等）→ `tag: "S"`（子维度编号如 S2/S6 只写进 `title`，如 `归类错误（S2）`）
- **内容类分组**（C3 一致性 / C4 知行合一 / C6 经验验证 / C7 关联 / C8 复核等）→ `tag: "C"`
- ⚠️ **禁止**在 `tag` 落 `"S2"`/`"C6"` 等带编号的值——看板 `isStructG` 只认 `tag === 'S'`，落 `"S2"` 会被 `!isStructG` 误分进「内容审查」区（结构问题混入内容区，2026-09-07 落库实测踩坑，已修正后重落）
- 分组 `title` 内可保留子编号便于人读，但**分区判定只看 tag**，两处互不替代

> 连带约束：`rows` 用对象数组时，需显式 `状态` 列（`pass/fail/warn`）才会渲染徽章；C7 关系列固定最右（看板 `isC7` 检测到「关系」+「说明」列自动把关系列移到最右，`headers` 顺序建议直接按 `条目/关联目标/说明/关系` 排好）。

---

## 七、修复记录（仍为 md 执行日志）

**修复动作不落库**：用户授权修复后仍写 `修复记录-{YYYY-MM-DD}.md`（执行日志，vault `工作区/审查报告/` 目录），记录修复动作与结果。对应审查通过 `date` 关联（不再有审查报告 md 可 wikilink，改用「对应审查：2026-08-14」文字引用）。
