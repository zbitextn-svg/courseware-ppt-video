---
name: courseware-card-animation
description: 把幼儿园/学校课件（.pptx 或已整理好的讲稿）拆成一套「透明卡片动画」视频：米白圆角纸卡、逐张滑入、元素依次上浮，输出带 alpha 通道的 ProRes 4444 MOV（1920×1080/25fps），可直接叠在实拍视频或录屏上；同时给出叠底预览 mp4 和每张卡的 1080p 静帧。Use when the user asks to 把课件/PPT 做成卡片动画、卡片视频、透明卡片、无背景素材、叠在视频上的卡片、逐条出示的课堂卡片，或要复用同一套卡片版式批量出多套课件视频。
---

# 课件 → 透明卡片动画

把一节课拆成 10–18 张卡片，每张停留 5 秒，逐张从侧边滑入，卡内元素依次上浮。
成品是**带透明通道的视频**，剪映/PR 里直接压在原片画面上，不需要抠像。

## 成品规格

| 项 | 值 |
|---|---|
| 画布 | 1920×1080，25fps |
| 视频 | ProRes 4444 / `yuva444p12le` / alpha 16bit（`.mov`） |
| 卡片 | 米白纸卡 `#FAF6EC`，圆角，左/右/居中三种落位 |
| 节奏 | 每张 5s、末张 6.2s，入场 640ms、出场 480ms |
| 附带 | 叠底预览 `.mp4`（米色底，先看效果）、`stills/card_XX.png`（做封面/暂停页）、总览图 |

## 工作流

### 1. 读出课件内容

```bash
python scripts/dump_pptx.py 课件.pptx > dump.txt
```

拿到每页的文字（带字号，用来判断主标题/副标题/正文）、表格、图片尺寸、备注。
不要直接照搬页面文字——PPT 的短句要补成能独立读懂的卡片语言，教师口播的内容不必全进卡片。

### 2. 规划卡片

一份 8–9 页的课件通常拆成 **10–17 张卡**。拆法：

- 封面 1 张；活动目标 1 张（3 条）；每个环节 1–2 张；结尾 1 张
- 长段落拆成「问题卡 + 方法卡 + 口诀卡」
- 并列的三项（三个方法、三种颜色、三个动作）用 `levels` 三栏，别拆成三张
- 儿歌/口诀单独成 `poem` 卡，方便课堂停在这里带读

### 3. 写内容脚本

复制 `assets/example_cards.py` 到工作目录，只改 `CARDS`：

```python
KIT = os.environ.get("CARD_KIT") or os.path.expanduser(
    "~/.workbuddy/skills/courseware-card-animation/scripts")
sys.path.insert(0, KIT)
import kit

CARDS = [dict(t="title", color="#C0503C", kicker="中二班 · 科学领域",
              h1="秋天的小树叶", sub="…"), …]

kit.build(CARDS, "cards.html")
```

13 种卡型的字段见 [references/card-types.md](references/card-types.md)，版式与字号规则见
[references/design.md](references/design.md)。先只写 2–3 张跑通，再加满。

### 4. 截图校对（必做）

```bash
python scripts/preview.py cards.html
```

输出 `stills_<name>/c01.png…` 和总览 `ov_<name>.jpg`。**逐张看**：

- 文字有没有溢出卡片、有没有掉到底边外
- 居中卡是否真的居中（左右留白相等）
- 图标是否糊成一团（细节少的图标要放大）
- 同一环节的卡片字号是否一致

不通过就改 `CARDS`（或 `references/design.md` 里的宽度/字号），重新生成再看，**别直接渲染**。

### 5. 渲染 + 校验 + 叠底预览

```bash
python scripts/render_cards.py cards.html out/cards.mov
python scripts/qa_cards.py out/cards.mov --flat
```

`qa_cards.py` 每张卡抽一帧拼成 `qa_<name>.jpg`，并报空白帧数量；`--flat` 另出米底
`cards_preview.mp4`。**空白帧必须为 0**，校验图要逐张过。

交付三个文件：`（透明卡片动画·ProRes4444）.mov`、`（透明卡片·叠底预览）.mp4`、
`（卡片全览）.jpg`，静帧目录另有 1080p PNG。

## 卡型速查

| `t` | 用途 | 关键字段 |
|---|---|---|
| `title` | 封面 | `kicker` `h1` `sub` |
| `steps` | 目标、步骤、分点说明 | `head` `steps=[(名称, 说明)]` |
| `quote` | 提问、原话、结论；`big=True` 放大成口诀卡 | `lines` `src` |
| `poem` | 儿歌、口诀 | `head` `lines` `src` |
| `levels` | 2–5 栏并列（方法/颜色/动作） | `head` `cols` `rows=[(标签, 名称, 说明)]` |
| `grid` | 带图标的清单，1–2 列 | `head` `cols` `items=[(图标, 名称, 说明)]` |
| `chips` | 一串短语/词卡 | `head` `chips` |
| `compare` | 左右对比（过去/现在、能/不能） | `left` `right` `note` |
| `chars` | 汉字、字母卡 | `items=[(字, 注释)]` `fs` |
| `swatch` | 色卡（美术课） | `items=[(色值, 名称, 比喻)]` `note` |
| `stats` | 数字（时间、分值、数量） | `label` `boxes=[(数字, 单位)]` `note` |
| `flow` | 四步流程 | `head` `nodes` |
| `end` | 结尾 | `h1` `sub` `stats=[(字, 说明)]` |

所有卡型都接受 `color`（色点/竖条/图标色）、`pos`（`left`/`right`/`center`）、
`w`（卡宽，一般不用手写）、`dur`（该卡毫秒数）。

## 配色规则

- 一节课 **2 个主色 + 1 个强调色**，超过 4 种会显乱
- 按环节分色，不按页面顺序换色：封面/情境、讲解、操作/游戏、小结各一色
- 常用：暖橙 `#D9832A`、砖红 `#C0503C`、靛蓝 `#4A5BA8`、科学青 `#2B8A7E`、木色 `#C1794A`、墨紫 `#8C5A9E`
- 浅底由 `kit.tint(色, 0.13)` 自动算，别手动调

## 硬性约束

- **卡片里不放照片**。这套是纯文字卡，实拍照片会破坏统一的纸卡质感；需要图就用 `ICONS` 里的线性图标
- 不要用 emoji（字体子集不含，跨机器显示不一致）
- 不要用 `√ ✗` 之类符号，改写成「能转 / 不能转」
- 字体是系统中文显示体（手写/圆体），经子集内嵌进 HTML。换机器要设 `CARD_FONT`，或把字体放到 `assets/fonts/display.ttf`
- 渲染必须前台运行：无头 Chrome 在后台任务里会被调度器连坐杀掉

## 参考

- [references/card-types.md](references/card-types.md) — 13 种卡型的完整字段、限制、选用建议
- [references/design.md](references/design.md) — 卡宽默认值、字号层级、对齐与留白、特殊卡处理
- [references/pitfalls.md](references/pitfalls.md) — 踩过的坑与修法（出问题先看这个）
