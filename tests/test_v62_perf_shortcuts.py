# -*- coding: utf-8 -*-
"""v5.12 性能与工程验收：并行批处理 / 大图 draft / 全局快捷键。"""
import os, sys, time, shutil

# 项目根 = tests/ 的上一级；不写死本机路径，换台机器直接能跑
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import check, report
from PIL import Image
import image_processor_pro as mod

TMP = os.path.join(os.environ.get("TEMP", "."), "aptx_v62_test")
SRC = os.path.join(TMP, "src")


class FakeMB:
    def showinfo(self, *a, **k): pass
    def showwarning(self, *a, **k): pass
    def showerror(self, *a, **k): pass
    def askyesno(self, *a, **k): return True


def pump(root, seconds):
    end = time.time() + seconds
    while time.time() < end:
        root.update(); time.sleep(0.02)


def build(n=10, big=False):
    shutil.rmtree(SRC, ignore_errors=True)
    os.makedirs(SRC)
    for i in range(n):
        if big:
            Image.new("RGB", (4000, 3000), (i * 20 % 255, 80, 40)).save(
                os.path.join(SRC, f"big_{i:02d}.png"))
        else:
            Image.new("RGB", (1200, 800), (i * 20 % 255, 80, 40)).save(
                os.path.join(SRC, f"shot_{i:02d}.jpg"), quality=90)


def make_app():
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)
    mod.messagebox = FakeMB()
    mod.enable_dpi_awareness()
    root = mod.create_root()
    root.withdraw()   # 测试不显示窗口，避免干扰桌面
    app = mod.ImageProcessorPro(root)
    root.update()
    return root, app


def run_batch(app, root, parallel, rename=False):
    app.parallel.set(parallel)
    app.rename_enabled.set(rename)
    app.rename_pattern.set("CASE-{i:03}")
    app.target_format.set("JPG")
    app.enable_resize.set(False)
    out = os.path.join(TMP, f"out_p{int(parallel)}_r{int(rename)}")
    shutil.rmtree(out, ignore_errors=True)
    app.output_dir.set(out)
    files = sorted(os.path.join(SRC, f) for f in os.listdir(SRC))
    app._add_files(files)
    app._run_paths(files, reset_results=True, label="测试", silent=True)
    end = time.time() + 60
    while app._running and time.time() < end:
        root.update(); time.sleep(0.02)
    root.update()
    return out, files


def main():
    build(n=10)
    root, app = make_app()
    app._logs = []
    app.log = lambda msg, tag="dim": app._logs.append(msg)
    print("== 1. 串行处理 ==")
    t0 = time.perf_counter()
    out_s, files = run_batch(app, root, parallel=False)
    ts = time.perf_counter() - t0
    serial_out = sorted(f for f in os.listdir(out_s) if f.lower().endswith((".jpg",".png",".webp",".bmp",".ico")))
    print(f"   用时 {ts:.2f}s | 产物 {len(serial_out)} 个")
    check("串行模式不记 [PARALLEL]", any("[PARALLEL]" in l for l in app._logs), expect=False)

    print("== 2. 并行处理 ==")
    t0 = time.perf_counter()
    out_p, _ = run_batch(app, root, parallel=True)
    tp = time.perf_counter() - t0
    parallel_out = sorted(f for f in os.listdir(out_p) if f.lower().endswith((".jpg",".png",".webp",".bmp",".ico")))
    print(f"   用时 {tp:.2f}s | 产物 {len(parallel_out)} 个")
    check("并行模式记 [PARALLEL]", any("[PARALLEL]" in l for l in app._logs))
    print(f"   加速比 {ts/max(tp,1e-6):.2f}x")
    check("并行与串行产物集一致", set(serial_out) == set(parallel_out))

    print("== 3. 并行 + 重命名 ==")
    out_r, _ = run_batch(app, root, parallel=True, rename=True)
    rn = sorted(f for f in os.listdir(out_r) if f.lower().endswith((".jpg",".png",".webp",".bmp",".ico")))
    print("   产物:", rn)
    check("全为 CASE-00x.jpg", all(n.startswith("CASE-") and n.endswith(".jpg") for n in rn))

    print("== 4. 大图 draft（4000x3000 → 不缩放，应原样保留尺寸）==")
    build(n=3, big=True)
    app.parallel.set(True); app.rename_enabled.set(False); app.target_format.set("PNG")
    app.enable_resize.set(False)
    out_big = os.path.join(TMP, "out_big")
    app.output_dir.set(out_big)
    files = sorted(os.path.join(SRC, f) for f in os.listdir(SRC))
    app._add_files(files)
    app._run_paths(files, reset_results=True, label="大图", silent=True)
    end = time.time() + 60
    while app._running and time.time() < end:
        root.update(); time.sleep(0.02)
    ok = True
    for n in os.listdir(out_big):
        if not n.lower().endswith(".png"):
            continue
        with Image.open(os.path.join(out_big, n)) as im:
            if im.size != (4000, 3000):
                ok = False
    check("输出尺寸仍为 4000x3000", ok)

    print("== 5. 全局快捷键接线 ==")
    called = {}
    app.select_files = (lambda: called.setdefault("o", True)) or app.select_files
    app.start_thread = (lambda: called.setdefault("enter", True)) or app.start_thread
    app.cancel_processing = (lambda: called.setdefault("esc", True)) or app.cancel_processing
    app._on_ctrl_o(); app._on_ctrl_enter(); app._on_escape()
    check("Ctrl+O 触发加图", bool(called.get("o")))
    check("Ctrl+Enter 触发开始", bool(called.get("enter")))
    check("空闲时 Esc 不触发取消", not called.get("esc"))
    # 运行中按 Esc 才取消：模拟 running 状态
    app._running = True
    called.clear()
    app.cancel_processing = (lambda: called.setdefault("esc", True)) or app.cancel_processing
    app._on_escape()
    check("运行中 Esc 触发取消", bool(called.get("esc")))

    app._on_close()
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)
    print("测试配置已清理")


if __name__ == "__main__":
    main()
    sys.exit(report())