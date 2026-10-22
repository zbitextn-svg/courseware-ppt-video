# 课件动画视频管线技术文档

本文档描述 `scripts/make_video.py` + `scripts/compose_video.py` 的实现原理、参数与已知坑，供维护和调参时参考。

## 目录
1. [依赖](#依赖)
2. [管线流程](#管线流程)
3. [参数调优](#参数调优)
4. [已知坑与修复](#已知坑与修复)

## 依赖

```
python-pptx  lxml  pymupdf  pillow  numpy
soffice (LibreOffice)  ffmpeg
```

安装：`pip install -r scripts/requirements.txt`（macOS: `brew install --cask libreoffice ffmpeg`）

## 管线流程

### 1. make_variants（make_video.py）
- 用 python-pptx 打开源课件，逐页读取形状的 bbox 和类型（图片/文字）。
- **静态背景判定**：全出血底图（w≥1260 且 h≥700）或整高侧板（h≥700 且贴顶/贴底）不参与动画。
- **出场排序**：按空间行序 `sort key = (round(y/40), x)`，自上而下、同行自左向右。
- 展开为**累积快照文稿** variants.pptx：第 k 个快照隐藏第 k 项之后的所有元素。快照页通过 deepcopy spTree + 重新 relate 图片关系复制生成。

### 2. fix_fonts + render_snaps（make_video.py）
- fix_fonts：zip 内逐 XML 替换缺失字体（默认 `Microsoft YaHei → PingFang SC`）。不替换则渲染出**空心方块**。
- 渲染前必须设置 `FONTCONFIG_FILE` 指向生成的 fontconfig（索引 /System/Library/Fonts、/Library/Fonts、~/Library/Fonts + 字体族替换）。无 fontconfig 时 LibreOffice 找不到中文字体，同样渲染为方块。
- soffice 无头转 PDF → pymupdf 2.0x 缩放逐页渲 PNG → 归一 1920x1080。

### 3. compose（compose_video.py）
- 文字/卡片：上浮 36px + 淡入，**Remotion spring 物理曲线**（mass=1, stiffness=100, damping=13，欠阻尼轻微过冲）。
- 图片：纯淡入。透明度封顶 1.0，过冲只作用于位移。
- 页间交叉淡化 800ms，头部 0.6s 淡入、尾部 0.8s 淡出。
- 逐帧 numpy 合成 → 管道喂 ffmpeg rawvideo → libx264 CRF18 → 1080p25 无声 mp4。

## 参数调优

| 参数 | 位置 | 默认 | 说明 |
|---|---|---|---|
| `DPI_SCALE` | make_video.py | 1.5 | 逻辑 96dpi → 1920x1080 |
| `STEP` | make_video.py | 150ms | 同页元素出场间隔（放慢改 200+） |
| `T0` | make_video.py | 250ms | 首元素延迟 |
| `DUR_TXT / DUR_PIC` | make_video.py | 480/620ms | 文字/图片单元素动画时长 |
| `HOLD` | compose_video.py | 2600ms | 每页动画播完后停留 |
| `XFADE` | compose_video.py | 800ms | 页间交叉淡化 |
| `RISE` | compose_video.py | 36px | 文字上浮距离 |
| `SPRING_K/C/M` | compose_video.py | 100/13/1 | 弹簧物理参数（damping 10 更弹、16 更稳） |
| `zoom` | render_snaps | 2.0 | PDF 渲染倍率 |

## 已知坑与修复

| 坑 | 现象 | 修复 |
|---|---|---|
| 缺字体 + 无 fontconfig | 快照文字全是空心方块 | fix_fonts 替换 + FONTCONFIG_FILE 环境 |
| 大文件 PPT | soffice 转 PDF 超时/失败 | 先压缩媒体（照片压 1400px JPEG q86 可从 127MB→3.9MB） |
| 合成脚本相对路径 | cwd 在课程目录时找不到 snaps | 输出文件名不要带目录前缀，脚本内 os.chdir(workdir) |
| 旧 .ppt 格式 | python-pptx 打不开 | 先 `soffice --headless --convert-to pptx` 转格式 |
| 深色背景页 | 淡入时底色闪黑 | 静态背景判定已覆盖全出血底图；特殊布局手动调 static 阈值 |
