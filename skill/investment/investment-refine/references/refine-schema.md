# 提炼落库模板（POST /api/refine/record · schema）

> 由 investment-refine SKILL.md 第四步引用。**提炼完成后按本模板规定字段，`MCP 工具 `refine_record`（REST POST /api/refine/record 兼容，连接见 Ai/tools/investment-console-mcp/README.md）` 写入投资看板**，看板完整展示产物 + 决策链路。

---

## 一、落库对象结构（单次提炼 = 一条 record）

```json
{
  "id": "ref-xxx",
  "at": 1786809179530,
  "from": "工作区/原始资源/牛奶行业点评.md",
  "sourceType": "raw",
  "source": "[原文](https://xueqiu.com/.../XXXXXX)",
  "targets": [
    {
      "path": "我的/行业/牛奶行业.md",
      "type": "wiki",
      "layer": "other",
      "category": "industry",
      "tags": ["行业", "周期"],
      "basis": "原文「原奶价格已跌至 2018 年以来低位，去产能进入中后期…」",
      "why": "供需格局 + 周期位置 → 单列行业条目；作者未登记 → 其他层",
      "relation": "new"
    }
  ],
  "reason": "整体拆分决策说明",
  "steps": ["读取原文", "归属层判断", "创建条目", "更新博主档案", "校验"],
  "bloggerUpdated": false,
  "bloggerName": "",
  "verify": { "ok": true, "detail": "verify-format.py 0 问题" },
  "verificationHints": ["该判断可后续建分析档案做结果跟踪"]
}
```

---

## 二、字段规范（必须遵守）

| 字段 | 必填 | 类型 | 说明 |
|:---|:---|:---|:---|
| `from` | ✅ | string | 源材料相对路径（原始资源 或 粗制品） |
| `sourceType` | 建议 | string | `raw`=原始资源 / `coarse`=粗制品直提（帖子集 #29 / 直投 #30）；缺省按 from 含「粗制品」推断 |
| `source` | 建议 | string | 原文链接（markdown 格式 `[标题（博主 日期）](url)`） |
| `targets` | ✅ | array | **产物列表**，每项见下 |
| `reason` | 建议 | string | 整体拆分决策说明（为何拆成这些条目） |
| `steps` | 建议 | array | 提炼步骤时间轴（读取→分析→创建→档案→校验） |
| `bloggerUpdated` | 建议 | bool | 是否更新了博主档案（言论追踪） |
| `bloggerName` | 建议 | string | 涉及博主名 |
| `verify` | 建议 | object | 产出校验结果 `{ok, detail}`（verify-format.py） |
| `verificationHints` | 建议 | array | 可验证判断提示（建分析档案建议） |

### `targets[]` 每项

| 字段 | 必填 | 说明 |
|:---|:---|:---|
| `path` | ✅ | 产物相对路径 |
| `type` | ✅ | 英文码：`wiki`=框架条目 / `blogger`=博主画像言论追踪 / `macro`=宏观 |
| `layer` | 建议 | **英文码**（见下方字典表）：`my`/`blogger`/`other`/`macro`/`workspace` |
| `category` | 建议 | **英文码**（见下方字典表）：`analysis_framework`/`trading_system`/`investment_mentality`/`investment_insight`/`stock`/`industry`/`macro` |
| `tags` | 建议 | 标签（来自标签体系，一级前缀） |
| `basis` | ✅ | **依据**：原文支撑该条目的关键句引用——回答"从哪句话提炼的" |
| `thinking` | ✅ | **思考链路 v2**（2026-08-31）：自由长度对象数组 `[{kind,text,quote?,alt?}]`，按真实推理过程记录（观察/疑问/假设/查证/对比/权衡/排除/决策/结论…）；`quote`=触发该步的原文引用、`alt`=备选方案/否决理由；三个决策点（归属层/拆分/关系）必含。**禁止固定 5 步模板套话**（旧格式字符串数组仍兼容展示） |
| `why` | ✅ | **决策**：拆分/归类/标签判断（结论摘要）——回答"为什么提炼成这个" |
| `relation` | 建议 | **英文码**：`new`/`append`/`complement`/`conflict_check`/`other`——判断范围按分层检索链（同作者同类分类 → 全库关键词兜底 → 新建，关键词取产物名拆分+原文实体+标签 3-5 词，检索文件名/标题/标签；见 SKILL.md 第一步第 3 步；与 C7 联动） |

---

## 二B、字典码对照表（避坑 · 2026-08-31 实测）

**`layer`/`category`/`relation`/`type`/`sourceType` 必须传数据库字典英文码，传中文会落库失败（外键约束报错）**。全量对照（源：远端 MySQL `investment_kb` 的 `dict` 单表，`type` 列区分字典域；2026-08-31 schema 整合后由多张 dict_* 合并为单表）：

| 字段 | 字典表 | 合法码（码 → 中文含义） |
|:---|:---|:---|
| `layer` | dict(type=layer) | `my`=我的 / `blogger`=博主 / `other`=其他 / `macro`=宏观 / `workspace`=工作区 / `attachment`=附件 |
| `category` | dict(type=category) | `analysis_framework`=分析框架 / `trading_system`=交易体系 / `investment_mentality`=投资心态 / `investment_insight`=投资心得 / `stock`=个股 / `industry`=行业 / `macro`=宏观 |
| `relation` | dict(type=target_relation) | `new`=新建 / `append`=追加 / `complement`=互补 / `conflict_check`=矛盾预检 / `other`=其他 |
| `type` | dict(type=target_type) | `wiki`=框架条目 / `blogger`=博主画像 / `macro`=宏观条目 |
| `sourceType` | dict(type=source_type) | `raw`=原始资源 / `coarse`=粗制品 |
| 审查 `checks[].status` | dict(type=check_status) | `pass`=通过 / `warn`=警告 / `fail`=失败（`ok`=旧数据遗留，新写入不用；**无 `info`**） |

> **避坑**：落库报 `foreign key constraint fails ... dict_*` 时，用 `SHOW CREATE TABLE {refine_targets|review_checks}` + 对应字典表核对码值，不要猜中文。博主画像目标 `category` 可省略（列可空）。

---

## 三、`type` 取值与看板展示

| type | 含义 | 看板展示 |
|:---|:---|:---|
| `wiki` | 框架条目 | 分类色块 + 归属层徽章 + 产物决策卡 |
| `blogger` | 博主画像言论追踪 | **粉色「言论追踪」标记** |
| `macro` | 宏观 | 琥珀色「宏观」标记 |

`sourceType=coarse` 时看板显示「粗制品直提」徽章；`verify.ok` 显示「校验通过」；`bloggerUpdated` 显示「言论追踪」。

---

## 四、决策一致性（质量保障）

- `basis`（依据原文句）必须**真实来自原文**，禁止事后编撰
- `why`（决策）必须来自第一步分析的真实判断：归属层铁律（博主控制台登记）、标签体系、同作者一致性预检
- `relation`（关系）与审查 C7 关联备注提案、C3 矛盾预检联动——提炼时标注的互补/矛盾，审查时据此核对
- 落库失败（看板未启动等）不阻断提炼主流程，但汇报中必须提示「看板数据未写入，需补录」

---

## 五、旧数据兼容

- 旧格式 `to[]`（字符串数组）→ 服务端自动归一化为 `targets[]`（type 按路径推断：`博主/`→blogger、`宏观/`→macro、其余→wiki；layer/category 从路径提取）
- 看板读取兼容 `r.to` / `r.targets` 两种结构
