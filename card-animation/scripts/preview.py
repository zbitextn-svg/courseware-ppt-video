# -*- coding: utf-8 -*-
"""版式校对：把每张卡截成静止帧，拼一张总览图，肉眼一次看完所有版式。

用法:
    python preview.py cards.html
    python preview.py cards.html --t 3600 --port 9670

产物:
    stills_<base>/c01.png …
    ov_<base>.jpg        总览（4 列）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import CDP, W, H, open_page  # noqa
from PIL import Image


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    html = os.path.abspath(sys.argv[1])
    t = 3600
    port = 9670
    if "--t" in sys.argv:
        t = int(sys.argv[sys.argv.index("--t") + 1])
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])

    work = os.path.dirname(html)
    base = os.path.splitext(os.path.basename(html))[0]
    outdir = os.path.join(work, "stills_" + base)
    if os.path.isdir(outdir):
        for f in os.listdir(outdir):
            os.remove(os.path.join(outdir, f))
    else:
        os.makedirs(outdir)

    cdp = CDP(port=port)
    cdp.start(os.path.join(work, "_pvprof_" + base))
    meta = open_page(cdp, html)
    n = meta["n"]
    print("卡片数", n)

    files = []
    for i in range(n):
        cdp.eval_wait(f"window.__render({i}, {t});"
                      "new Promise(r=>requestAnimationFrame("
                      "()=>requestAnimationFrame(()=>r(1))))")
        p = os.path.join(outdir, f"c{i + 1:02d}.png")
        open(p, "wb").write(cdp.shot())
        files.append(p)
    cdp.close()

    cols, tw, th = 4, 480, 270
    rows = (n + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols + 10 * (cols + 1),
                              th * rows + 10 * (rows + 1)), "#DED6C6")
    for i, p in enumerate(files):
        im = Image.open(p).convert("RGBA").resize((tw, th), Image.LANCZOS)
        bg = Image.new("RGBA", (tw, th), "#F3EDE1")
        bg.alpha_composite(im)
        r, c = divmod(i, cols)
        sheet.paste(bg.convert("RGB"), (10 + c * (tw + 10), 10 + r * (th + 10)))
    q = os.path.join(work, "ov_" + base + ".jpg")
    sheet.save(q, quality=90)
    print("总览:", q)


if __name__ == "__main__":
    main()
