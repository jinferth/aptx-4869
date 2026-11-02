# -*- coding: utf-8 -*-
"""v5.13 中英双语验收：控件/日志/报告/持久化/切回。"""
import os, sys, time, shutil, csv, glob

# 项目根 = tests/ 的上一级；不写死本机路径，换台机器直接能跑
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import check, report
from PIL import Image
import image_processor_pro as mod

TMP = os.path.join(os.environ.get("TEMP", "."), "aptx_v63_test")
SRC = os.path.join(TMP, "src")


class FakeMB:
    def showinfo(self, *a, **k): pass
    def showwarning(self, *a, **k): pass
    def showerror(self, *a, **k): pass
    def askyesno(self, *a, **k): return True


def build():
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(SRC)
    for i in range(3):
        Image.new("RGB", (600, 400), (i * 40 % 255, 90, 60)).save(
            os.path.join(SRC, f"shot_{i}.jpg"), quality=90)


def make_app():
    mod.messagebox = FakeMB()
    mod.enable_dpi_awareness()
    root = mod.create_root()
    root.withdraw()   # 测试不显示窗口，避免干扰桌面
    app = mod.ImageProcessorPro(root)
    root.update()
    return root, app


def main():
    build()
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)
    root, app = make_app()
    logs = []
    app.log = lambda msg, tag="dim": logs.append(msg)

    print("== 1. 默认中文 ==")
    print("   开始按钮:", app.btn_run.cget("text"), "| 导出报告:", app.btn_report.cget("text"))
    print("   树表头:", [app.tree.heading(c, "text") for c in ("#0", "size", "state")])
    print("   预设:", list(app.cmb_preset["values"]))
    print("   元数据勾选:", app.chk_meta.cget("text"))
    print("   标题:", root.title())

    print("== 2. 切到英文 ==")
    app.cmb_lang.set("English")
    app._on_lang_change()
    root.update()
    print("   开始按钮:", app.btn_run.cget("text"), "| 导出报告:", app.btn_report.cget("text"))
    print("   树表头:", [app.tree.heading(c, "text") for c in ("#0", "size", "state")])
    print("   预设:", list(app.cmb_preset["values"]))
    print("   元数据勾选:", app.chk_meta.cget("text"))
    print("   标题:", root.title())
    print("   监听按钮:", app.btn_watch.cget("text"))
    check("按钮译为英文", app.btn_run.cget("text") == "Start Processing")
    check("树表头译为英文",
          [app.tree.heading(c, "text") for c in ("#0", "size", "state")] == ["File Name", "Size", "Status"])
    check("预设名译为英文", list(app.cmb_preset["values"])[0] == "WeChat")
    check("标题去掉中文", "图像情报分析终端" not in root.title())

    print("== 3. 英文下跑一批 ==")
    out = os.path.join(TMP, "out_en")
    shutil.rmtree(out, ignore_errors=True)
    app.output_dir.set(out)
    app.target_format.set("JPG")
    files = sorted(os.path.join(SRC, f) for f in os.listdir(SRC))
    app._add_files(files)
    app._run_paths(files, reset_results=True, label="Test", silent=True)
    end = time.time() + 60
    while app._running and time.time() < end:
        root.update(); time.sleep(0.02)
    root.update()
    produced = sorted(os.listdir(out))
    print("   产物:", produced)
    csvs = [p for p in produced if p.endswith(".csv")]
    print("   报告文件:", csvs)
    check("报告文件名英文", all(c.startswith("case_report_") for c in csvs))
    if csvs:
        with open(os.path.join(out, csvs[0]), encoding="utf-8-sig", newline="") as fp:
            rows = list(csv.reader(fp))
        print("   表头:", rows[0])
        print("   状态列值:", [r[2] for r in rows[1:]])
    print("   日志样例:", [l for l in logs if "Resolved" in l or "PARALLEL" in l][:2])
    check("状态列英文", app.tree.item(files[0], "values")[1] == "Done")

    print("== 4. 持久化 ==")
    saved = mod.load_settings()
    print("   settings.lang =", saved.get("lang"))
    app._on_close()
    root2 = mod.create_root()
    app2 = mod.ImageProcessorPro(root2)
    root2.update()
    print("   重启后开始按钮:", app2.btn_run.cget("text"))
    check("重启后仍是英文", app2.lang == "en")
    print("   重启后预设:", list(app2.cmb_preset["values"]))

    print("== 5. 切回中文 ==")
    app2.cmb_lang.set("中文")
    app2._on_lang_change()
    root2.update()
    print("   开始按钮:", app2.btn_run.cget("text"))
    print("   树表头:", [app2.tree.heading(c, "text") for c in ("#0", "size", "state")])
    print("   预设:", list(app2.cmb_preset["values"]))
    print("   标题:", root2.title())
    check("切回中文后按钮恢复", app2.btn_run.cget("text") == "开始推理")
    check("切回中文后表头恢复",
          [app2.tree.heading(c, "text") for c in ("#0", "size", "state")] == ["文件名", "尺寸", "状态"])
    check("切回中文后预设名恢复", list(app2.cmb_preset["values"])[0] == "微信配图")

    app2._on_close()
    if os.path.exists(mod.SETTINGS_FILE):
        os.remove(mod.SETTINGS_FILE)
    print("测试配置已清理")


if __name__ == "__main__":
    main()
    sys.exit(report())