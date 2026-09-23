# Conventional Commits 提交信息规范（git-ops）

用户未自定义提交信息时按本规范生成。git 硬性要求：subject 与 body 之间必须空行（否则整段被当标题）；`-m` 一次只传一段，多段用多个 `-m`。

## 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **type**（必填，英文）：`feat` 新功能 / `fix` 修复 / `docs` 文档 / `style` 格式 / `refactor` 重构 / `perf` 性能 / `test` 测试 / `build` 构建 / `ci` CI / `chore` 杂项 / `revert` 回滚
- **scope**（可选）：影响范围，如 `(investment-framework)`；跨模块或无法归一时省略
- **subject**（必填）：一句话描述，中文 ≤30 字、英文 ≤50 字符，结尾不加句号
- **body**（可选）：空行分隔，解释「为什么改」而非「改了什么」；多行时每行 ≤72 字符
- **footer**（可选）：空行分隔——`BREAKING CHANGE: <描述>` 或 issue 引用（`Closes #123`）

## 正反例

| | 示例 |
|:--|:--|
| ❌ 无类型、无空行 | `git commit -m "修复了问题 并且更新了文档"` |
| ✅ 拆分 + 带类型 | `git commit -m "fix(api): 修复token过期未刷新" -m "docs: 补充部署说明"` |
| ❌ subject 写「改了什么」的流水账 | `feat(api): 修改了三个文件，加了函数，删了注释` |
| ✅ subject 写「结果」 | `feat(api): 新增用户认证接口` |

## 完整示例

```
feat(api): 新增用户认证接口

实现 OAuth2 授权码流程，支持 refresh_token 轮换，
用于移动端免密续期场景。

BREAKING CHANGE: /auth/token 响应格式变更
Closes #123
```

```bash
git commit -m "feat(api): 新增用户认证接口" -m "实现 OAuth2 授权码流程，支持 refresh_token 轮换，用于移动端免密续期场景。" -m "BREAKING CHANGE: /auth/token 响应格式变更" -m "Closes #123"
```

## 落地规则

- **简单变更**（一行能讲清）：只写 subject
- **复杂变更**（多维度/有理由背景）：subject + body
- **破坏性变更 / 有关联 issue**：追加 footer
