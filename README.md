# courseware-ppt-video

幼儿园/教育课件的两条制作流水线，均为可被 AI 工具直接加载的 skill。

| Skill | 目录 | 产出 | 适用场景 |
|---|---|---|---|
| `courseware-ppt-video` | 仓库根目录 | 重制后的 `.pptx` + 1080p25 弹簧动效 `.mp4` | 整页课件讲解视频 |
| `courseware-card-animation` | [`card-animation/`](card-animation/) | 带 alpha 的 ProRes 4444 `.mov`（透明卡片） | 短视频/口播画面上的字卡叠加 |

两者可以串联：先用根目录的流程做课件定稿，再挑重点页用 `card-animation/` 出透明字卡叠到实拍画面上。

## 安装到其他 AI 工具

```bash
git clone https://github.com/zbitextn-svg/courseware-ppt-video.git

# 整页视频流程（根目录即一个 skill）
cp -r courseware-ppt-video ~/.claude/skills/courseware-ppt-video

# 透明卡片流程（子目录是一个独立 skill）
cp -r courseware-ppt-video/card-animation ~/.claude/skills/courseware-card-animation
```

WorkBuddy 用户直接放到 `~/.workbuddy/skills/` 下即可。

## 依赖

```bash
pip install python-pptx pillow fonttools numpy
brew install --cask libreoffice   # 整页视频流程
brew install ffmpeg               # 两条流程都需要
```

## card-animation 用法

```bash
# 1. 导出课件文字/图片
python3 card-animation/scripts/dump_pptx.py 课件.pptx > dump.txt

# 2. 参照 card-animation/assets/example_cards.py 写内容清单
python3 my_cards.py                  # → cards.html

# 3. 渲染前先校版式
python3 card-animation/scripts/preview.py cards.html

# 4. 逐帧渲染透明视频 + 抽帧校验 + 米底预览
python3 card-animation/scripts/render_cards.py cards.html out/cards.mov
python3 card-animation/scripts/qa_cards.py out/cards.mov --flat
```

13 种卡型（封面/流程/引文/儿歌/层级/网格/标签/步骤/数据/色卡/汉字/对比/结尾）的字段说明见
[`card-animation/references/card-types.md`](card-animation/references/card-types.md)。
