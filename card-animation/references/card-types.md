# 卡型字段手册

所有卡型共用的键：

| 键 | 说明 |
|---|---|
| `t` | 卡型（必填） |
| `color` | 该卡的强调色，决定色点、竖条、图标色、数字底色 |
| `pos` | `left`（默认）`right` `center`，决定落位与滑入方向 |
| `w` | 卡宽 px。不写则用下表的默认值，**一般不用手写** |
| `dur` | 该卡停留毫秒，默认 5000；不写则末张自动 6200 |

默认宽度：`grid 900 · steps 900 · levels 1180 · stats 780 · compare 940 · chars 900 ·
chips 800 · swatch 900 · poem 940 · flow 1200 · end 900`

---

## title — 封面

```python
dict(t="title", color=MAIN, kicker="小一班 · 社会领域",
     h1="大家一起玩真快乐", sub="一起玩 · 轮流玩 · 交换玩，和朋友在一起最开心")
```

- `kicker` 小字行（班级 + 领域），限 16 字
- `h1` 主标题，1 行最好；8 字以内视觉最稳，最多 12 字
- `sub` 副标题 1 行，≤ 32 字
- 分隔线用主题色渐变，不可配

## steps — 目标 / 步骤 / 分点

```python
dict(t="steps", color=BLUE, pos="left", head="这次活动我们要做到", kicker="GOALS",
     steps=[("乐意分享", "学习与同伴合作分享的方法，愿意把玩具和好朋友一起玩"),
            ("大胆表达", "愿意主动和同伴共同游戏，大胆说出「我想和你一起玩」"),
            ("体验快乐", "体验大家一起玩的快乐，喜欢幼儿园的集体生活")])
```

- `steps` 3 条最稳，最多 5 条（5 条时说明压到 20 字内）
- 名称 ≤ 6 字，说明 ≤ 30 字
- 编号自动 01/02/03，不用自己写序号

## quote — 提问 / 原话 / 结论

```python
dict(t="quote", color=CORAL, pos="right",
     lines=["这个小女孩捂着腮帮子，她怎么了？", "牙齿为什么会坏掉了？"],
     src="看一看 · 猜一猜：是小红脸和小蓝脸在她牙齿上造房子了")
```

- `lines` 1–3 行，每行 ≤ 20 字；左侧有竖色条，宽度贴合文字
- `src` 底部说明（灰色小字），≤ 40 字，单行不换行
- `big=True` → 字号 46px，用作口诀/金句卡；此时每行 ≤ 14 字，最多 3 行
- 引用孩子原话时用「」包住，不要加引号句

## poem — 儿歌 / 口诀

```python
dict(t="poem", color=ORANGE, pos="center", head="火车就要开", kicker="CHANT",
     lines=["小朋友们快快来，我的火车就要开，", "车上朋友多，朋友多，真热闹，", "唱起歌来乐淘淘。"],
     src="游戏 · 一个跟一个搭肩开火车，开到好朋友身边抱一抱")
```

- 4–5 行，每行 ≤ 14 字；行与行之间会依次上浮，适合带读
- 和 `quote big=True` 的区别：`poem` 带卡头（标题 + 英文小标），`quote big` 没有

## levels — 2–5 栏并列

```python
dict(t="levels", color=ORANGE, pos="center", cols=3,
     head="一起玩的三个小妙招", kicker="THREE WAYS",
     rows=[("方法一", "一起玩", "你搭积木我来递，两个人玩更热闹"),
           ("方法二", "轮流玩", "你先玩一会儿，我再玩一会儿"),
           ("方法三", "交换玩", "我的换你的，两样玩具都玩到")])
```

- `rows` 每项是 `(标签, 名称, 说明)`：标签是上方的小字（方法一 / 01 / 秘密二），名称是大字
- 3 栏最稳；5 栏也能用（w=1180 时每列约 200px），此时说明压到 **8 字内**
- 标签 ≤ 4 字，名称 ≤ 5 字

## grid — 带图标的清单

```python
dict(t="grid", color=BLUE, pos="right", cols=1, w=880, head="认识玩具的家", kicker="HOME",
     items=[("bin", "玩具筐 · 玩具宝宝的小家", "住着小汽车、积木和娃娃"),
            ("window", "玩具柜 · 玩具筐的大家", "所有小家都住在这里")])
```

