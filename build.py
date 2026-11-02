# -*- coding: utf-8 -*-
"""一键构建：改版本号 → 生成打包配置 → PyInstaller → 产出发布件 → 清理旧产物。

以前这些步骤全靠手敲命令串起来，换台机器就断。现在一条命令走完，
并且每一步都可单独执行、可重复执行。

用法：
    python build.py                 用源码里的当前版本号构建
    python build.py --bump patch    先把版本号 +1（改源码），再构建
    python build.py --bump minor
    python build.py --bump major
    python build.py --no-run        只生成 spec / 版本资源 / 清理，不真的打包
    python build.py --clean-only    只清理 dist 与根目录的旧 spec、版本资源
    python build.py --keep 3        dist 里保留几个版本（默认 2）

产物布局：
    dist/                 PyInstaller 原始输出，只保留最近几个版本
    release/              可对外分发的发布目录（见 assemble_release）
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJ = Path(__file__).resolve().parent
SRC = PROJ / "image_processor_pro.py"
DIST = PROJ / "dist"
RELEASE = PROJ / "release"
BUILD = PROJ / "build"

APP_TITLE_CN = "侦探工具箱"
APP_TITLE_EN = "APTX-4869"
PRODUCT_DESC = "APTX-4869 图像情报分析终端 (Intelligence Analysis Terminal)"

# 不进包的模块：这些在 exe 里完全用不到，砍掉能省好几 MB
EXCLUDES = [
    "numpy", "scipy", "pandas", "matplotlib",
    "setuptools", "pkg_resources", "pip", "wheel",
    "unittest", "test", "pydoc_data", "distutils", "lib2to3",
    "IPython", "PyQt5", "PySide2", "PySide6",
    "http", "xml", "email", "html", "xmlrpc", "pdb", "doctest",
]

SPEC_TEMPLATE = '''# -*- mode: python ; coding: utf-8 -*-
"""{title} {ver} 打包配置（由 build.py 自动生成，勿手改）。

