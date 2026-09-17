# 数据模型与关键链路

## 项目位置与运行

| 项 | 值 |
|:--|:--|
| 应用根 | `~/Project/fitness-console/web/`（2026-09-12 修正：原 WorkBuddy 私有临时目录已不存在） |
| 核心文件 | `web/index.html`（单文件，约 3200 行） |
| 后端 | `server.js`（数据同步 `/api/data/{user}`、AI Key 分发 `/api/ai-key`） |
| 本机服务 | `http://127.0.0.1:8699`（Tailscale `100.88.254.127:8699`） |
| GitHub Pages | `jianglvbo/fitness-plan` → `https://jianglvbo.github.io/fitness-plan/`（静态版：无服务端同步，AI Key 手动填） |

## state 结构（defaultState）

```js
{
  profile: { height, weight, age, activity, gender, bodyFat },
  settings: { theme, mode, aiKey(加密), aiModel, aiBase },
  foods: [...], exercises: [...],   // 库（含力量运动 part/gear）
  dietPlan: { kcal, protein, fat, carb, foodIds[], meals: {breakfast|lunch|dinner: {proteinW,carbW,fatW}} },
  workoutPlan: { kcal, minutes, daysPerWeek, bias, exerciseIds[], splitType, weekSchedule:{1-7: cardio|strength|mixed|rest}, bodyParts:{周几: shoulder|chest|core|arm|leg}, myGear[] },
  planMode: 'detailed',             // 恒 detailed（无简单模式）
  plan: { generatedAt, mode: 'ai'|'local', days: {日期: {diet[], workout[]}} },
  aiPredictions: { 1m|3m|6m: {...} }, records: [...], suggestions: []
}
```

**新增字段铁律**：改 `defaultState()` 后必须同步 `migratePlanParams()`（周计划/部位/器械/三餐）或 `migrateExerciseCats()`（运动部位/器械），否则旧用户 localStorage 数据缺字段。

## 登录与账号

- `BUILTIN_USERS = [{username, salt, passHash}]`；salt 形如 `<user>-salt-0810`
- `hashPw(pw, salt)`：djb2 变体 + 200 轮，**必须从文件提取原函数计算**，勿凭猜
- 会话 `fitness-console-session`（localStorage）；守卫：boot 检查 + switchPage 入口 + window focus
- 账号：jlb / whx / hzk / wyb

## 运动力量体系

- 力量运动字段：`part`（shoulder/chest/core/arm/leg）+ `gear`（none/barbell/dumbbell/bar/machine/band/rope）
- 内置力量动作 29 个（含杠铃/无器械系列），常量 `BODY_PARTS`/`GEAR_LIST`/`GEAR_LABEL`
- 新增力量动作：带 part/gear；旧数据迁移在 `migrateExerciseCats`（按 id 或名称关键词推断）

## AI 链路（DeepSeek）

| 环节 | 函数 | 要点 |
|:--|:--|:--|
| 计划生成 | `generatePlan()` → `aiGeneratePlan()` + `mapAiPlan()` | prompt 带 weekly_schedule/body_parts/my_gear/meal_preferences；串行三步：计划→预测→建议（进度弹窗 `openProgressModal`） |
| 确定性修正 | `mapAiPlan` 内 | ① 休息日强制 workout=[] ② 训练日无安排用 `buildDayWorkout(dayType, part)` 补齐 ③ `calibrateDiet` 按目标热量缩放克数 |
| 预测 | `ensureAllPredicts(force, onProgress)` | predicting 锁防并发；force 重算 |
| 建议 | `fetchSuggestions()` | AI 失败降级 `localSuggestions()` |
| Key | `resolveAIKey()` | 服务端 keys.json 优先，404/失败降级本地设置加密 key |

## 自定义组件

- 下拉：`cxSelectHTML(id, value, options)` → `<div class="cx-select" data-cx data-val>`；`bindCustomSelects(root, onChange)` 绑定；**选择时只替换 head 文本节点、保留箭头 span**
- 多选：`.chip.active` 切换（如器械选择）
- 弹窗：`openModal(html)` / `closeModal()`（锁背景滚动 body.modal-open）；进度弹窗 `openProgressModal()`

## 常见坑（历史教训）

1. **section 交换丢开标签**：HTML 区块交换后必校验 `<section class="page" id=...>` 完整 + div 平衡（validate.py）
2. **双层渐变浑浊**：html 与 body 不可同设渐变背景，body 保持透明
3. **下拉文字累加**：cxSelect 更新值必须先删文本节点再插入，箭头 span 勿删
4. **AI 不遵守周计划**：休息日必须本地强制清空，勿信 LLM 自觉
5. **改 localStorage key 丢数据**：会话/数据/迁移 key 一律不动
6. **Pages 被墙**：本机直连 github.io 被重置，验证用代理 127.0.0.1:7890

## 部署流程

1. `cp ~/Project/fitness-console/web/index.html "$PAGES_REPO/index.html"`（`$PAGES_REPO`＝本机 `jianglvbo/fitness-plan` 的克隆目录，2026-09-12 实测本机尚无该克隆 → **首次发布前先 `git clone git@github.com:jianglvbo/fitness-plan.git`**；原写的 `/tmp/fitness-plan` 不是 git 仓库，push 必然失败）
2. 在 `$PAGES_REPO` 内 `git add/commit/push`（user.name=jianglvbo, user.email=jianglvbo@users.noreply.github.com）
3. Pages 自动构建（约 1-2 分钟）；验证走代理
