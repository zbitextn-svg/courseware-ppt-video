# 踩坑清单

出问题先在这里找。每条都是实际跑坏过的。

## 渲染与浏览器

**无头 Chrome 反复崩溃（Trace/BPT trap）**
必须带：`--headless=new --no-sandbox --disable-gpu-sandbox --disable-dev-shm-usage --disable-gpu`。
少一个都可能崩。`cdp.py` 里已经写死。

**后台任务里渲染必被拦**
渲染是长任务，但**不能**用 `run_in_background` 或 `nohup &`——沙箱会在子进程启动时把它杀掉。
必须前台执行并给足 timeout（一套 12 张卡约 4–6 分钟）。

**每页启动一次 Chrome 会崩**
改成单实例 + 逐卡导航驱动（`cdp.py` 的 CDP 类），一次开台、多次截图。

**截图拿到白底 / 黑底**
必须 `Emulation.setDefaultBackgroundColorOverride{color:{r:0,g:0,b:0,a:0}}`，
否则 mock 背景不透明，ProRes 的 alpha 通道全 255。

**截图拿到上一帧**
`window.__render(i,t)` 之后要等两帧合成：`awaitPromise` 里包
`requestAnimationFrame(()=>requestAnimationFrame(...))`。少这步动画会错位一格。

**中文字体没生效**
字体以 woff2 子集内嵌，`font-display: block` 会先隐形；开页后要 `sleep 0.6–0.8s` 再截图，
否则第一张卡是空白或默认字体。

## 版式

**居中卡偏左/偏右**
不要用 `margin-left:-w/2` 硬算宽度。用 `left:0;right:0;margin:0 auto;width:fit-content`。
代价是子容器要显式 `width:100%`，否则会缩成一团。

**卡片不垂直居中**
切卡时 `display` 必须设成 `flex`，写 `block` 会丢掉 `.card` 上的 flex 居中。

**卡片内容顶到上边**
`.card` 的高度要撑满 1080 并 `flex-direction: column; justify-content: center`。

**底部注脚溢出卡片**
`.qsrc` 是 `nowrap`，超长直接跑到卡外。控制字数，或改 `white-space: normal` 但会增加卡高。

## 内容

**`compare` 报解包错误**
`left` / `right` 必须是 `(标题, [要点...])` **二元组**。写成三元组（多塞一个颜色）会
`too many values to unpack`。颜色用 `left_tone` / `right_tone`。

**`√` `✗` 显示成方框**
字体子集里没有这些符号，跨机器 fallback 不一致。改写成「能转 / 不能转」这类文字。

**emoji 显示忽大忽小**
走系统彩色 emoji 字体，渲染尺寸不可控，且部分环境不显示。卡片里一律不用。

**生僻字变豆腐块**
`all_text()` 只收集 `CARDS` 里的字符串。若在 `kit.py` 的 CSS/模板里写了中文（比如固定文案），
它不会被收进子集，要手动加到 `all_text` 的保底字符串里。

## ffmpeg

**`-vsync` 报错**
新版 ffmpeg 已移除，用 `-fps_mode passthrough`。

**`-alpha_bits 10` 报错**
只接受 `0 / 8 / 16`。要高质量透明就用 16（输出 `yuva444p12le`）。

**成片校验全黑/全透明**
抽帧位置算错了：`卡号 × 卡时长` 恰好是新卡的第一帧，此时 `opacity=0`。
要抽**卡内** 2.2s 处（`qa_cards.py` 已按 meta 计算）。