改打包规则请改 build.py 里的 SPEC_TEMPLATE，重新生成。
左侧取景框与预览窗需要 assets/app_icon_512.png，缺了会退化成 "NO ICON"。
"""

a = Analysis(
    ['image_processor_pro.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('conan_hd.ico', '.'),
        ('conan.ico', '.'),
        ('assets/app_icon_512.png', 'assets'),
    ],
    hiddenimports=['PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={excludes},
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='{exe_cn}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['conan_hd.ico'],
    version='{verfile}',
)
'''

# 中英双语言表：Windows 资源里同时给 zh-CN 与 en-US，
# 英文用户看到的属性面板也是英文的，而不是一串中文。
VERSION_TEMPLATE = '''VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({maj}, {min}, {pat}, 0),
    prodvers=({maj}, {min}, {pat}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable('080404b0', [
        StringStruct('CompanyName', 'APTX-4869 Project'),
        StringStruct('FileDescription', '{desc}'),
        StringStruct('FileVersion', '{quad}'),
        StringStruct('InternalName', 'APTX4869'),
        StringStruct('LegalCopyright', 'Copyright (C) 2026 APTX-4869 Project. MIT License.'),
        StringStruct('OriginalFilename', '{exe_cn}'),
        StringStruct('ProductName', '{title_cn}'),
        StringStruct('ProductVersion', '{quad}')
      ]),
      StringTable('040904b0', [
        StringStruct('CompanyName', 'APTX-4869 Project'),
        StringStruct('FileDescription', '{desc_en}'),
        StringStruct('FileVersion', '{quad}'),
        StringStruct('InternalName', 'APTX4869'),
        StringStruct('LegalCopyright', 'Copyright (C) 2026'),
        StringStruct('OriginalFilename', '{exe_en}'),
        StringStruct('ProductName', '{title_en}'),
        StringStruct('ProductVersion', '{quad}')
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [2052, 1200, 1033, 1200])])
  ]
)
'''


# ---------------------------------------------------------------- 工具

def log(msg: str) -> None:
    print(f"  {msg}")


def fail(msg: str) -> None:
    print(f"[错误] {msg}")
    sys.exit(1)


class Ver:
    """版本号。显示文本保持源码里的写法：v5.13 或 v5.13.1 都行。"""

    def __init__(self, maj: int, mi: int, pa: int = 0, text: str | None = None):
        self.maj, self.mi, self.pa = maj, mi, pa
        self.text = text or (f"v{maj}.{mi}" if pa == 0 else f"v{maj}.{mi}.{pa}")

    @property
    def quad(self) -> str:
        return f"{self.maj}.{self.mi}.{self.pa}.0"

    @property
    def tuple3(self) -> tuple[int, int, int]:
        return self.maj, self.mi, self.pa

    def __str__(self) -> str:
        return self.text


def read_version() -> Ver:
    """从源码里读当前版本号。两段（v5.13）或三段（v5.13.1）都认。"""
    txt = SRC.read_text(encoding="utf-8")
    m = re.search(r'APP_VERSION\s*=\s*"v(\d+)\.(\d+)(?:\.(\d+))?"', txt)
    if not m:
        fail("在 image_processor_pro.py 里找不到 APP_VERSION")
    maj, mi = int(m.group(1)), int(m.group(2))
    pa = int(m.group(3)) if m.group(3) else 0
    return Ver(maj, mi, pa, m.group(0).split('"')[1])


def bump_version(level: str) -> Ver:
    """把源码里的 APP_VERSION 往上提一格，并在变更摘要里插一段占位。

    major/minor 保持两段写法（v5.13 → v6.0 / v5.14），patch 一定写成三段（v5.13.1）。
    """
    cur = read_version()
    if level == "major":
        ver = Ver(cur.maj + 1, 0, 0)
    elif level == "minor":
        ver = Ver(cur.maj, cur.mi + 1, 0)
    else:
        ver = Ver(cur.maj, cur.mi, cur.pa + 1)
    txt = SRC.read_text(encoding="utf-8")
    txt = re.sub(r'APP_VERSION\s*=\s*"v\d+\.\d+(?:\.\d+)?"',
                 f'APP_VERSION = "{ver.text}"', txt, count=1)

    # 在模块文档字符串的变更摘要区插一段新条目
    marker = "---------------------------------------\n"
    idx = txt.find(marker)
    if idx != -1:
        head = (f"{ver.text} 变更摘要\n{marker}"
                f"[待补] 这一版的改动写在这里；每条说明「做了什么 / 为什么这么做」。\n\n")
        txt = txt[:idx] + head + txt[idx:]
    SRC.write_text(txt, encoding="utf-8")
    log(f"版本号 → {ver.text}")
    return ver


def write_spec(ver: "Ver") -> Path:
    v = ver.text
    exe_cn = f"{APP_TITLE_CN}_{v}"
    spec_path = PROJ / f"{exe_cn}.spec"
    spec_path.write_text(SPEC_TEMPLATE.format(
        title=APP_TITLE_CN, ver=v, excludes=repr(EXCLUDES),
        exe_cn=exe_cn, verfile=f"version_{v}.txt",
    ), encoding="utf-8")
    log(f"生成打包配置 {spec_path.name}")
    return spec_path


def write_version_resource(ver: "Ver") -> Path:
    v = ver.text
    quad = ver.quad
    path = PROJ / f"version_{v}.txt"
    path.write_text(VERSION_TEMPLATE.format(
        maj=ver.maj, min=ver.mi, pat=ver.pa, quad=quad,
        desc=PRODUCT_DESC, desc_en="APTX-4869 Intelligence Analysis Terminal",
        exe_cn=f"{APP_TITLE_CN}_{v}.exe", exe_en=f"{APP_TITLE_EN}_{v}.exe",
        title_cn=APP_TITLE_CN, title_en=APP_TITLE_EN,
    ), encoding="utf-8")
    log(f"生成版本资源 {path.name}")
    return path


def run_pyinstaller(spec: Path) -> None:
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(spec)]
    log("打包中（首次约 1~2 分钟）…")
    proc = subprocess.run(cmd, cwd=str(PROJ), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = "\n".join((proc.stdout or "").strip().splitlines()[-15:])
        fail(f"PyInstaller 失败：\n{tail}\n{(proc.stderr or '')[-800:]}")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def assemble_release(ver: "Ver") -> None:
    """组装可对外分发的发布目录。"""
    v = ver.text
    exe_cn_src = DIST / f"{APP_TITLE_CN}_{v}.exe"
    if not exe_cn_src.exists():
        fail(f"没找到打包产物 {exe_cn_src.name}")

    if RELEASE.exists():
        shutil.rmtree(RELEASE)
    RELEASE.mkdir(parents=True)

    exe_cn = RELEASE / f"{APP_TITLE_CN}_{v}.exe"
    exe_en = RELEASE / f"{APP_TITLE_EN}_{v}.exe"
    shutil.copy2(exe_cn_src, exe_cn)
    shutil.copy2(exe_cn_src, exe_en)

    for doc in ("README.md", "README_EN.md", "LICENSE"):
        src = PROJ / doc
        if src.exists():
            shutil.copy2(src, RELEASE / doc)

    digest = sha256_of(exe_cn)
    size_mb = exe_cn.stat().st_size / 1024 / 1024
    (RELEASE / "SHA256.txt").write_text(
        f"{digest}  {exe_cn.name}\n{digest}  {exe_en.name}\n", encoding="utf-8")

    notes = RELEASE / "RELEASE_NOTES.md"
    notes.write_text(build_release_notes(ver, digest, size_mb), encoding="utf-8")
    log(f"发布目录 {RELEASE.name}/：双份 exe + SHA256.txt + RELEASE_NOTES.md"
        f" + 说明书（{size_mb:.1f} MB）")


def build_release_notes(ver: "Ver", digest: str, size_mb: float) -> str:
    v = ver.text
    changelog = ""
    txt = SRC.read_text(encoding="utf-8")
    m = re.search(rf"{re.escape(v)} 变更摘要\n-+\n(.*?)(?=\n\S| 变更摘要)", txt, re.S)
    if m:
        changelog = m.group(1).strip()

    signed = "未签名（NotSigned）"
    return f"""# {APP_TITLE_EN} {v} · 发布说明

