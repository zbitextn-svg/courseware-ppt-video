---
name: courseware-ppt-video
description: 把教案/旧 PPT 优化重制为差异化画风的课件 PPT，并把 PPT 合成为 1080p25 弹簧动效演示视频（MP4）。适用于：制作或重制幼儿园/教育课件 PPT、PPT 转动画演示视频、批量课件风格重制、只有 Word 教案需要从零构建课件。触发词：做课件、做PPT、PPT转视频、课件动画视频、重制课件。
---

# 幼儿园课件 PPT + 动画视频制作

## 依赖

```
pip install -r scripts/requirements.txt
# macOS 还需: brew install --cask libreoffice ffmpeg
```

## 工作流 A：PPT 制作（优化/重制课件）

按 [references/ppt-design.md](references/ppt-design.md) 的循环执行，核心要点：

1. **画风必须按主题衍生**，多份课件间禁止同质化（每份提取 2 主色 + 1 装饰母题，贯穿全部页面）。
2. 每页走「生成 DSL → lint → 截图核验 → 修改」循环；lint 对 absolute 容器常误报，以截图实况为准。
3. 每页截图必查溢出/重叠（多列卡片、长文本是最高频问题）。
4. 素材：AI 生成图裁底部 6-7% 水印；照片压 1400px JPEG q86 再引用；引用扩展名以 ls 实际为准。
5. 只有 Word 教案时：提炼每页要点后从零构建整套视觉（含 AI 插画）。
6. 旧 `.ppt` 先 `soffice --headless --convert-to pptx` 转格式。

有 PPT 引擎（如 slidep）用 `create / upsert-dsl --dsl-file --page-index(0-based) / lint / screenshot --page-index --out` 命令循环；无引擎时用 python-pptx 直接构建。

## 工作流 B：动画视频合成（PPT → MP4）

一条命令，对任意 16:9 pptx 通用：

```bash
python3 scripts/make_video.py <课件.pptx> <工作目录> [输出.mp4]
```

内部三步（参数与原理见 [references/video-pipeline.md](references/video-pipeline.md)）：

1. **make_variants** — 每页形状按空间行序编排出场，展开为累积快照文稿 variants.pptx
2. **render** — fix_fonts 字体修复 + fontconfig + LibreOffice 转 PDF + 渲染 1920x1080 快照
3. **compose** — Remotion spring 弹簧动效（文字上浮淡入、图片淡入、页间 800ms 交叉淡化）逐帧合成 1080p25 mp4

批量处理：

```bash
for f in 源目录/*.pptx; do
  name=$(basename "$f" .pptx)
  python3 scripts/make_video.py "$f" "work/$name" "输出/$name.mp4"
done
```

## 建议流程

先交付 PPT 让用户确认 → 确认后再跑视频管线（视频耗时数分钟/份，避免返工）。视频输出按用户指定目录存放；未指定时放在 PPT 同级的「PPT视频」子文件夹。

## 另一条流程：透明卡片动画

需要「把课件拆成叠加在实拍画面上的透明文字卡」而不是整页 PPT 视频时，用同级目录
[card-animation/SKILL.md](card-animation/SKILL.md)：米白圆角卡片逐张滑入、元素依次上浮，
输出带 alpha 的 ProRes 4444（1920x1080@25fps），可直接叠到剪映/PR 时间线上。

选型：整页讲解视频 → 工作流 A+B；短视频/口播画面的字卡叠加 → `card-animation/`。

## 踩坑速查

| 现象 | 原因/修复 |
|---|---|
| 视频快照文字空心方块 | 缺字体：管线已内置 fix_fonts + fontconfig；自定义字体替换改 `fix_fonts(workdir, repl=...)` |
| soffice 转 PDF 失败/超时 | PPT 媒体过大：先压缩照片再重试 |
| python-pptx 打不开 | 旧 .ppt：先转 pptx |
| 节奏太快/太慢 | 调 `STEP`（元素间隔 ms）、`HOLD`（页停留 ms）、`XFADE`（页切换 ms） |
| macOS 批量改文件内容 | 用 Python `open().read().replace()`，不要用 `sed -i`（中文路径不可靠） |
