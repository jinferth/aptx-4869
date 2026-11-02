# -*- coding: utf-8 -*-
"""v5.9 预设方案 + EXIF 保留 验收。"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import check, report
import shutil

# 项目根 = tests/ 的上一级；不写死本机路径，换台机器直接能跑
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)

import tkinter as tk
from PIL import Image

import image_processor_pro as mod

TMP = os.path.join(os.environ.get("TEMP", "."), "aptx_v59_test")
SRC = os.path.join(TMP, "src")


class FakeMB:
    answer = True
    def showinfo(self, *a, **k): pass
    def showwarning(self, *a, **k): print("   [warn]", a[0] if a else "")
    def showerror(self, *a, **k): pass
    def askyesno(self, *a, **k): return FakeMB.answer


def build():
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(SRC)
    im = Image.new("RGB", (1000, 700), (110, 90, 70))
    exif = Image.Exif()
    exif[271] = "Canon"
    exif[272] = "EOS R5"
    exif[306] = "2026:10:29 12:00:00"
    exif[36867] = "2026:10:29 11:59:00"
    exif[34853] = {1: "N", 2: (39.0, 54.0, 23.0)}   # GPS
    im.save(os.path.join(SRC, "shot.jpg"), exif=exif)


def tags_of(path):
    with Image.open(path) as r:
        return dict(r.getexif())


def main():
    build()
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)
    mod.messagebox = FakeMB()
    mod.enable_dpi_awareness()
    root = mod.create_root()
    root.withdraw()   # 测试不显示窗口，避免干扰桌面
    app = mod.ImageProcessorPro(root)
    root.update()

    src = os.path.join(SRC, "shot.jpg")
    print("源图 EXIF tags:", sorted(tags_of(src).keys()))

    print("== 1. 默认（不保留）==")
    app.target_format.set("JPG")
    app.keep_meta.set(False)
    opts = app._collect_options()
    info = app._process_one(src, opts, os.path.join(TMP, "out_default"))
    print("   成品 tags:", sorted(tags_of(info["saved"]).keys()) or "无")

    print("== 2. 勾选保留拍摄信息 ==")
    app.keep_meta.set(True)
    opts = app._collect_options()
    info = app._process_one(src, opts, os.path.join(TMP, "out_keep"))
    got = tags_of(info["saved"])
    print("   成品 tags:", sorted(got.keys()))
    check("含品牌/机型/时间", all(t in got for t in (271, 272, 306)))
    check("不含 GPS(34853)", 34853 not in got)

    print("== 3. 保留 EXIF + 目标体积 ==")
    app.enable_target_size.set(True); app._update_target_widgets()
    app.target_kb.set("40")
    opts = app._collect_options()
    info = app._process_one(src, opts, os.path.join(TMP, "out_keep_small"))
    size_kb = os.path.getsize(info["saved"]) / 1024
    got = tags_of(info["saved"])
    print(f"   体积 {size_kb:.1f} KB (目标 40) | 质量 {info['quality']}")
    check("压体积后仍保留 EXIF", 271 in got)

    print("== 4. 内置预设 ==")
    app.enable_target_size.set(False); app._update_target_widgets()
    for name in ("微信配图", "网页 WEBP", "图标 ICO", "原图直转"):
        app.preset_name.set(name)
        app._apply_preset()
        root.update()
        print(f"   {name:8s} -> 格式={app.target_format.get():5s} "
              f"resize={app.enable_resize.get()}/{app.resize_width.get()} "
              f"目标体积={app.enable_target_size.get()}/{app.target_kb.get()} "
              f"水印={app.enable_watermark.get()}")

    print("== 5. 另存自定义预设 ==")
    app.target_format.set("WEBP"); app.enable_resize.set(True); app.resize_width.set("800")
    app.enable_watermark.set(True); app.watermark_text.set("MY MARK")
    app.wm_angle.set(-20); app.wm_color.set("#FFFFFF")
    mod.simpledialog.askstring = lambda *a, **k: "我的方案"
    app._save_preset()
    root.update()
    print("   预设列表:", app.cmb_preset["values"])
    print("   已选中:", app.preset_name.get())

    print("== 6. 重启后仍存在并可用 ==")
    app._on_close()
    root2 = mod.create_root()
    app2 = mod.ImageProcessorPro(root2)
    root2.update()
    print("   预设列表:", app2.cmb_preset["values"])
    app2.preset_name.set("我的方案")
    app2._apply_preset()
    root2.update()
    print("   套用后:", app2.target_format.get(), app2.resize_width.get(),
          app2.watermark_text.get(), app2.wm_angle.get(), app2.wm_color.get())

    print("== 7. 删除与内置保护 ==")
    FakeMB.answer = False
    app2._delete_preset()
    check("取消删除后仍在", "我的方案" in app2.cmb_preset["values"])
    FakeMB.answer = True
    app2._delete_preset()
    print("   确认删除后:", app2.cmb_preset["values"])
    app2.preset_name.set("微信配图")
    app2._delete_preset()
    check("内置预设仍在（不可删）", "微信配图" in app2.cmb_preset["values"])

    app2._on_close()
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)
    print("测试配置已清理")


if __name__ == "__main__":
    main()
    sys.exit(report())