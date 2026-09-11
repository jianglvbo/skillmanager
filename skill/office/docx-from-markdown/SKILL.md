---
name: docx-from-markdown
description: 从 Markdown 生成规范排版的本地 Word（.docx）文档：新建空白文档 → 一次插入 Markdown → 统一表头样式 → 另存到指定路径，全流程走本地 editor_sdk 通道，并回读校验结构。触发词：「生成Word」「生成docx」「markdown转Word」「批量生成文档」「写一份方案/开题报告并导出Word」。排除条件：需要封面与深度版式设计的单篇专业文档走 tencent-docx；仅读取或编辑已有 docx 内容走 tencent-local-office-edit。
agent_created: true
---

# docx-from-markdown

## Default stance

核心原则：

1. **结构保真优先于版式美化** —— Markdown 的标题层级（`#` / `##` / `###`）与表格必须原样落到 docx 的 Heading 与 Table 结构，不得退化为纯文本段落
2. **一次插入整篇** —— 用 `doc_insert_markdown` 传 `file://<绝对路径>`，不要把长正文塞进调用字符串、更不要逐段 `doc_insert_text`
3. **表头样式是硬门禁** —— 每张表都必须执行表头着色（底色 + 居中），未着色视为任务未完成，不靠事后检查弥补
4. **落盘后必须回读校验** —— 以落盘文件的 `total_headings` / `total_tables` 与草稿比对，不接受「插入成功」回包作为完成依据

禁止行为：

1. **禁止对同一 `file_id` 重复执行 `doc_insert_markdown`** —— 会整篇重复插入（标题数、表格数直接翻倍）
2. **禁止把 `create_doc` 的文本回包直接当 `file_id`** —— 回包是自然语言文本而非 JSON，必须正则提取 `file_id=`
3. **禁止复用旧 `file_id` 重建文档** —— 需要重生成时一律新建，不复用可能已含内容的实例
4. **禁止省略实例清理** —— 校验用的后台实例需 `close_file`，否则同路径残留孤儿实例，用户后续看不到实时改动

## Workflow

第一步：判定输出格式 —— 结构化文本类需求（方案、报告、总结、纪要）一律输出 `.docx`，不默认交付 Markdown

第二步：写 Markdown 草稿到工作目录（临时草稿放工作区，不进 skill 仓库）

第三步：新建空白文档 —— `create_doc`，从文本回包正则提取 `file_id`

第四步：一次插入全文 —— `doc_insert_markdown file_id=<id> idx=0 markdown=file://<草稿绝对路径>`

第五步：统一表头样式 —— `doc_list_tables` 取全部 `table_id` → 逐表 `doc_set_table_cells`，`cells` 覆盖第 1 行全部列，`common_cell_properties` 设底色与居中

第六步：另存目标路径 —— `save_file file_id=<id> file_path=<目标绝对路径>`

第七步：回读校验 —— `open_file` 目标路径，等待流式打开完成后 `doc_resolve_document_structure mode=outline link=0`，比对结构与草稿

第八步：清理实例 —— `close_file` 后台校验实例，保留用户正在查看的实例

### 决策点

- **表格数/标题数与草稿不一致** → 判为重复插入或漏插，回到第三步用全新 `file_id` 重跑，不要在旧实例上补救
- **需要封面、目录、页眉页脚等深度版式** → 改走 `tencent-docx`，本 skill 只做结构保真的结构化文档
- **目标文件已存在** → 直接覆盖写（`save_file` 指定路径即为覆盖），无需先删除

## Output format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| 输出路径 | string | 落盘绝对路径，必须位于用户指定目录 |
| 标题数 | int | `total_headings`，含 H1/H2/H3，应与草稿一致 |
| 表格数 | int | `total_tables`，应与草稿一致 |
| 校验结论 | string | `通过` 或具体不一致原因 |

## Relative files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| 需要批量生成多份文档 | `scripts/build_docx.py` | 按 JSON 作业清单批量建文档、着色、另存 | **执行**（不读代码，看输出） |
| 需要单个 `doc_*` 工具的参数定义 | 由 `tencent-local-office-edit` skill 提供 | `python3 edsdk.py schema <工具名>` | 读取 |

## Source hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式约定（目标目录、文件命名、必须回读校验） |
| 2 | `tencent-local-office-edit` skill 的工具契约（schema 必填项与坐标约定） |
| 3 | Markdown → docx 的结构保真原则 |

## 自检

- [ ] 草稿标题层级与目标结构一致（1 个 H1 + 各章 H2 + 小节 H3）？
- [ ] 每张表都完成表头着色（着色调用数 = 表格数）？
- [ ] 落盘文件的 `total_headings` / `total_tables` 与草稿一致？
- [ ] 全程未对同一 `file_id` 重复插入？
- [ ] 后台实例已清理，无孤儿实例残留？
