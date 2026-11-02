# -*- coding: utf-8 -*-
"""一键回归：逐个跑 tests/ 下的验收脚本，报告通过/失败。

用法：
    python tests/run_all.py            # 跑全部
    python tests/run_all.py v56 v63    # 只跑名字里含这些关键字的

每个脚本都是独立进程：Tk 应用的全局状态（消息框替换、设置文件）不会互相污染。
跑之前会清掉 %APPDATA% 里的 settings.json —— 否则上一轮残留的参数会让断言看起来通过。
"""
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
PYTHON = sys.executable

# 找不到项目源码时用系统 python 试一次（本机 tkinter 在 D:\Python314）
if not (PROJ / "image_processor_pro.py").exists():
    print(f"[!] 找不到 {PROJ / 'image_processor_pro.py'}")
    sys.exit(2)


def settings_file() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "DetectiveToolbox" / "settings.json"


def clean_settings() -> None:
    try:
        settings_file().unlink()
    except OSError:
        pass


def collect(patterns: list[str]) -> list[Path]:
    files = sorted(HERE.glob("test_*.py"))
    if not patterns:
        return files
    return [f for f in files if any(p in f.name for p in patterns)]


def run_one(path: Path, timeout: int = 300) -> tuple[bool, str, float]:
    clean_settings()
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            [PYTHON, str(path)], cwd=str(PROJ), env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"超时（>{timeout}s）", time.perf_counter() - t0
    finally:
        clean_settings()
    cost = time.perf_counter() - t0

    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        tail = "\n".join(out.strip().splitlines()[-14:])
        return False, f"退出码 {proc.returncode}\n{tail}", cost
    if "Traceback" in out:
        tail = "\n".join(out.strip().splitlines()[-14:])
        return False, f"有异常\n{tail}", cost
    # 脚本已改用 check() 断言，失败会走退出码；这里只兜底扫一下失败标记
    if "<<< 失败" in out:
        tail = "\n".join(ln for ln in out.splitlines() if "<<< 失败" in ln)
        return False, "存在未通过的断言：\n" + tail, cost
    return True, "", cost


def main() -> int:
    patterns = sys.argv[1:]
    files = collect(patterns)
    if not files:
        print("没有匹配的测试脚本")
        return 2

    print(f"回归开始 · {len(files)} 个脚本 · Python {sys.executable}\n")
    failed = []
    for f in files:
        sys.stdout.write(f"  {f.name:28s} ")
        sys.stdout.flush()
        ok, msg, cost = run_one(f)
        if ok:
            print(f"通过  ({cost:.1f}s)")
        else:
            print(f"失败  ({cost:.1f}s)")
            print(msg)
            failed.append(f.name)

    print()
    if failed:
        print(f"结果：{len(files) - len(failed)}/{len(files)} 通过，失败：{', '.join(failed)}")
        return 1
    print(f"结果：{len(files)}/{len(files)} 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
