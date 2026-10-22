# -*- coding: utf-8 -*-
"""成片校验 + 叠底预览

用法:
    python qa_cards.py out/cards.mov                 # 抽帧拼校验图
    python qa_cards.py out/cards.mov --flat          # 另出米色底 H.264 预览 mp4
    python qa_cards.py out/cards.mov --dur 51.2 --flat

抽帧规则（重要）：每张卡抽「卡内 2.2s」的帧，不要抽 卡号 × 卡时长，
那是新卡第一帧（opacity=0 全透明），会误判成空白。

产物:
    qa_<name>.jpg      校验图
    <name>_preview.mp4 叠底预览（加 --flat）
"""
import os
import json
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import find_ffmpeg  # noqa
from PIL import Image

FPS = 25


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    mov = os.path.abspath(sys.argv[1])
    work = os.path.dirname(mov)
    name = os.path.splitext(os.path.basename(mov))[0]

    # 卡片数/时长：优先读 render_cards.py 留下的 meta
    ff = find_ffmpeg()
    meta_p = os.path.splitext(mov)[0] + ".meta.json"
    if os.path.exists(meta_p):
        meta = json.load(open(meta_p, encoding="utf-8"))
        n, durs = meta["n"], meta["durs"]
        fps = meta.get("fps", FPS)
        dur = sum(durs) / 1000.0
        frames = [int(round(sum(durs[:i]) / 1000.0 * fps + min(2.2, durs[i] / 1000 - 1.2) * fps))
                  for i in range(n)]
    else:
        if "--dur" in sys.argv:
            dur = float(sys.argv[sys.argv.index("--dur") + 1])
        else:
            r = subprocess.run([os.environ.get("FFPROBE") or "ffprobe", "-v", "error",
                                "-show_entries", "format=duration",
                                "-of", "csv=p=0", mov], capture_output=True, text=True)
            dur = float(r.stdout.strip())
        fps = FPS
        n = max(1, int(round((dur - 6.2) / 5.0)) + 1)
        frames = [i * 5 * fps + int(2.2 * fps) for i in range(n)]

    qa_dir = os.path.join(work, "qa_" + name)
    os.makedirs(qa_dir, exist_ok=True)

    files = []
    for i in range(n):
        frame = frames[i]
        p = os.path.join(qa_dir, f"c{i + 1:02d}.png")
        subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error",
                        "-i", mov, "-vf", f"select='eq(n\\,{frame})'",
                        "-fps_mode", "passthrough", "-frames:v", "1", p],
                       check=True)
        files.append(p)

    cols, tw, th = 4, 480, 270
    rows = (n + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols + 10 * (cols + 1),
                              th * rows + 10 * (rows + 1)), "#DED6C6")
    empty = 0
    for i, p in enumerate(files):
        im = Image.open(p).convert("RGBA")
        if im.split()[-1].getbbox() is None:
            empty += 1
            print("⚠ 空白帧:", p)
        im = im.resize((tw, th), Image.LANCZOS)
        bg = Image.new("RGBA", (tw, th), "#F1ECE0")
        bg.alpha_composite(im)
        r, c = divmod(i, cols)
        sheet.paste(bg.convert("RGB"), (10 + c * (tw + 10), 10 + r * (th + 10)))
    q = os.path.join(work, "qa_" + name + ".jpg")
    sheet.save(q, quality=90)
    print(f"校验图: {q}  （{n} 张卡，空白 {empty}）")

    if "--flat" in sys.argv:
        pv = os.path.join(work, name + "_preview.mp4")
        subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error",
                        "-f", "lavfi", "-i", f"color=c=0xEFE6D6:s=1920x1080:r={FPS}",
                        "-i", mov, "-filter_complex",
                        "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p",
                        "-t", f"{dur:.2f}", "-c:v", "libx264", "-crf", "20",
                        "-preset", "medium", "-movflags", "+faststart", pv],
                       check=True)
        print("叠底预览:", pv, "%.1f MB" % (os.path.getsize(pv) / 1048576))


if __name__ == "__main__":
    main()
