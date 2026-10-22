#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用课件动画视频管线（由小动物补墙洞管线参数化而来）：
   用法: python3 make_video.py <课程.pptx> <工作目录> [输出.mp4]
   步骤:
     1. make_variants —— 每页形状按空间行序出场编排，展开成累积快照文稿 variants.pptx
     2. render snaps —— soffice 转 pdf → pymupdf 逐页渲染 1920x1080 快照
     3. compose —— spring 弹簧动效逐帧合成 1080p25 无声视频
"""
import json
import os
import subprocess
import sys
from copy import deepcopy

from lxml import etree
from pptx import Presentation

SKIP_TAGS = ('nvGrpSpPr', 'grpSpPr')
DPI_SCALE = 1.5          # 1280x720 逻辑像素 -> 1920x1080
STEP = 150               # 元素间隔 ms（v2 放慢节奏）
T0 = 250                 # 首元素延迟 ms
DUR_TXT, DUR_PIC = 480, 620


# ---------------- 1. make_variants ----------------

def shape_id_of(el):
    for e in el.iter():
        if etree.QName(e).localname == 'cNvPr':
            return int(e.get('id'))
    return None


def copy_slide(prs, src_slide):
    var = prs.slides.add_slide(src_slide.slide_layout)
    dst_tree = var.shapes._spTree
    for el in list(dst_tree):
        if etree.QName(el).localname not in SKIP_TAGS:
            dst_tree.remove(el)
    rid_map = {}
    A = '{http://schemas.openxmlformats.org/drawingml/2006/main}blip'
    R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed'
    for child in src_slide.shapes._spTree:
        tag = etree.QName(child).localname
        if tag in SKIP_TAGS:
            continue
        dup = deepcopy(child)
        for blip in dup.iter(A):
            old = blip.get(R)
            if old is None:
                continue
            if old not in rid_map:
                rel = src_slide.part.rels[old]
                rid_map[old] = var.part.relate_to(rel.target_part, rel.reltype)
            blip.set(R, rid_map[old])
        dst_tree.append(dup)
    return var


def hide_ids(slide, ids):
    tree = slide.shapes._spTree
    for el in list(tree):
        if etree.QName(el).localname in SKIP_TAGS:
            continue
        if shape_id_of(el) in ids:
            tree.remove(el)


def make_variants(src, workdir):
    os.makedirs(workdir, exist_ok=True)
    prs = Presentation(src)
    timeline, shapes, snap_pages = {}, {}, []
    for idx, slide in enumerate(prs.slides, 1):
        infos, evs = {}, []
        for sh in slide.shapes:
            try:
                x, y = sh.left / 914400 * 96, sh.top / 914400 * 96
                w, h = sh.width / 914400 * 96, sh.height / 914400 * 96
            except Exception:
                continue
            pic = str(sh.shape_type).startswith('PICTURE')
            infos[int(sh.shape_id)] = {
                'bbox': [round(x * DPI_SCALE), round(y * DPI_SCALE),
                         round(w * DPI_SCALE), round(h * DPI_SCALE)],
                'pic': pic, 'name': sh.name}
            # 全出血底/整高侧板视为静态背景，不参与动画
            static = (w >= 1260 and h >= 700) or (h >= 700 and (y <= 4 or y + h >= 716))
            if static:
                continue
            evs.append({'id': int(sh.shape_id), 'x': x, 'y': y, 'pic': pic})
        evs.sort(key=lambda e: (round(e['y'] / 40), e['x']))
        items = [{'id': e['id'], 'kind': 'fade',
                  'delay': T0 + i * STEP,
                  'dur': DUR_PIC if e['pic'] else DUR_TXT}
                 for i, e in enumerate(evs)]
        timeline[idx] = items
        shapes[str(idx)] = infos
        for k, ev in enumerate(items):
            snap_pages.append((idx, k, {e['id'] for e in items[k + 1:]}))
        print('page %02d: %d events' % (idx, len(items)), flush=True)

    n_orig = len(prs.slides._sldIdLst)
    total = 0
    for (pg, k, hide) in snap_pages:
        src_slide = prs.slides[pg - 1]
        var = copy_slide(prs, src_slide)
        hide_ids(var, hide)
        total += 1
    json.dump(timeline, open(os.path.join(workdir, 'timeline.json'), 'w'))
    json.dump(shapes, open(os.path.join(workdir, 'shapes.json'), 'w'))
    json.dump({'n_orig': n_orig, 'n_snaps': total},
              open(os.path.join(workdir, 'meta.json'), 'w'))
    prs.save(os.path.join(workdir, 'variants.pptx'))
    print('variants.pptx: %d orig + %d snapshots' % (n_orig, total), flush=True)


# ---------------- 2. render snaps ----------------

def fix_fonts(workdir, repl=(('Microsoft YaHei', 'PingFang SC'),)):
    """隔离副本内替换缺失字体（本机无雅黑常规体，文字会变空心方块）"""
    import shutil
    import zipfile
    src_pptx = os.path.join(workdir, 'variants.pptx')
    tmp = src_pptx + '.tmp'
    with zipfile.ZipFile(src_pptx) as zin, \
         zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.endswith('.xml'):
                text = data.decode('utf-8')
                for a, b in repl:
                    text = text.replace(a, b)
                data = text.encode('utf-8')
            zout.writestr(item, data)
    shutil.move(tmp, src_pptx)
    print('fonts fixed:', ', '.join(a + '->' + b for a, b in repl), flush=True)


FONT_CONF = '/tmp/fonts_0918.conf'


def ensure_fontconf(sub='PingFang SC'):
    """LibreOffice 在无 FONTCONFIG_FILE 时找不到中文字体（文字渲染为空心方块）。
       写一份 fontconfig：索引系统/用户字体目录 + 缺失字体族替换。"""
    conf = f'''<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <dir>/System/Library/Fonts</dir>
  <dir>/System/Library/AssetsV2</dir>
  <dir>/Library/Fonts</dir>
  <dir>/Users/frey/Library/Fonts</dir>
  <cachedir>/tmp/fc-cache-0918</cachedir>
  <match target="pattern">
    <test qual="any" name="family"><string>Microsoft YaHei</string></test>
    <edit name="family" mode="assign" binding="same"><string>{sub}</string></edit>
  </match>
</fontconfig>
'''
    with open(FONT_CONF, 'w') as f:
        f.write(conf)
    return FONT_CONF


def render_snaps(workdir):
    var = os.path.join(workdir, 'variants.pptx')
    env = dict(os.environ, FONTCONFIG_FILE=ensure_fontconf())
    subprocess.run(['soffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', workdir, var],
                   check=True, capture_output=True, timeout=600, env=env)
    pdf = var.replace('.pptx', '.pdf')
    import fitz
    doc = fitz.open(pdf)
    os.makedirs(os.path.join(workdir, 'snaps'), exist_ok=True)
    zoom = 2.0   # 96dpi * 2 = 144dpi -> ~1920x1080
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        img = pix.tobytes('png')
        open(os.path.join(workdir, 'snaps', 'n%03d.png' % i), 'wb').write(img)
    print('rendered %d snapshot pages' % len(doc), flush=True)
    doc.close()
    # 尺寸归一到 1920x1080
    from PIL import Image
    d = os.path.join(workdir, 'snaps')
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        im = Image.open(p)
        if im.size != (1920, 1080):
            im = im.resize((1920, 1080), Image.LANCZOS)
            im.save(p)
    print('normalized to 1920x1080', flush=True)


# ---------------- 3. compose ----------------

def compose(workdir, out):
    os.chdir(workdir)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    # 直接复用补墙洞验证过的合成脚本（同目录随管线分发）
    code = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'compose_video.py'), encoding='utf-8').read()
    g = {'__name__': '__main__'}
    sys.argv = ['compose_video.py', out]
    exec(compile(code, 'compose_video.py', 'exec'), g)


def main():
    src, workdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    out = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else \
        os.path.join(workdir, 'out.mp4')
    os.makedirs(workdir, exist_ok=True)
    prev = os.getcwd()
    make_variants(src, workdir)
    fix_fonts(workdir)
    render_snaps(workdir)
    os.chdir(prev)
    compose(workdir, out)
    print('DONE:', out, flush=True)


if __name__ == '__main__':
    main()
