# -*- coding: utf-8 -*-
"""v5.7 目标体积压缩验收。"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import check, report
import csv
import time
import shutil

# 项目根 = tests/ 的上一级；不写死本机路径，换台机器直接能跑
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)

import tkinter as tk
from PIL import Image

import image_processor_pro as mod

TMP = os.path.join(os.environ.get("TEMP", "."), "aptx_v57_test")
SRC = os.path.join(TMP, "src")


class FakeMB:
    def showinfo(self, *a, **k):
        pass

    def showwarning(self, *a, **k):
        pass

    def showerror(self, *a, **k):
        pass


def build():
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(SRC)
    # 造几张体积差异很大的图：噪点图压不小，纯色图一压就小
    import random
    random.seed(7)
    noisy = Image.new("RGB", (1200, 800))
    px = noisy.load()
    for y in range(0, 800, 2):
        for x in range(0, 1200, 2):
            v = random.randint(0, 255)
            for dy in range(2):
                for dx in range(2):
                    px[x + dx, y + dy] = (v, (v * 3) % 256, (v * 7) % 256)
    noisy.save(os.path.join(SRC, "noisy.jpg"), quality=95)
    Image.new("RGB", (1200, 800), (30, 80, 120)).save(os.path.join(SRC, "flat.jpg"), quality=95)
    Image.new("RGB", (1600, 1200), (200, 200, 200)).save(os.path.join(SRC, "big_flat.jpg"), quality=95)


def run(app, root, timeout=120):
    app.start_thread()
    end = time.time() + timeout
    while app._running and time.time() < end:
        root.update()
        time.sleep(0.02)
    root.update()
    time.sleep(0.15)
    root.update()


def main():
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)
    build()
    mod.messagebox = FakeMB()
    mod.enable_dpi_awareness()

    root = mod.create_root()
    root.withdraw()   # 测试不显示窗口，避免干扰桌面
    app = mod.ImageProcessorPro(root)
    root.update()

    print("== 1. 格式联动 ==")
    for fmt in ("JPG", "WEBP", "PNG", "BMP", "ICO"):
        app.target_format.set(fmt)
        app._update_target_widgets()
        root.update()
        print(f"   {fmt:5s} 目标体积勾选框={str(app.chk_target['state']):8s} "
              f"输入框={str(app.ent_target['state'])}")
        lossy = fmt in ("JPG", "WEBP")
        check(f"{fmt} 目标体积可用性",
              app.chk_target["state"] == ("normal" if lossy else "disabled"))

    print("== 2. 未勾选时不生效 ==")
    app.target_format.set("JPG")
    app.enable_target_size.set(False)
    app._update_target_widgets()
    print("   target_bytes =", app._target_bytes())

    print("== 3. 各类体积目标（JPG）==")
    app.enable_target_size.set(True)
    app._update_target_widgets()
    app._add_files([os.path.join(SRC, n) for n in ("noisy.jpg", "flat.jpg", "big_flat.jpg")])
    for kb in (60, 200):
        out_dir = os.path.join(TMP, f"out_{kb}")
        app.output_dir.set(out_dir)
        app.target_kb.set(str(kb))
        app.target_format.set("JPG")
        run(app, root)
        print(f"   --- 目标 {kb} KB ---")
        print("      状态:", app.lbl_status.cget("text"))
        if app.report_path and os.path.exists(app.report_path):
            with open(app.report_path, encoding="utf-8-sig", newline="") as fp:
                rows = list(csv.reader(fp))
            head = rows[0]
            qi = head.index("质量")
            fi = head.index("成品体积")
            for r in rows[1:]:
                size_kb = r[fi]
                print(f"       {r[1]:14s} {size_kb:10s} 质量={r[qi]:4s} 状态={r[2]}")

    print("== 4. 不可达目标（1 KB）==")
    app.output_dir.set(os.path.join(TMP, "out_tiny"))
    app.target_kb.set("1")
    app.enable_resize.set(False)
    run(app, root)
    print("   状态:", app.lbl_status.cget("text"))
    txt = app.log_area.get("1.0", "end")
    check("日志含超标警告", "仍超过目标体积" in txt)

    print("== 5. 与 Resize 配合 ==")
    app.output_dir.set(os.path.join(TMP, "out_resize"))
    app.target_kb.set("30")
    app.enable_resize.set(True)
    app.resize_width.set("600")
    app.source_files = []
    app.status.clear()
    app.results.clear()
    app._add_files([os.path.join(SRC, "noisy.jpg")])
    run(app, root)
    with Image.open(os.path.join(TMP, "out_resize", "noisy.jpg")) as im:
        size = im.size
    kb = os.path.getsize(os.path.join(TMP, "out_resize", "noisy.jpg")) / 1024
    print(f"   Resize 600 + 目标 30KB -> {size[0]}×{size[1]}, {kb:.1f} KB")

    print("== 6. 配置持久化 ==")
    app._save_settings()
    saved = mod.load_settings()
    print("   ", {k: saved[k] for k in ("target_size_enabled", "target_kb")})

    app._on_close()
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)
    print("测试配置已清理")


if __name__ == "__main__":
    main()
    sys.exit(report())
