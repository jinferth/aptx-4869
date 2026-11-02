# -*- coding: utf-8 -*-
"""v5.11 文件夹监听验收。

分成两段：
1. 确定性部分——直接驱动扫描逻辑，验证"半写入不处理 / 写完才处理 / 不自噬 / 不重复"。
   静置规则依赖墙钟（轮询 1.2 秒 + 静置 2 秒），这里把 pending 里的首见时间往前拨，
   断言就不受机器快慢影响。
2. 端到端部分——真的开监听、真落文件，确认后台轮询到主线程的链路通。
"""
import os
import sys
import time
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import check, report

PROJ = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, PROJ)

from PIL import Image
import image_processor_pro as mod

TMP = os.path.join(os.environ.get("TEMP", "."), "aptx_v61_test")
WATCH = os.path.join(TMP, "watch")
OUT = os.path.join(WATCH, "resolved_cases")


class FakeMB:
    popups = 0

    def showinfo(self, *a, **k):
        FakeMB.popups += 1

    def showwarning(self, *a, **k):
        pass

    def showerror(self, *a, **k):
        pass

    def askyesno(self, *a, **k):
        return True


def pump(root, seconds):
    end = time.time() + seconds
    while time.time() < end:
        root.update()
        time.sleep(0.03)


def wait_for(root, cond, timeout=40.0):
    """等条件成立，而不是死等固定秒数。"""
    end = time.time() + timeout
    while time.time() < end:
        root.update()
        time.sleep(0.03)
        if cond():
            return True
    root.update()
    return False


def make_image(path, size=(600, 400), color=(120, 80, 40)):
    Image.new("RGB", size, color).save(path, quality=90)


def backdate(app, path, seconds):
    """把某文件的首见时间往前拨，模拟"已经静置了足够久"。"""
    if path in app._pending_watch:
        size, mtime, first = app._pending_watch[path]
        app._pending_watch[path] = (size, mtime, first - seconds)


def main():
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(WATCH)
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)
    mod.messagebox = FakeMB()
    mod.enable_dpi_awareness()
    root = mod.create_root()
    root.withdraw()   # 测试不显示窗口，避免干扰桌面
    app = mod.ImageProcessorPro(root)
    root.update()

    app._watch_dir = WATCH
    app.target_format.set("JPG")

    # ================= 1. 静置逻辑（确定性） =================
    print("== 1. 静置规则：写完才处理 ==")
    target = os.path.join(WATCH, "slow.jpg")
    src = os.path.join(WATCH, "a.jpg")
    make_image(src)
    data = open(src, "rb").read()
    half = len(data) // 2
    with open(target, "wb") as fp:
        fp.write(data[:half])
        fp.flush()

    got = app._scan_watch_dir()
    check("半写入的文件不被认走", target not in got)

    # 补齐文件：大小与 mtime 都变了，按"首次见到"重新计时
    with open(target, "ab") as fp:
        fp.write(data[half:])
    got = app._scan_watch_dir()
    check("文件刚写完还不算稳定", target not in got)
    backdate(app, target, mod.WATCH_SETTLE_SECONDS + 1)
    got = app._scan_watch_dir()
    check("写完并静置够久后才被认走", target in got)
    check("认走后不再重复", target not in app._scan_watch_dir())

    print("== 2. 排除输出目录（不自噬） ==")
    os.makedirs(OUT, exist_ok=True)
    Image.new("RGB", (300, 200), (10, 200, 30)).save(os.path.join(OUT, "produced.jpg"))
    app._watch_exclude = os.path.abspath(OUT)
    app._seen_watch.clear()
    app._pending_watch.clear()
    got = app._scan_watch_dir()
    check("产物不会被当成新文件", not any(p.startswith(OUT) for p in got))
    app._watch_exclude = ""

    print("== 3. 目录被记住 ==")
    app._save_settings()
    saved = mod.load_settings()
    check("settings.watch_dir 记住了目录", saved["watch_dir"] == WATCH)

    # ================= 4. 端到端：后台轮询真的能投递 =================
    print("== 4. 端到端：开启监听后新文件自动处理 ==")
    app._seen_watch.clear()
    app._pending_watch.clear()
    app._toggle_watch()
    root.update()
    check("按钮切成停止监听", app.btn_watch.cget("text") == "停止监听")

    e2e = os.path.join(WATCH, "e2e.jpg")
    make_image(e2e, color=(30, 160, 60))
    arrived = wait_for(root, lambda: e2e in app.source_files)
    check("后台轮询把新文件送进了清单", arrived)
    done = wait_for(root, lambda: app.status.get(e2e) == 2) if arrived else False
    check("新文件被处理完成", done)
    check("监听模式不弹框", FakeMB.popups == 0)
    check("产物已落盘", os.path.isfile(os.path.join(OUT, "e2e.jpg")))

    print("== 5. 停止监听后不再接收 ==")
    app._toggle_watch()
    root.update()
    check("按钮切回开启监听", app.btn_watch.cget("text") == "开启监听")
    late = os.path.join(WATCH, "late.jpg")
    make_image(late, color=(60, 60, 60))
    pump(root, 4)
    check("停止后新文件未被加入", late not in app.source_files)

    app._on_close()
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)
    print("测试配置已清理")


if __name__ == "__main__":
    main()
    sys.exit(report())
