# -*- coding: utf-8 -*-
"""示例：一套 8 张卡的完整内容脚本。

复制这个文件到你的工作目录，改 CARDS 就行：
    python cards.py            # 生成 cards.html（同目录）
    python <skill>/scripts/preview.py cards.html
    python <skill>/scripts/render_cards.py cards.html out/demo.mov

引擎位置可用环境变量覆盖：export CARD_KIT=/path/to/.../scripts
"""
import os
import sys

KIT = os.environ.get("CARD_KIT") or os.path.expanduser(
    "~/.workbuddy/skills/courseware-card-animation/scripts")
sys.path.insert(0, KIT)
import kit  # noqa: E402

# 三种主色 + 一种强调色，一节课内不要超过 4 种
MAIN = "#C0503C"    # 主色：封面、封面感的话
COOL = "#3C7CB0"    # 冷色：观察、讲解
WARM = "#D2922A"    # 暖色：操作、游戏
GREEN = "#4E946A"   # 收尾：小结、约定

CARDS = [
    # 1 封面：kicker / h1 / sub 三段
    dict(t="title", color=MAIN,
         kicker="中二班 · 科学领域",
         h1="秋天的小树叶",
         sub="看一看 · 比一比 · 说一说：树叶为什么会变颜色？"),

    # 2 目标：最多 3 条，每条 name ≤ 6 字、desc ≤ 30 字
    dict(t="steps", color=COOL, pos="left",
         head="这次活动我们要做到", kicker="GOALS",
         steps=[("看一看", "观察树叶的颜色、形状和纹理，发现它们的不同"),
                ("比一比", "把树叶按颜色或形状分类，说出自己的理由"),
                ("说一说", "用完整的话讲述自己的发现，愿意听同伴说")]),

    # 3 提问：lines 每行一句，src 是底部的说明
    dict(t="quote", color=WARM, pos="right",
         lines=["树上的叶子，为什么有的绿、有的黄？",
                "它们是从哪里开始变颜色的？"],
         src="看一看 · 猜一猜：先说出自己的想法，再去找答案"),

    # 4 儿歌：4~5 行，念的时候可以停在这张
    dict(t="poem", color=MAIN, pos="center",
         head="小树叶", kicker="CHANT",
         lines=["小树叶，飘呀飘，", "飘到天上像小鸟。",
                "小树叶，落呀落，", "落在地上睡一觉。"],
         src="跟着老师念一念，加上手上的动作"),

    # 5 三栏并列：tag / name / desc
    dict(t="levels", color=COOL, pos="center",
         head="树叶的三个秘密", kicker="SECRETS",
         rows=[("秘密一", "颜色", "绿色、黄色、红色，还有一半绿一半黄"),
               ("秘密二", "形状", "像手掌、像小船、像小针、像小扇子"),
               ("秘密三", "纹理", "摸一摸叶脉，粗粗的、一条一条")]),

    # 6 左右对比：left/right 都是 (标题, [要点...])
    dict(t="compare", color=GREEN, pos="center", w=1000,
         head="夏天的叶子和秋天的叶子", kicker="THEN & NOW",
         left=("夏天的叶子", ["绿绿的，密密地长在枝头", "摸上去软软的、潮潮的"]),
         right=("秋天的叶子", ["慢慢变黄、变红，一片片飘下来", "摸上去干干的、脆脆的"]),
         right_tone=WARM,
         note="小结：天变凉了，树叶里的颜色就变了样"),

    # 7 图标宫格：icon 名见 references/card-types.md；不给 icon 就自动用 01/02 序号
    dict(t="grid", color=COOL, pos="left", cols=1, w=880,
         head="动手做 · 树叶分类", kicker="DO",
         items=[("hand", "按颜色分", "把绿叶、黄叶、红叶分别放到三个筐里"),
                ("talk", "按形状分", "手掌形、小船形、小针形，说说你为什么这么分")]),

    # 8 结尾：h1 + sub + 三到四个短语
    dict(t="end", color=GREEN, pos="center", w=900,
         h1="每片叶子都不一样",
         sub="回家和爸爸妈妈捡几片树叶，看看还能发现什么",
         stats=[("看", "颜色"), ("摸", "纹理"), ("说", "发现")]),
]

if __name__ == "__main__":
    kit.build(CARDS, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "example.html"))
