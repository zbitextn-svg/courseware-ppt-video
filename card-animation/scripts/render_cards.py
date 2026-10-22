# -*- coding: utf-8 -*-
"""逐帧渲染 HTML 卡片 → 透明 ProRes 4444 MOV（1920x1080, 25fps）

用法:
    python render_cards.py cards.html out/cards.mov
    python render_cards.py cards.html out/cards.mov --still-only   # 只出每张卡的静止 PNG
    python render_cards.py cards.html out/cards.mov --fps 30 --port 9455

产物:
    out/cards.mov          透明通道视频（yuva444p10le，alpha 16bit）
    stills/card_01.png …   每张卡的静止态 PNG（可直接做封面/暂停页）
    frames/f_00000.png …   中间帧序列（可删）

提速机制：静止段不逐帧截图，先用一张静止参考帧复用，只有入场/出场/动态卡逐帧渲染。
"""
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import CDP, W, H, find_ffmpeg, open_page  # noqa

GAP_FRAMES = 0  # 卡片之间留空帧数（一般不需要）


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    html = os.path.abspath(sys.argv[1])
    work = os.path.dirname(html)
    base = os.path.splitext(os.path.basename(html))[0]
    out = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("-") \
        else os.path.join(work, "out", base + ".mov")

    fps = 25
    port = 9444
    still_only = "--still-only" in sys.argv
    if "--fps" in sys.argv:
        fps = int(sys.argv[sys.argv.index("--fps") + 1])
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])

    frames_dir = os.path.join(work, "frames_" + base)
    stills_dir = os.path.join(work, "stills_" + base)
    shutil.rmtree(frames_dir, ignore_errors=True)
    os.makedirs(frames_dir, exist_ok=True)
    shutil.rmtree(stills_dir, ignore_errors=True)
    os.makedirs(stills_dir, exist_ok=True)

    cdp = CDP(port=port)
    cdp.start(os.path.join(work, "_cdpprof_" + base))
    meta = open_page(cdp, html)
    n = meta["n"]
    durs = meta.get("durs") or [meta["dur"]] * n
    inn, out_ms = meta["inn"], meta["out"]
    live = set(meta.get("live") or [])
    print(f"卡片 {n} 张 | 每张 {durs} ms | 入场 {inn} | 出场 {out_ms} | 动态卡 {sorted(live)}")

    # ---- 1) 每张卡的静止态 PNG
    for i in range(n):
        t_still = min(durs[i] * 0.34, 4200) if i in live else durs[i] - out_ms - 200
        cdp.eval(f"window.__render({i}, {t_still:.0f})")
        png = cdp.shot()
        open(os.path.join(stills_dir, f"card_{i + 1:02d}.png"), "wb").write(png)
        print(f"  静止卡 {i + 1:02d}  {len(png) // 1024} KB")

    if still_only:
        cdp.close()
        print("仅静止态完成 →", stills_dir)
        return

    # ---- 2) 逐帧渲染
    total = sum(int(round(d / 1000 * fps)) for d in durs) + GAP_FRAMES * (n - 1)
    print(f"总帧数 {total}，开始逐帧渲染…")
    idx = 0
    t0 = time.time()
    for i in range(n):
        dur = durs[i]
        card_frames = int(round(dur / 1000 * fps))
        cdp.eval(f"window.__render({i}, {inn + 200})")
        still_ref = cdp.shot()
        for f in range(card_frames):
            t = f * 1000.0 / fps
            if i not in live and inn + 60 <= t <= dur - out_ms - 60:
                png = still_ref
            else:
                cdp.eval_wait(
                    f"window.__render({i}, {t:.2f});"
                    "new Promise(r=>requestAnimationFrame("
                    "()=>requestAnimationFrame(()=>r(1))))")
                png = cdp.shot()
            open(os.path.join(frames_dir, f"f_{idx:05d}.png"), "wb").write(png)
            idx += 1
        if i < n - 1:
            idx += GAP_FRAMES
        print(f"  第 {i + 1}/{n} 张完成，累计 {idx} 帧，{time.time() - t0:.0f}s")

    cdp.close()

    # ---- 3) 合成带 alpha 的 ProRes 4444
    print("合成 ProRes 4444…")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run([find_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
                    "-framerate", str(fps),
                    "-i", os.path.join(frames_dir, "f_%05d.png"),
                    "-c:v", "prores_ks", "-profile:v", "4444",
                    "-pix_fmt", "yuva444p10le",
                    "-alpha_bits", "16", "-vendor", "apl0",
                    "-movflags", "+faststart", out], check=True)

    info = subprocess.run([os.environ.get("FFPROBE") or "ffprobe", "-v", "error",
                           "-select_streams", "v:0",
                           "-show_entries",
                           "stream=codec_name,profile,width,height,pix_fmt,r_frame_rate",
                           "-show_entries", "format=duration,size",
                           "-of", "json", out], capture_output=True, text=True)
    print(info.stdout)
    print("输出:", out, "%.1f MB" % (os.path.getsize(out) / 1048576))
    print("静止卡:", stills_dir)
    # 记下卡片数/时长，qa_cards.py 直接读取，不用猜
    with open(os.path.splitext(out)[0] + ".meta.json", "w", encoding="utf-8") as f:
        json.dump({"n": n, "durs": durs, "fps": fps}, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
