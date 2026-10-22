# -*- coding: utf-8 -*-
"""无头 Chrome CDP 客户端：单实例截图，支持透明背景。

本机踩过的坑都固化在这里：
- 必须加 --no-sandbox / --disable-gpu-sandbox / --disable-dev-shm-usage，否则 headless 反复崩溃
- 截图前必须 setDefaultBackgroundColorOverride(a=0)，否则透明卡片会带白底
- 逐帧驱动要 eval + awaitPromise 等两帧合成，否则拿到上一帧
"""
import base64
import json
import os
import shutil
import subprocess
import time
import urllib.request

import websocket

W, H = 1920, 1080


def find_chrome():
    cands = [
        os.environ.get("CHROME_PATH"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chrome"),
    ]
    for c in cands:
        if c and os.path.exists(c):
            return c
    raise SystemExit("找不到 Chrome/Chromium，请设置环境变量 CHROME_PATH")


def find_ffmpeg():
    return os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"


class CDP:
    def __init__(self, port=9444):
        self.i = 0
        self.port = port
        self.proc = None
        self.ws = None

    def start(self, profile):
        shutil.rmtree(profile, ignore_errors=True)
        os.makedirs(profile, exist_ok=True)
        self.proc = subprocess.Popen(
            [find_chrome(), "--headless=new", "--no-sandbox",
             "--disable-gpu-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
             "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
             "--mute-audio", "--force-device-scale-factor=1",
             f"--window-size={W},{H}",
             f"--user-data-dir={profile}",
             f"--remote-debugging-port={self.port}",
             "--remote-allow-origins=*",
             "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        url = None
        for _ in range(100):
            try:
                with urllib.request.urlopen(
                        f"http://127.0.0.1:{self.port}/json/list", timeout=1) as r:
                    tabs = json.loads(r.read())
                pages = [t for t in tabs if t.get("type") == "page"]
                if pages:
                    url = pages[0]["webSocketDebuggerUrl"]
                    break
            except Exception:
                pass
            time.sleep(0.15)
        if not url:
            raise SystemExit("Chrome 调试端口未就绪")
        self.ws = websocket.create_connection(url, timeout=120,
                                              max_size=64 * 1024 * 1024)

    def send(self, method, **params):
        self.i += 1
        self.ws.send(json.dumps({"id": self.i, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.i:
                if "error" in msg:
                    raise RuntimeError(method + " -> " +
                                       json.dumps(msg["error"], ensure_ascii=False))
                return msg.get("result", {})

    def eval(self, expr):
        r = self.send("Runtime.evaluate", expression=expr,
                      returnByValue=True, awaitPromise=False)
        return r.get("result", {}).get("value")

    def eval_wait(self, expr):
        """执行并等待 Promise（内部等两帧合成），保证截图拿到最新状态"""
        r = self.send("Runtime.evaluate", expression=expr,
                      returnByValue=True, awaitPromise=True)
        return r.get("result", {}).get("value")

    def shot(self):
        r = self.send("Page.captureScreenshot", format="png",
                      fromSurface=True, captureBeyondViewport=False)
        return base64.b64decode(r["data"])

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass
        if self.proc:
            self.proc.terminate()


def open_page(cdp, html, wait=0.8):
    """打开页面、设置透明背景、等待字体加载完成"""
    cdp.send("Page.enable")
    cdp.send("Runtime.enable")
    cdp.send("Emulation.setDeviceMetricsOverride", width=W, height=H,
             deviceScaleFactor=1, mobile=False)
    cdp.send("Emulation.setDefaultBackgroundColorOverride",
             color={"r": 0, "g": 0, "b": 0, "a": 0})
    cdp.send("Page.navigate", url="file://" + os.path.abspath(html))
    for _ in range(150):
        if cdp.eval("document.readyState") == "complete":
            break
        time.sleep(0.1)
    time.sleep(wait)
    return json.loads(cdp.eval("JSON.stringify(window.__meta)"))
