# 控制台风格（console-style）设计令牌规范

风格本质：**玻璃拟态 + 极光渐变 + 多主题 token 的类苹果控制台 UI**。

来源：`web/index.html` `<style>` 内 `:root` 与各 `[data-theme]` 块。改动样式必须同步全部主题，禁止单主题适配。

## 全局基础变量

```css
:root{
  --radius: 18px; --radius-sm: 12px; --radius-lg: 24px;
  --shadow: 0 8px 32px rgba(0,0,0,.10), 0 2px 8px rgba(0,0,0,.06);
  --shadow-sm: 0 2px 12px rgba(0,0,0,.07);
  --blur: 22px;
  --font: -apple-system, "SF Pro Display", "PingFang SC", "Segoe UI", sans-serif;
}
```

## 主题体系：10 主题 × 日/夜

主题键：`aurora`(默认 靛紫) / `emerald`(翡翠绿) / `rose`(玫瑰粉) / `sakura` / `sunset` / `amber` / `ocean` / `midnight` / `graphite` / `matcha`。每套含：

| 变量组 | 说明 | 示例（aurora light） |
|:--|:--|:--|
| `--bg1/2/3` | 三色渐变底（135° 对角） | `#eef2ff → #fdf2f8 → #f0f9ff` |
| `--glass/-strong/-border` | 毛玻璃底/强底/边框 | `rgba(255,255,255,.58/.78/.75)` |
| `--text/-2/-3` | 三级文字色 | `#1c1c28 / #5c5c70 / #9a9ab0` |
| `--accent / --accent-2` | 强调色双色 | `#6366f1 / #a855f7` |
| `--accent-grad` | 强调渐变（135°） | `linear-gradient(135deg,#6366f1,#a855f7)` |
| `--good/--bad/--warn` | 语义色 | `#10b981 / #f43f5e / #f59e0b` |
| `--chart1~5` | 图表五色 | `#6366f1/#f43f5e/#f59e0b/#10b981/#38bdf8` |

## 风格基调

- **玻璃拟态**：`.card` = `background:var(--glass)` + `backdrop-filter:blur(var(--blur)) saturate(180%)` + `border:1px solid var(--glass-border)` + `border-radius:var(--radius)` + `--shadow-sm`
- **背景**：渐变在 `html`（fixed，**单层**——body 不设背景，双层叠加会浑浊）；背景光斑 `.blob`（blur 80px，drift 动画）叠加
- **过渡不露白**：`html` 渐变背景承载滚动回弹区域，`overscroll-behavior:none`（html/body）
- **表单**：select/input `appearance:none` + 自定义 SVG 箭头 + 聚焦光晕；数字输入去 spinner
- **自定义下拉**：`cxSelectHTML(id, value, options)` + `bindCustomSelects(root, onChange)`（毛玻璃弹层）；选择时仅替换 head 文本节点，保留箭头（勿删 span）
- **图标**：线性 SVG（stroke-width 2，round cap），`iconSvg(key, color, size)`
- **动效**：页面切换 `pageIn`（0.5s cubic-bezier(.22,1,.36,1)）；卡片 `cardIn`；主题过渡 `.4s ease`

## 分类色（运动/食物库）

- 运动类别 `CAT_META`：strength 蓝 #2563EB / cardio 红 #EF4444 / yoga 紫 / daily 灰
- 力量部位 `BODY_PARTS`：shoulder 肩 #f97316 / chest 胸 #ef4444 / core 腹 #eab308 / arm 手 #8b5cf6 / leg 腿 #22c55e
- 食物大组 `LIB_GROUPS`：蛋白质 / 主食碳水 / 蔬菜 / 脂肪&水果（各带色）
