#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把快照按动画时间轴合成 1080p 25fps 无声视频（剪映/Remotion 风格出场）：
   文字/卡片上浮 30px + 淡入（easeOutCubic），图片纯淡入，页间交叉淡化。
   用法: python3 compose_video.py 输出.mp4
"""
import json
import subprocess
import sys
import numpy as np
from PIL import Image

FPS = 25
W, H = 1920, 1080
HOLD = 2600          # 每页动画播完后的停留 ms
XFADE = 800          # 页间交叉淡化 ms
RISE = 36            # 文字上浮距离 px

# ---- Remotion spring() 同款物理参数（remotion.dev/docs/spring）----
# mass=1, stiffness=100, damping=13（默认10偏弹，13 更自然，阻尼比 ζ≈0.65）
SPRING_K, SPRING_C, SPRING_M = 100.0, 13.0, 1.0
_OMEGA_N = (SPRING_K / SPRING_M) ** 0.5
_ZETA = SPRING_C / (2.0 * (SPRING_K * SPRING_M) ** 0.5)
_OMEGA_D = _OMEGA_N * (1.0 - _ZETA * _ZETA) ** 0.5


def spring(t):
    """欠阻尼弹簧从 0 到 1 的闭合解（初速度 0），允许轻微过冲后回落"""
    if t <= 0:
        return 0.0
    decay = np.exp(-_ZETA * _OMEGA_N * t)
    return 1.0 - decay * (np.cos(_OMEGA_D * t)
                          + (_ZETA * _OMEGA_N / _OMEGA_D) * np.sin(_OMEGA_D * t))


def load(path):
    return np.asarray(Image.open(path).convert('RGB')).astype(np.float32)


def main():
    timeline = json.load(open('timeline.json'))
    timeline = {int(k): v for k, v in timeline.items()}
    shapes = json.load(open('shapes.json'))
    meta = json.load(open('meta.json'))
    n_orig = meta['n_orig']

    offs = {}
    cur = n_orig
    for p in sorted(timeline):
        offs[p] = cur
        cur += len(timeline[p])

    dur = {p: max(e['delay'] + e['dur'] for e in timeline[p]) / 1000.0 + HOLD / 1000.0
           for p in timeline}
    total = sum(dur.values()) - XFADE / 1000.0 * (len(dur) - 1)
    nframes = int(round(total * FPS))
    print('total %.1fs, %d frames @%dfps' % (total, nframes, FPS))

    ff = subprocess.Popen(
        ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
         '-s', '%dx%d' % (W, H), '-framerate', str(FPS), '-i', '-',
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
         '-pix_fmt', 'yuv420p', '-movflags', '+faststart', sys.argv[1]],
        stdin=subprocess.PIPE)

    pages = sorted(timeline)
    starts = {}
    t0 = 0.0
    for p in pages:
        starts[p] = t0
        t0 += dur[p] - XFADE / 1000.0

    cache = {}

    def snaps(p):
        if p not in cache:
            lst = [load('snaps/n%03d.png' % p)]
            for k in range(len(timeline[p])):
                lst.append(load('snaps/n%03d.png' % (offs[p] + k + 1)))
            cache.clear()
            cache[p] = lst
        return cache[p]

    def render(p, t):
        evs = timeline[p]
        n = len(evs)
        shp = shapes[str(p)]
        sn = snaps(p)
        frame = sn[1].copy()
        for k, e in enumerate(evs):
            before = sn[k + 1]
            after = sn[0] if k == n - 1 else sn[k + 2]
            s, d = e['delay'] / 1000.0, e['dur'] / 1000.0
            if t >= s + d:
                frame = after.copy()
                continue
            if t <= s:
                break
            delta = after - before
            info = shp.get(str(e['id']), {})
            bb = info.get('bbox', [0, 0, W, H])
            x0 = max(0, int(bb[0]) - 4)
            y0 = max(0, int(bb[1]) - 4)
            x1 = min(W, int(bb[0] + bb[2]) + 4)
            y1 = min(H, int(bb[1] + bb[3]) + 4)
            pc = spring((t - s))
            alpha = min(1.0, max(0.0, pc))       # 透明度封顶在 1，过冲只作用于位移
            if info.get('pic'):
                frame += delta * alpha
            else:
                ry0 = max(0, y0 - RISE - 2)
                y1e = min(H, y1 + 2)
                d2 = delta[ry0:y1e, x0:x1]
                dy = int(round((1 - pc) * RISE))  # 过冲时为负 -> 越过终点再回落
                dz = np.zeros_like(d2)
                if dy > 0:
                    dz[dy:, :] = d2[:-dy, :]
                elif dy < 0:
                    dz[:dy, :] = d2[-dy:, :]
                else:
                    dz = d2
                frame[ry0:y1e, x0:x1] += dz * alpha
        return np.clip(frame, 0, 255).astype(np.uint8)

    for f in range(nframes):
        T = f / FPS
        p_cur = pages[0]
        for p in pages:
            if T >= starts[p]:
                p_cur = p
        t_local = T - starts[p_cur]
        img = render(p_cur, min(t_local, dur[p_cur])).astype(np.float32)

        nxt_i = pages.index(p_cur) + 1
        if nxt_i < len(pages):
            tail = dur[p_cur] - t_local
            if tail < XFADE / 1000.0:
                img2 = render(pages[nxt_i], 0).astype(np.float32)
                a = 1 - (tail / (XFADE / 1000.0)) ** 3
                img = img * (1 - a) + img2 * a

        if T < 0.6:
            img = img * (T / 0.6)
        elif T > total - 0.8:
            img = img * max(0.0, (total - T) / 0.8)

        ff.stdin.write(img.astype(np.uint8).tobytes())
        if f % 250 == 0:
            print('frame %d/%d' % (f, nframes), flush=True)

    ff.stdin.close()
    ff.wait()
    print('exit', ff.returncode)


if __name__ == '__main__':
    main()
