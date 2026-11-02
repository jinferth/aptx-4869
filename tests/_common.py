# -*- coding: utf-8 -*-
"""测试公共部件：断言原语、消息框替身、应用工厂。

为什么要有 check()：
历史上这些验收脚本只是把布尔值 print 出来，靠人眼看。v5.12 那次「三个同名源图被互相覆盖」
的缺陷就是这么漏过去的——脚本打印了 False，但没人把 False 当成失败。
现在统一走 check()：不符合预期就直接记为失败，run_all.py 会据此判定退出码。
"""
import os
import shutil
import sys
import time
from pathlib import Path

PROJ = str(Path(__file__).resolve().parent.parent)
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)

FAILURES: list[str] = []


def check(label: str, cond, expect: bool = True) -> bool:
    """记录一条断言。

    expect=False 用于「本不该发生」的断言（例如半写入文件不该被处理）。
    返回原值，可以继续参与表达式。
    """
    ok = (bool(cond) == expect)
    print(f"   {label}: {bool(cond)}" + ("" if ok else "   <<< 失败"))
    if not ok:
        FAILURES.append(f"{label}（期望 {expect}，实际 {bool(cond)}）")
    return cond


def report() -> int:
    """脚本收尾调用：有失败就以非零码退出。"""
    if FAILURES:
        print("\n   —— 断言未通过 ——")
        for f in FAILURES:
            print(f"   × {f}")
        return 1
    return 0


class FakeMB:
    """顶掉 tkinter 的 messagebox，避免测试时弹窗卡住。"""

    popups = 0
    last = None

    def _record(self, kind, title, text):
        FakeMB.popups += 1
        FakeMB.last = (kind, title, text)
        print(f"   [弹窗/{kind}] {title}: {str(text)[:90]}")

    def showinfo(self, title, text, **k):
        self._record("info", title, text)

    def showwarning(self, title, text, **k):
        self._record("warn", title, text)

    def showerror(self, title, text, **k):
        self._record("error", title, text)

    def askyesno(self, title, text, **k):
        self._record("ask", title, text)
        return True


def make_app():
    """建一个干净的应用实例：清配置、替换消息框、返回 (root, app)。"""
    import image_processor_pro as mod

    mod.messagebox = FakeMB()
    mod.enable_dpi_awareness()
    root = mod.create_root()
    app = mod.ImageProcessorPro(root)
    root.update()
    return root, app


def scratch_dir(name: str) -> str:
    """每个测试用自己的临时目录，避免互相踩。"""
    base = os.path.join(os.environ.get("TEMP") or os.path.expanduser("~"), "aptx_tests")
    path = os.path.join(base, name)
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)
    return path


def pump(root, seconds: float) -> None:
    """跑 Tk 事件循环若干秒，等后台线程把结果送回主线程。"""
    end = time.time() + seconds
    while time.time() < end:
        root.update()
        time.sleep(0.02)
    root.update()


def clean_settings() -> None:
    """清掉真实配置目录里的 settings.json —— 否则残留参数会让断言看起来通过。"""
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    try:
        os.remove(os.path.join(base, "DetectiveToolbox", "settings.json"))
    except OSError:
        pass