- `items` 每项 `(图标, 名称, 说明)`，可选第 4 位指定该格颜色
- 图标写 `None` 就自动变成 `01/02` 序号
- `icon_solid=True` 让图标底色变成实色 + 白色线条（适合四色垃圾桶这类需要强区分的）
- 1 列（w=880）用于「问题 + 追问」；2 列（w=1000）用于并列项
- 可用图标：`ask eye hand talk check cross star drop sun moon leaf tree brush palette
  bin recycle earth mask bridge book music heart clock body bulb cup window flag`
- 名称 ≤ 12 字，说明 ≤ 26 字

## chips — 词卡串

```python
dict(t="chips", color=MAIN, pos="center", head="六个好方法，记在心里", kicker="SIX WAYS",
     chips=["勤洗手", "多喝水", "多锻炼", "常通风", "增减衣物", "少去人多的地方"])
```

- 3–8 个，每个 ≤ 7 字；自动换行、带底色
- 适合「一串要点」，不适合有解释的内容（那用 `grid` 或 `steps`）

## compare — 左右对比

```python
dict(t="compare", color=BLUE, pos="center", w=1040,
     head="过去和现在，大不一样", kicker="THEN & NOW",
     left=("过去的生活", ["衣服补了又补，食物很缺少", "住的是简陋的小土房"]),
     right=("现在的生活", ["食物丰富，想吃什么有什么", "高楼大厦，又漂亮又安全"]),
     right_tone=RED,
     note="议一议：从现在的幸福生活来得容易吗")
```

- `left` / `right` 必须是 **`(标题, [要点...])` 二元组**。写成三元组会解包报错
- 每侧 2–3 条，每条 ≤ 18 字；条数不等也可以，但视觉上相等更好看
- `note` 是底部小字结论/追问，≤ 40 字
- 默认左灰右主题色；可用 `left_tone` / `right_tone` 分别指定

## chars — 汉字 / 字母卡

```python
dict(t="chars", color=BLUE, pos="center", head="象形字：日和月", kicker="CHINESE",
     items=[("日", "像太阳，中间一横是光"), ("月", "像弯弯的月亮")], fs=96)
```

- 字体走宋体（比手写体更像课本），`fs` 控制字号，2–4 个字时可到 96–118
- 每个字配一句注释，≤ 12 字
- 字多时（5 个以上）`fs` 降到 74 左右

## swatch — 色卡

```python
dict(t="swatch", color=BROWN, pos="center", head="秋天的三种暖色", kicker="COLORS",
     items=[("#C0503C", "枫叶红", "像一团小火苗"), ("#D2922A", "杏叶黄", "像一片金色阳光"),
            ("#8B5E3C", "枯叶褐", "像大地和树皮")],
     note="暖色调：让人想到太阳、火和秋天")
```

- 2–4 个色点，命名 + 一句比喻（≤ 8 字）
- 色值直接写十六进制，圆点会显示真实颜色

## stats — 数字卡

```python
dict(t="stats", color=RED, pos="center", label="终极关 · 怎么算分",
     boxes=[("5", "分 / 个大沙包"), ("60", "秒倒计时")],
     note="小沙包 1 个记 1 分 · 一分钟内看哪队拿得多")
```

- `boxes` 2–3 组，数字 ≤ 4 字符，单位 ≤ 8 字
- 适合比分、时长、人数、数量对比

## flow — 流程

```python
dict(t="flow", color=BLUE, pos="center", head="一次完整的抢包", kicker="HOW TO JUMP",
     nodes=["出发点", "跳过地垫", "跳上跳下", "抢到软包"])
```

- 3–5 个节点，每个 ≤ 5 字；节点间自动加箭头
- 只有先后顺序且节点极短时才用；有解释就用 `steps`

## end — 结尾

```python
dict(t="end", color=GREEN, pos="center", w=900,
     h1="和朋友在一起，最快乐！",
     sub="一起玩 · 轮流玩 · 交换玩，我们都是爱分享的好宝宝",
     stats=[("一起玩", "更热闹"), ("轮流玩", "都开心"), ("交换玩", "都玩到")])
```

- `h1` ≤ 12 字（字号 62px）
- `sub` ≤ 34 字
- `stats` 3–4 组，第一项是大字、第二项是小字；用来收束主题（不是数字时也成立，如「看 / 颜色」）
