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
5. **读参考件走提取脚本** —— editor_sdk 的查询接口只回文本预览（归一化空白并截断），要「照着某份 docx 复刻结构」必须用 `scripts/extract_docx_text.py` 取全文

禁止行为：

1. **禁止对同一 `file_id` 重复执行 `doc_insert_markdown`** —— 会整篇重复插入（标题数、表格数直接翻倍）
2. **禁止想当然解析 `create_doc` 回包** —— 回包形态不稳定：有时是自然语言文本（需正则取 `file_id=`），有时只回一个裸 id。两种都要认，不能只按一种写死
3. **禁止复用旧 `file_id` 重建文档** —— 需要重生成时一律新建，不复用可能已含内容的实例
4. **禁止省略实例清理** —— 校验用的后台实例需 `close_file`，否则同路径残留孤儿实例，用户后续看不到实时改动
5. **禁止用 `k=v` 传布尔/空值参数** —— `True` 不是合法 JSON，会被当字符串触发 `type must be boolean`，布尔与 `None` 必须走 `--json`
6. **禁止用长字符串匹配要改格式的段落** —— 预览截断到约 4 字，匹配串须是短短语，并以「首个非空文本节点」兜底
7. **禁止把 `document is not open` 当致命错误直接放弃** —— 服务空闲后首次插入偶发此错，需重开并重试（脚本已内置 3 次重试）

## Workflow

第一步：判定输出格式 —— 结构化文本类需求（方案、报告、总结、纪要）一律输出 `.docx`，不默认交付 Markdown

第一步补：若有参考件（「参考这份再写几个」）—— 先用 `scripts/extract_docx_text.py` 取参考件全文，提取其章节骨架、表格维度与样式（表头底色、标签表整表着色、页面设置、封面标题字体字号），作为新文档的复刻基准

第二步：写 Markdown 草稿到工作目录（临时草稿放工作区，不进 skill 仓库）

第三步：新建空白文档 —— `create_doc`，按上式两种回包形态取 `file_id`

第四步：一次插入全文 —— `doc_insert_markdown file_id=<id> idx=0 markdown=file://<草稿绝对路径>`；遇 `document is not open` 则重开重试

第五步：统一表头样式 —— `doc_list_tables` 取全部 `table_id` → 逐表 `doc_set_table_cells`，`cells` 覆盖第 1 行全部列，`common_cell_properties` 设底色与居中；标签表（问题陈述/成功标准类）改为整表着色 + 首列居中

第六步：插图（仅参考件含图时）—— 草稿里保留「图：<标题>」题注行，用 `images` 配置（`doc_find` 定位题注 → `doc_insert_image` 插到题注之前）。`doc_find` 返回键是 `locations`，不是 `matches`

第七步：另存目标路径 —— `save_file file_id=<id> file_path=<目标绝对路径>`

第八步：回读校验 —— `open_file` 目标路径，等待流式打开完成后 `doc_resolve_document_structure mode=outline limit=0`，比对结构、表格维度、图片数与草稿及参考件

第九步：清理实例 —— `close_file` 后台校验实例，保留用户正在查看的实例

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
| 需要批量生成多份文档 | `scripts/build_docx.py` | 按 JSON 作业清单批量建文档、设页面/字体、格式化封面标题、分类着色、插图、另存（配置项见脚本 docstring） | **执行**（不读代码，看输出） |
| 需要读参考件全文 | `scripts/extract_docx_text.py` | 解析 OOXML 输出完整段落与表格（绕开预览截断） | **执行** |
| 需要单个 `doc_*` 工具的参数定义 | 由 `tencent-local-office-edit` skill 提供 | `python3 edsdk.py schema <工具名>` | 读取 |

## Source hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式约定（目标目录、文件命名、必须回读校验） |
| 2 | `tencent-local-office-edit` skill 的工具契约（schema 必填项与坐标约定） |
| 3 | Markdown → docx 的结构保真原则 |

## 自检

- [ ] 草稿标题层级与目标结构一致（1 个 H1 + 各章 H2 + 小节 H3）？
- [ ] 每张表都完成着色（着色调用数 = 表格数 − 显式跳过的封面表数）？标签表（问题陈述/成功标准类）是否整表着色？
- [ ] 封面标题已居中并套用目标字体字号（脚本输出 `title=True`）？
- [ ] 参考件含图时，图片已插入且题注在图片之后（脚本输出 `images=` 与配置条数一致）？
- [ ] 落盘文件的 `total_headings` / `total_tables` 与草稿及参考件一致？
- [ ] 全程未对同一 `file_id` 重复插入？
- [ ] 后台实例已清理，无孤儿实例残留？
- [ ] 脚本输出无 `WARN`？出现 `WARN` 必须查明原因后再交付，不得直接汇报成功