发布日期：{datetime.now().strftime('%Y-%m-%d')}
版本：{v}
体积：{size_mb:.1f} MB
SHA256：`{digest}`

## 这个包里有什么

| 文件 | 说明 |
|---|---|
| `{APP_TITLE_EN}_{v}.exe` | 英文名程序，双击即用，免安装 |
| `{APP_TITLE_CN}_{v}.exe` | 同一份程序的中文名副本 |
| `README.md` | 中文说明书 |
| `README_EN.md` | English manual |
| `SHA256.txt` | 校验和，用来确认下载的文件没被改过 |
| `RELEASE_NOTES.md` | 本文件 |

## 怎么用

1. 下载后先核对校验和（可选但推荐）：
   在 PowerShell 里执行 `Get-FileHash .\\{APP_TITLE_EN}_{v}.exe -Algorithm SHA256`，
   结果应当与 `SHA256.txt` 里的一致。
2. 双击 exe。首次运行会把参数记在 `%APPDATA%\\DetectiveToolbox\\settings.json`，
   不写程序目录，所以整个文件夹可以随便挪动。
3. 界面右上角可切换 中 / English。

## 关于数字签名

**本程序没有做代码签名（{signed}）。** 从网上下载的未签名 exe 会被 Windows SmartScreen
拦一下，需要点「更多信息 → 仍要运行」。

这是个人项目的现实取舍：代码签名证书需要按年付费，而 SmartScreen 的信誉还依赖真实下载量，
短期内买了也去不掉那个提示。替代方案是给出 SHA256 校验和——你可以自行核对来源。

## 这一版改了什么

{changelog or "（见 README 第九章）"}
"""


def clean(keep: int = 2) -> None:
    """清理旧产物：dist 里只留最近几个版本，根目录只留当前版本的 spec/版本资源。"""
    v = read_version().text

    if DIST.exists():
        exes = sorted(DIST.glob("*.exe"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in exes[keep:]:
            old.unlink()
            log(f"删除旧产物 {old.name}")
        if keep <= 1:
            for old in DIST.glob("*.exe"):
                if old.stem != f"{APP_TITLE_CN}_{v}":
                    old.unlink()

    # 根目录的 spec 与版本资源：只留当前版本
    for spec in PROJ.glob(f"{APP_TITLE_CN}_v*.spec"):
        if spec.stem != f"{APP_TITLE_CN}_{v}":
            spec.unlink()
            log(f"删除旧打包配置 {spec.name}")
    for res in PROJ.glob("version_v*.txt"):
        if res.stem != f"version_{v}":
            res.unlink()
            log(f"删除旧版本资源 {res.name}")


def main() -> int:
    ap = argparse.ArgumentParser(description="构建 APTX-4869 图像情报分析终端")
    ap.add_argument("--bump", choices=["major", "minor", "patch"], help="先把版本号往上提")
    ap.add_argument("--no-run", action="store_true", help="只生成配置与清理，不打包")
    ap.add_argument("--clean-only", action="store_true", help="只清理旧产物")
    ap.add_argument("--keep", type=int, default=2, help="dist 里保留几个版本（默认 2）")
    args = ap.parse_args()

    print("=" * 62)
    print(f"  APTX-4869 构建器 · {PROJ}")
    print("=" * 62)

    if args.bump:
        bump_version(args.bump)
    ver = read_version()
    log(f"当前版本 {ver.text}")

    if args.clean_only:
        clean(args.keep)
        print("\n  清理完成")
        return 0

    spec = write_spec(ver)
    write_version_resource(ver)

    if not args.no_run:
        run_pyinstaller(spec)
        assemble_release(ver)
    clean(args.keep)

    print("\n  完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
