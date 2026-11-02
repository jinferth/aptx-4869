# -*- coding: utf-8 -*-
"""v5.8 水印颜色 / 角度 / 间距 验收。"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import check, report
import time
import shutil

# 项目根 = tests/ 的上一级；不写死本机路径，换台机器直接能跑
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)

import tkinter as tk
from PIL import Image, ImageChops

import image_processor_pro as mod

TMP = os.path.join(os.environ.get("TEMP", "."), "aptx_v58_test")


class FakeMB:
    def showinfo(self, *a, **k): pass
    def showwarning(self, *a, **k): pass
    def showerror(self, *a, **k): pass


def main():
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(TMP)
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)
    mod.messagebox = FakeMB()
    mod.enable_dpi_awareness()
    root = mod.create_root()
    root.withdraw()   # 测试不显示窗口，避免干扰桌面
    app = mod.ImageProcessorPro(root)
    root.update()

    base = Image.new("RGBA", (600, 400), (128, 128, 128, 255))
    cfg = {"text": "TOP SECRET", "pos": "br", "opacity": 100, "tile": False,
           "color": "#E74C3C", "angle": 0, "gap": 180}

    print("== 1. 五种颜色 ==")
    for name, value in mod.WM_COLORS:
        cfg["color"] = value
        out = app._apply_watermark(base.copy(), cfg)
        target = tuple(int(value.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        pixels = list(out.convert("RGB").getdata())
        hit = sum(1 for p in pixels if all(abs(p[i] - target[i]) <= 10 for i in range(3)))
        print(f"   {name} {value} -> 命中目标色的像素 {hit} 个")
        check(f"{name} 颜色命中", hit > 0)

    print("== 2. 角度 ==")
    cfg["color"] = "#E74C3C"
    for angle in (0, 30, -30, 45):
        cfg["angle"] = angle
        out = app._apply_watermark(base.copy(), cfg)
        bbox = ImageChops.difference(base.convert("RGB"), out.convert("RGB")).getbbox()
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        print(f"   {angle:+3d}° 包围盒 {w}×{h} 宽高比 {w/h:.2f}")

    print("== 3. 平铺间距 ==")
    cfg.update(tile=True, angle=0)
    for gap in (110, 180, 320):
        cfg["gap"] = gap
        out = app._apply_watermark(base.copy(), cfg)
        diff = ImageChops.difference(base.convert("RGB"), out.convert("RGB")).convert("L")
        marked = sum(1 for p in diff.getdata() if p > 8)
        print(f"   间距 {gap}% 覆盖率 {marked/len(diff.getdata()):.1%}")

    print("== 4. 倾斜平铺（角度+间距组合）==")
    cfg.update(gap=200, angle=-30)
    out = app._apply_watermark(base.copy(), cfg)
    bbox = ImageChops.difference(base.convert("RGB"), out.convert("RGB")).getbbox()
    print("   包围盒:", bbox, "| 覆盖高度比例 %.0f%%" % ((bbox[3]-bbox[1])/400*100))

    print("== 5. 位置仍正确（角度 0）==")
    cfg.update(tile=False, angle=0, color="#E74C3C")
    for key in ("tl", "mc", "br"):
        cfg["pos"] = key
        out = app._apply_watermark(base.copy(), cfg)
        b = ImageChops.difference(base.convert("RGB"), out.convert("RGB")).getbbox()
        cx = (b[0] + b[2]) / 2 / 600
        cy = (b[1] + b[3]) / 2 / 400
        col = "l" if cx < 0.4 else ("r" if cx > 0.6 else "c")
        row = "t" if cy < 0.4 else ("b" if cy > 0.6 else "m")
        print(f"   {key} -> {row}{col}")
        check(f"{key} 位置正确", row + col == key)

    print("== 6. 控件联动 ==")
    app.enable_watermark.set(True); app._update_wm_widgets(); root.update()
    print("   开: 角度滑杆", "disabled" if app.scale_angle.instate(["disabled"]) else "normal",
          "| 间距滑杆（未平铺）", "disabled" if app.scale_gap.instate(["disabled"]) else "normal")
    check("开启水印后角度滑杆可用", not app.scale_angle.instate(["disabled"]))
    check("未平铺时间距滑杆不可用", app.scale_gap.instate(["disabled"]))
    app.wm_tile.set(True); app._on_wm_toggle_tile(); root.update()
    print("   开平铺后间距滑杆", "disabled" if app.scale_gap.instate(["disabled"]) else "normal")
    check("勾平铺后间距滑杆可用", not app.scale_gap.instate(["disabled"]))
    app.wm_color.set("#4A9EFF"); app._draw_wm_colors(); root.update()
    print("   选蓝色后 _color_cells 仍为", len(app._color_cells))
    check("色块数量未因切色而变", len(app._color_cells) == 5)

    print("== 7. 持久化 ==")
    app.wm_color.set("#FFFFFF"); app.wm_angle.set(-25); app.wm_gap.set(240)
    app._save_settings()
    saved = mod.load_settings()
    print("   ", {k: saved[k] for k in ("wm_color", "wm_angle", "wm_gap")})

    app._on_close()
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)
    print("测试配置已清理")


if __name__ == "__main__":
    main()
    sys.exit(report())