---
name: docx-template-fill
description: 把内容填入既有的 Word（.docx）模板并**保留模板原格式**：复制模板 → 替换占位文本 → 锚点后插入 → 插图 → 填表 → 保存，全程只改文本、不碰样式。触发词：「填到模板里」「按模板填」「保持模板格式不变」「把内容填进这份模板」「模板填充」。排除条件：从零生成新 docx（走 docx-from-markdown）；需要改写模板样式或版式（走 tencent-local-office-edit / tencent-docx）。
agent_created: true
---

# docx-template-fill

## Default stance

核心原则：

1. **格式不变的唯一保证是「只改文本」** —— 全程不得调用 `doc_set_document_style` / `doc_update_text_property` / `doc_modify_paragraph` / `doc_set_table_properties` 等任何格式类工具；新增文本靠继承既有段落属性获得格式
2. **替换目标一次性定位、降序执行** —— 所有 `doc_find` 必须在**任何编辑之前**完成，再按 `begin` 降序 `doc_replace_text`；边找边改必然因文本长度变化而错位
3. **插入位置在编辑之后重新解析** —— 锚点后插入的坐标不能沿用编辑前的快照，必须编辑完成后重新 `doc_resolve_document_structure`
4. **表格用当前顺序解析 `table_id`** —— 多次编辑后旧 `table_id` 会失效（报 `table_id not found`），必须重新 `doc_list_tables` 按序取用
5. **模板原件不动** —— 复制成目标文件后只编辑副本，模板保持字节级不变
6. **交付前必须举证格式未变** —— 逐层比对页面设置 / 标题字体 / 样式表 / 表格底色 / 被替换段的 pPr 与 run rPr

禁止行为：

1. **禁止为了「好看」调整字体字号或对齐** —— 用户要的是模板原样，不是重新设计
2. **禁止删除段落来清理提示行** —— 用文本置空代替 `doc_delete_paragraph`，避免结构与坐标变动
3. **禁止把 `doc_replace_text` 的参数写成 `begin`/`end`** —— 它是 `ranges: [{begin, end}]` + `text`
4. **禁止用长串或非唯一串做定位** —— 结构预览在 compact 模式仅回约 4 字，且 `doc_find` 只取首个命中，match 必须短且唯一
5. **禁止在未确认模板占位结构前动手** —— 先取全文与结构坐标，确认每个占位的段落范围与表格维度

## Workflow

第一步：读模板 —— 用 `scripts/extract_docx_text.py`（来自 `docx-from-markdown` skill）取模板全文，看清占位符、表格维度与提示语

第二步：取结构坐标 —— `doc_resolve_document_structure mode=full text_preview_length=200 limit=0`，导出每个占位段落的 `start_index/end_index` 与表格 `table_id`，落盘备用

第三步：核对页面与样式基线 —— `doc_get_section_property` + 标题/正文字体 + 表格表头底色，记录下来作为交付前的比对基准

第四步：写填充配置 —— `fill.json`（见下节字段），edits 的 `match` 用占位原文的短片段

第五步：执行 —— `python3 scripts/fill_template.py fill.json`（脚本内部：复制模板 → 定位 → 降序替换 → 锚点插入 → 插图 → 填表 → 保存）

第六步：回读校验内容 —— 提取成品全文，确认占位符 0 残留、各章节内容到位

第七步：举证格式未变 —— 比对模板与成品的：页面设置、标题 run 属性、styles.xml（按样式名比属性，忽略序列化顺序与 styleId 重映射）、表格单元格底色、被替换段落的 pPr 与首个 run 的 rPr

第八步：清理实例 —— `close_file` 后台实例；未保存的实例需 `force=true`

### 决策点

- **锚点后连续空段落不足** → 说明模板该处没有预留槽位，改用「在锚点段落末尾追加文本」或与用户确认，不要强行插到别的段落后（会继承错误格式）
- **成品要替换模板原件文件名** → 先确认模板另有副本，再改名；默认产出独立文件
- **模板含图而新文档需要图** → 把 `images` 指向新图，按题注 `begin` 插到题注之前（与 `docx-from-markdown` 同法）

## Output format

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| 模板路径 | string | 原件，须保持未被修改 |
| 成品路径 | string | 填充结果，独立文件 |
| 替换处数 | int | edits 命中数，须等于配置条数 |
| 占位残留 | int | 成品中 `XXXX` 等占位数量，应为 0 |
| 格式比对 | string | 逐层比对结论：一致 / 差异项 |

## Relative files

| 场景 | 加载文件 | 内容 | 方式 |
|:---|:---|:---|:---|
| 执行填充 | `scripts/fill_template.py` | 按 `fill.json` 完成复制→替换→插入→插图→填表→保存 | **执行**（不读代码，看输出） |
| 读模板全文 | `docx-from-markdown/scripts/extract_docx_text.py` | 解析 OOXML 取完整段落与表格 | **执行** |
| 查 `doc_*` 参数定义 | 由 `tencent-local-office-edit` skill 提供 | `python3 edsdk.py schema <工具名>` | 读取 |

## Source hierarchy

| 优先级 | 来源 |
|:---|:---|
| 1 | 用户显式约定（保持模板格式不变、目标路径与命名） |
| 2 | 模板自身的格式定义（段落属性、样式表、表格底色） |
| 3 | `tencent-local-office-edit` skill 的工具契约 |

## 自检

- [ ] 模板原件字节未变（大小/时间戳）？成品为独立文件？
- [ ] 成品占位符 0 残留，且不含模板提示语（如「请简要概括…」「如果有多个场景…」）？
- [ ] 全程未调用任何格式类工具（只 `doc_replace_text` / `doc_insert_text` / `doc_insert_image` / `doc_set_table_cells` 的 text）？
- [ ] 页面设置、标题字体、样式表属性、表格底色与模板一致？
- [ ] 插入内容落在正确章节（没串到别的段落里）？图片在题注之前？
- [ ] 后台实例已清理？
