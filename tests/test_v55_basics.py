# -*- coding: utf-8 -*-
"""v5.5 新功能验收：配置持久化 / 自定义输出目录 / 取消 / 失败重试 / 结案报告。"""
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

TMP = os.path.join(os.environ.get("TEMP", "."), "aptx_v55_test")
SRC = os.path.join(TMP, "src")
OUT = os.path.join(TMP, "custom_out")
BIG = os.path.join(TMP, "big")


class FakeMB:
    last = ""

    def showinfo(self, title="", msg="", **k):
        FakeMB.last = f"[info] {title}: {msg}".replace("\n", " / ")

    def showwarning(self, title="", msg="", **k):
        FakeMB.last = f"[warn] {title}"

    def showerror(self, title="", msg="", **k):
        FakeMB.last = f"[error] {title}: {str(msg)[:40]}"


def build():
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(SRC)
    os.makedirs(BIG)
    exif = Image.Exif()
    exif[274] = 6
    Image.new("RGB", (400, 200), (200, 40, 40)).save(os.path.join(SRC, "1.jpg"), exif=exif)
    Image.new("RGBA", (300, 300), (0, 0, 0, 0)).save(os.path.join(SRC, "alpha.png"))
    Image.new("RGB", (120, 80), (30, 30, 30)).save(os.path.join(SRC, "small.jpg"))
    with open(os.path.join(SRC, "broken.jpg"), "wb") as fp:
        fp.write(open(os.path.join(SRC, "1.jpg"), "rb").read()[:1500])
    for i in range(10):
        Image.new("RGB", (3000, 2000), (i * 20, 60, 90)).save(
            os.path.join(BIG, f"big{i}.jpg"), quality=85)


def new_app():
    mod.messagebox = FakeMB()
    root = mod.create_root()
    root.withdraw()   # 测试不显示窗口，避免干扰桌面
    app = mod.ImageProcessorPro(root)
    root.update()
    return root, app


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
    build()

    # 清掉可能存在的旧配置，从默认态开始
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)

    root, app = new_app()
    print("== 1. 默认态 ==")
    print("  格式", app.target_format.get(), "| resize", app.enable_resize.get(),
          "| 水印", app.enable_watermark.get(), "| 输出目录", repr(app.output_dir.get()))

    # == 2. 自定义输出目录 + 处理，含一个损坏文件 ==
    app._add_files([os.path.join(SRC, n) for n in ("1.jpg", "alpha.png", "small.jpg", "broken.jpg")])
    app.output_dir.set(OUT)
    app._refresh_output_hint()
    app.target_format.set("PNG")
    run(app, root)

    print("== 2. 处理结果 ==")
    print("  状态:", app.lbl_status.cget("text"), "|", app.lbl_progress.cget("text").replace("\n", " / "))
    check("输出到自定义目录", os.path.isdir(OUT))
    print("  产物:", sorted(os.listdir(OUT)) if os.path.isdir(OUT) else [])
    print("  失败列表:", [os.path.basename(p) for p in app.failed_paths])
    print("  重试按钮:", str(app.btn_retry["state"]), "| 报告按钮:", str(app.btn_report["state"]))
    print("  报告路径:", app.report_path)

    # == 3. 结案报告内容 ==
    if app.report_path and os.path.exists(app.report_path):
        with open(app.report_path, encoding="utf-8-sig", newline="") as fp:
            rows = list(csv.reader(fp))
        print("== 3. 报告 ==")
        print("  行数", len(rows), "| 表头", rows[0])
        for r in rows[1:]:
            print("   ", r[:3], r[3], "->", r[4], "| 体积", r[5], "->", r[6], r[7], "| 耗时", r[8])
        with open(app.report_path, "rb") as fp:
            check("报告带 UTF-8 BOM（Excel 不乱码）", fp.read(3) == b"\xef\xbb\xbf")

    # == 4. 失败重试 ==
    before = len(app.results)
    app.retry_failed()
    end = time.time() + 60
    while app._running and time.time() < end:
        root.update()
        time.sleep(0.02)
    root.update()
    print("== 4. 重试 ==")
    print("  重试后状态:", app.lbl_status.cget("text"), "| 失败列表:",
          [os.path.basename(p) for p in app.failed_paths], "| 结果数不变:", len(app.results) == before)

    # == 5. 配置持久化 ==
    app.enable_resize.set(True)
    app.resize_width.set("640")
    app.enable_watermark.set(True)
    app.watermark_text.set("CASE 04869")
    app.target_format.set("WEBP")
    app._save_settings()
    saved = mod.load_settings()
    print("== 5. 配置持久化 ==")
    print("  落盘:", saved)
    check("配置文件已落盘", os.path.exists(mod.SETTINGS_FILE))
    root.destroy()

    # 重新启动，确认读回
    root2, app2 = new_app()
    print("  重启后:", app2.target_format.get(), app2.enable_resize.get(),
          app2.resize_width.get(), app2.enable_watermark.get(),
          app2.watermark_text.get(), repr(app2.output_dir.get()))
    root2.destroy()

    # == 6. 取消 ==
    root3, app3 = new_app()
    app3._add_files(sorted(os.path.join(BIG, n) for n in os.listdir(BIG)))
    app3.target_format.set("PNG")
    app3.output_dir.set(os.path.join(TMP, "cancel_out"))
    app3.start_thread()
    t0 = time.time()
    while time.time() - t0 < 0.45 and app3._running:
        root3.update()
        time.sleep(0.01)
    app3.cancel_processing()
    end = time.time() + 60
    while app3._running and time.time() < end:
        root3.update()
        time.sleep(0.02)
    root3.update()
    done = sum(1 for p in app3.source_files if app3.status.get(p) == 2)
    pending = sum(1 for p in app3.source_files if app3.status.get(p) == 0)
    print("== 6. 取消 ==")
    print("  状态:", app3.lbl_status.cget("text"), "| 已完成", done, "| 未处理", pending,
          "| 共", len(app3.source_files))
    print("  用时:", app3.lbl_progress.cget("text").replace("\n", " / "))
    root3.destroy()

    # 清理测试配置，避免污染用户真实设置
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)


if __name__ == "__main__":
    main()
    sys.exit(report())
