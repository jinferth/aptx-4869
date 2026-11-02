# -*- coding: utf-8 -*-
"""v5.6 水印升级验收：九宫格 / 透明度 / 平铺 / 可选性 / 实时预览。"""
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

TMP = os.path.join(os.environ.get("TEMP", "."), "aptx_v56_test")
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
    Image.new("RGB", (600, 400), (40, 60, 90)).save(os.path.join(SRC, "flat.png"))


def region_of(bbox, size):
    """把水印包围盒换算成九宫格区域名，用于断言。"""
    cx = (bbox[0] + bbox[2]) / 2 / size[0]
    cy = (bbox[1] + bbox[3]) / 2 / size[1]
    col = "l" if cx < 0.4 else ("r" if cx > 0.6 else "c")
    row = "t" if cy < 0.4 else ("b" if cy > 0.6 else "m")
    return row + col


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

    base_rgba = Image.new("RGBA", (600, 400), (40, 60, 90, 255))
    cfg = {"text": "TOP SECRET", "pos": "br", "opacity": 70, "tile": False}

    print("== 1. 九个位置 ==")
    ok_all = True
    for key in mod.WM_POSITION_ORDER:
        cfg["pos"] = key
        out = app._apply_watermark(base_rgba.copy(), cfg)
        bbox = ImageChops.difference(base_rgba.convert("RGB"), out.convert("RGB")).getbbox()
        got = region_of(bbox, out.size) if bbox else "无"
        expect_row, expect_col = key[0], key[1]
        expect = expect_row.replace("t", "t").replace("m", "m").replace("b", "b") + expect_col
        hit = got == expect
        ok_all &= hit
        print(f"   {key} 期望 {expect} 实测 {got} bbox={bbox}")
        check(f"{key} 九宫格位置", hit)
    check("九个位置全部正确", ok_all)

    print("== 2. 透明度 ==")
    cfg.update(pos="br", tile=False)
    for op in (0, 25, 70, 100):
        cfg["opacity"] = op
        out = app._apply_watermark(base_rgba.copy(), cfg)
        diff = ImageChops.difference(base_rgba.convert("RGB"), out.convert("RGB"))
        bbox = diff.getbbox()
        peak = max(diff.getextrema()[0][1], diff.getextrema()[1][1], diff.getextrema()[2][1])
        print(f"   透明度 {op:3d}% -> 有痕迹={bbox is not None} 最大通道差={peak}")
        check(f"透明度 {op}% 的痕迹符合预期", (bbox is not None) == (op > 0))

    print("== 3. 平铺 ==")
    cfg.update(opacity=70, tile=True)
    out = app._apply_watermark(base_rgba.copy(), cfg)
    diff = ImageChops.difference(base_rgba.convert("RGB"), out.convert("RGB")).convert("L")
    pixels = list(diff.getdata())
    marked = sum(1 for p in pixels if p > 8)
    ratio = marked / len(pixels)
    print(f"   平铺覆盖率 {ratio:.1%}（单点通常 <3%）")
    check("平铺覆盖率达标", ratio > 0.08)
    print(f"   包围盒 {diff.getbbox()}")

    print("== 4. 关掉水印时不得写入任何水印 ==")
    app.target_format.set("PNG")   # 无损，才能逐像素比较"有没有水印"
    app.enable_watermark.set(False)
    app._update_wm_widgets()
    opts = app._collect_options()
    print("   options.watermark =", opts["watermark"])
    src = os.path.join(SRC, "flat.png")
    app.output_dir.set(os.path.join(TMP, "out_off"))
    info = app._process_one(src, opts, os.path.join(TMP, "out_off"))
    with Image.open(src) as a, Image.open(info["saved"]) as b:
        same = ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox() is None
    check("成品与源图逐像素一致（无水印）", same)
    print("   控件状态: 输入框", str(app.ent_watermark["state"]),
          "| 平铺", str(app.chk_tile["state"]),
          "| 滑杆", "disabled" if app.scale_opacity.instate(["disabled"]) else "normal")

    print("== 5. 勾选后写入水印 ==")
    app.enable_watermark.set(True)
    app._update_wm_widgets()
    app.wm_position.set("tl")
    app.wm_opacity.set(80)
    opts = app._collect_options()
    info = app._process_one(src, opts, os.path.join(TMP, "out_on"))
    with Image.open(src) as a, Image.open(info["saved"]) as b:
        diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
        bbox = diff.getbbox()
    print("   左上水印包围盒:", bbox, "| 区域", region_of(bbox, (600, 400)) if bbox else "无")
    print("   控件状态: 输入框", str(app.ent_watermark["state"]),
          "| 滑杆", "disabled" if app.scale_opacity.instate(["disabled"]) else "normal")

    print("== 6. 实时预览 ==")
    app._add_files([src])
    app.tree.selection_set(src)
    app._show_detail(src)
    root.update()
    base = app._preview_base
    check("缩略图基线已缓存", base is not None)
    app.enable_watermark.set(False)
    app._update_wm_widgets()
    app._on_wm_change()
    root.update()
    plain = app.detail_photo
    app.enable_watermark.set(True)
    app._update_wm_widgets()
    app.wm_tile.set(True)
    app._on_wm_change()
    root.update()
    marked = app.detail_photo
    check("切换水印后缩略图对象发生变化", plain is not marked)

    print("== 7. 配置持久化 ==")
    app.wm_position.set("mc")
    app.wm_opacity.set(45)
    app.wm_tile.set(True)
    app._save_settings()
    saved = mod.load_settings()
    print("   ", {k: saved[k] for k in ("wm_position", "wm_opacity", "wm_tile")})

    app._on_close()
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)
    print("测试配置已清理")


if __name__ == "__main__":
    main()
    sys.exit(report())
