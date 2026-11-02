# -*- coding: utf-8 -*-
"""v5.10 批量重命名验收。"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import check, report
import shutil

# 项目根 = tests/ 的上一级；不写死本机路径，换台机器直接能跑
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)

from PIL import Image
import image_processor_pro as mod

TMP = os.path.join(os.environ.get("TEMP", "."), "aptx_v60_test")
SRC = os.path.join(TMP, "src")


class FakeMB:
    def showinfo(self, *a, **k): pass
    def showwarning(self, *a, **k): pass
    def showerror(self, *a, **k): pass
    def askyesno(self, *a, **k): return True


def build():
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(SRC)
    for name, color in (("aaa.jpg", (200, 60, 60)), ("bbb.jpg", (60, 200, 60)), ("ccc.jpg", (60, 60, 200))):
        Image.new("RGB", (400, 300), color).save(os.path.join(SRC, name), quality=90)


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

    print("== 1. 默认关闭 ==")
    print("   options.rename_pattern =", repr(app._collect_options()["rename_pattern"]))
    print("   输入框状态:", str(app.ent_rename["state"]))

    print("== 2. 开启后按顺序重命名 ==")
    app.rename_enabled.set(True)
    app._update_rename_widgets()
    app.rename_pattern.set("CASE-{i:03}")
    files = sorted(os.path.join(SRC, n) for n in ("aaa.jpg", "bbb.jpg", "ccc.jpg"))
    app._add_files(files)
    app.output_dir.set(os.path.join(TMP, "out1"))
    run(app, root)
    print("   输出:", sorted(os.listdir(os.path.join(TMP, "out1"))))

    print("== 3. 保留原名占位符 ==")
    app.rename_pattern.set("{name}_small")
    app.output_dir.set(os.path.join(TMP, "out2"))
    run(app, root)
    print("   输出:", sorted(os.listdir(os.path.join(TMP, "out2"))))

    print("== 4. 同名冲突自动加后缀 ==")
    app.rename_pattern.set("SAME")
    app.output_dir.set(os.path.join(TMP, "out3"))
    run(app, root)
    o3 = [f for f in sorted(os.listdir(os.path.join(TMP, "out3"))) if f.lower().endswith(".jpg")]
    print("   输出:", o3)
    check("三个同名各自成文件", len(o3) == 3)

    print("== 5. 改名后再跑一次，不覆盖旧文件 ==")
    run(app, root)
    got = sorted(os.listdir(os.path.join(TMP, "out3")))
    imgs = [f for f in got if f.lower().endswith((".jpg", ".png", ".webp"))]
    print("   输出:", got)
    print("   图片数（应 3→6）:", len(imgs))
    check("改名后再跑不覆盖旧文件（数量翻倍）", len(imgs) == 6)

    print("== 6. 报告里的成品文件名 ==")
    import csv
    with open(app.report_path, encoding="utf-8-sig", newline="") as fp:
        rows = list(csv.reader(fp))
    head = rows[0]
    fi = head.index("成品文件")
    print("   ", [r[fi] for r in rows[1:]])

    app._on_close()
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)
    print("测试配置已清理")


def run(app, root, timeout=60):
    app.start_thread()
    end = __import__("time").time() + timeout
    while app._running and __import__("time").time() < end:
        root.update()
        __import__("time").sleep(0.02)
    root.update()


if __name__ == "__main__":
    main()
    sys.exit(report())