# 版式与字号规则

## 画布与落位

- 画布 1920×1080，卡片垂直居中（`.card` 高 1080 + flex 居中）
- 左落位 `left:96px`、右落位 `right:96px`、居中 `left/right:0 + margin auto + fit-content`
- 落位决定滑入方向：`left` 从左侧滑入、`right` 从右侧、`center` 从下方上浮
- 连续 3 张同侧会显得呆板，按「左 → 右 → 中」交替排

## 字号层级（已固化，不要逐卡覆写）

| 元素 | 字号 | 说明 |
|---|---|---|
| 封面主标题 `.h1` | 86px | 封面的视觉锚点 |
| 结尾主标题 `.eh1` | 62px | 比封面小一级 |
| 金句卡 `.quote.big .ql` | 46px | 全员可读，适合停住带读 |
| 数字 `.sbig` | 82px | 分值、秒数 |
| 引文 `.ql` | 36px | 默认引文/提问 |
| 儿歌 `.pl` | 34px | 行距 1.5 |
| 并列大标题 `.lname` / 对比标题 `.ctag` | 34 / 30px | |
| 流程节点 `.fnode` | 30px | 胶囊形 |
| 清单名称 `.stx b` / `.gtx b` | 27 / 25px | |
| 正文说明 `.stx span` / `.ctxt p` | 18.5px | 卡片里最小正文 |
| 底部注脚 `.qsrc` / `.swnote` | 17–19px | 灰色，单行不换行 |

## 长度预算（写内容前先数一遍）

内容可用宽度 ≈ 卡宽 − 左右内边距（约 60–100px）。中文按「1 字 ≈ 1 em」估算：

- `.h1` 86px，卡宽 880，可用 ≈ 760px → **≤ 8 字最稳，绝对上限 12 字**
- `.ql` 36px，quote 卡最小宽 780 → 每行 **≤ 20 字**
- `.quote.big .ql` 46px → 每行 **≤ 14 字**，最多 3 行
- `.pl` 34px，poem 940 → 每行 **≤ 14 字**
- `.stx span` 18.5px，steps 900 − 编号列 40 − 间距 → 每行 **≤ 30 字**（超了会换行，两行还行，三行就挤）
- `.ldesc` 16px，levels 3 栏每列 ≈ 370px → 每列 **≤ 20 字**；5 栏每列 ≈ 210px → **≤ 8 字**
- `.ctxt p` 18.5px，compare 每侧 ≈ 420px → 每条 **≤ 18 字**
- `.qsrc` 是 `white-space: nowrap`，**超长不会换行，直接溢出卡片** → 严格 ≤ 40 字

## 居中卡为什么用 fit-content

`pos=center` 用 `left:0;right:0;margin:0 auto;width:fit-content` 而不是算 `margin-left:-w/2`。
后者要求每张卡显式知道自己的宽度，宽度算错就会偏；`fit-content` 让卡片按内容自适应并真正居中。
**副作用**：宽度为 `fit-content` 时，卡内子元素不会自动撑满，所以 `.frow`、`.sheet.grid` 这类容器
在 builder 里显式加了 `width:100%`——新增卡型时别忘了这一步。

## 图标

- `.gico` 68×68 圆角方，内嵌 svg 48×48
- 细线条图标（如小三角、衣架）在 1080p 下会糊，要么放大 svg，要么换成结构更清楚的图标
- 同一个图标出现两次以上时，改 `icon_solid=True` 用实色底 + 白线，区分度更高
- 试过但不成形的图标：`branch`（树枝）三版都糊——直接用 `brush` 表达「用笔尖」

## 动画机制（改版式时别破坏）

- JS 暴露 `window.__render(i, t)`：把第 i 张卡渲染到第 t 毫秒的状态，**必须是确定性的**（同 t 同结果），否则逐帧渲染会抖
- 卡片内元素用 `data-m`（动作：up/right/pop）和 `data-d`（延迟 ms）标记，`__render` 按 t 反推每个元素的位置
- 页面参数 `?shot#/N` 用于静态截图模式
- `window.__meta = {n, durs, inn, out, live}`；`live` 是需要逐帧驱动的动态卡（如旋转的情绪轮）
- 换卡时 `cards[k].el.style.display = (k===i) ? 'flex' : 'none'`，**必须是 `flex`**，写 `block` 会丢掉垂直居中
