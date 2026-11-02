# -*- coding: utf-8 -*-
"""
APTX-4869 图像情报分析终端 (Intelligence Analysis Terminal)
=========================================================
v5.14.1 变更摘要（切语言不再丢结果）
---------------------------------------
[修正] 切语言会把清单整体重置：已处理的图全部退回"待处理"、尺寸列变空、右侧详情卡清空。
       根因是 _refresh_tree 把状态写死成 STATUS_TEXT[0]；加文件时看不出问题，
       但 v5.13 起切语言也走这个函数。现改为按 status/sizes 里的真实状态重建，
       并保留选中项与详情卡。
[修正] 处理结束后再切语言，左侧状态区的"成功/失败/用时"不跟着翻译——那行文案是
       运行时拼出来的，控件登记表覆盖不到。新增 _refresh_progress_label 在切语言时重刷。
[修正] "重试失败"按钮文案是硬编码中文拼的，切英文后仍是中文；语言包里还留着一个
       半截的键 "重试失败 ("。改为 trf 模板。
[新增] docs/ 下的中英文界面截图，两份说明书顶部嵌入。
[说明] 切语言不追溯翻译历史日志——那是当时发生的事，改动它反而失真。

v5.14 变更摘要（发布就绪）
---------------------------------------
[新增] 英文说明书 README_EN.md：12 章完整对等版，不是摘要。中文 README 顶部加语言指引。
[新增] 「关于」对话框：版本、构建时间、体积、数字签名状态（直接读 PE 安全目录）、
       配置目录、许可证、当前 exe 的 SHA256。入口在侧栏底部和标题栏的版本徽标上。
[新增] 构建脚本 build.py + build.bat：改版本号 → 生成打包配置与版本资源 → PyInstaller
       → 产发布目录（双份 exe + SHA256.txt + RELEASE_NOTES.md）→ 清理旧产物，一条命令走完。
[新增] 验收脚本入库 tests/：9 个脚本 + run_all.py 一键回归；全部改成真断言（check()），
       失败会返回非零退出码，不再靠人眼看打印结果。
[架构] i18n 改为注册表驱动（LANGS）：加一门语言 = 加一条注册 + 写一份字典，不用改界面代码。
[取舍] 原本计划的「首次运行引导窗」取消：它与后台监听线程存在竞态，会让监听偶发失效。
[修正] 关闭流程幂等（_on_close 可重入），UI 泵用 _alive 标志决定是否续期。
[许可] 采用 MIT 许可（LICENSE 文件）：可自由使用、修改、再分发，保留版权声明即可。
       About 对话框与两份说明书同步标注。

v5.13 变更摘要（中英双语）
---------------------------------------
[新增] 界面右上角语言下拉：中文 / English，切换即时生效，不用重启。
[架构] 语言包 I18N_EN：键就是界面上的中文原文，tr() 取值、trf() 处理带占位符的文案。
       静态文案走控件树登记表（不改每个创建处，新增控件漏翻译也不会报错）；
       动态文案（日志/弹窗/状态列/报告）在写入时翻译。
[覆盖] 控件文案、树表头、状态列、证物格、监听区、进度与结案摘要、日志、弹窗、
       结案报告表头与文件名、预览窗、窗口标题、内置预设显示名。
[注意] 预设显示名随语言变（微信配图 → WeChat），内部键不变，
       所以切换语言后仍选中同一个预设；用户自存预设名不翻译。
[修正] 语言包键名笔误："当前一张" vs 源码"当前这张"，那条翻译原本永远命中不了。

v5.12 变更摘要（性能与工程）
---------------------------------------
[新增] 并行批处理：文件数 > 1 且 CPU 核数 > 1 时自动用线程池（上限 8 线程）并发处理。
       Pillow 的解码/缩放/编码是 C 扩展会释放 GIL，多线程能真提速，无需多进程的 pickle 坑。
       输出路径由主线程预分配，避免多线程抢写同一文件；取消时停派新任务并退出工作线程。
[新增] 大图内存优化：缩放前先对 JPEG/PNG/WEBP/TIFF 调 Image.draft() 降采样，
       8000px 级别的图不再整幅解像进内存（对应已知限制 #4）。
[新增] 全局快捷键：Ctrl+O 加图、Ctrl+Enter 开始推理、Esc 取消（运行中才生效）。
       并行开关是设置项 parallel，默认开，不想用可在 settings.json 设 false。

v5.11 变更摘要（文件夹监听）
---------------------------------------
[新增] 左侧栏 FOLDER WATCH：选目录 → 开启监听，落进该目录的新图会自动处理。
[防竞态] 只收"尺寸+修改时间连续两次观测一致，且首次见到已过 2 秒"的文件，
         避免读到写到一半的文件（半写阶段实测不处理、0 失败）。
[防自噬] 扫描时按 abspath 前缀排除本次输出目录，否则产物会被当新文件再次处理。
[防重复] 以 (路径, 大小, 修改时间) 去重，同一文件只处理一次；覆盖同名文件算新版本。
[不打断] 监听触发的处理 silent=True，不弹汇总框，只写日志；处理中到达的文件入队，
         上一轮结束后自动续跑。

v5.10 变更摘要（批量重命名）
---------------------------------------
[新增] 重命名开关 + 命名模板，支持占位符 {name} {i} {n} {date} 与补零写法 {i:03}。
       模板里的 Windows 非法字符自动替换成下划线；重名由 _unique_path 兜底加 _1/_2。
[修正] 结案报告同一秒内跑两次会互相覆盖，改为存在即加后缀。

v5.9 变更摘要（预设方案 + 拍摄信息保留）
---------------------------------------
[新增] 预设方案：4 个内置（微信配图 / 网页 WEBP / 图标 ICO / 原图直转）+ 任意自定义，
       一键套用全部参数，存于 settings.json 的 presets 字段；内置预设不可删不可改。
[新增] "保留拍摄信息（不含 GPS）"：默认关闭（等于清空全部元数据，这是原有行为）。
       勾选后只带回 Make / Model / DateTime / DateTimeOriginal，
       GPS 与 MakerNote 一律丢弃 —— 保留可用的，去掉敏感的。
[事实] 经实测，convert() 之后新图不带 info，所以此前的成品本来就没有 EXIF；
       这次不是"加一个清理开关"，而是"补一个可选的保留能力"。

v5.8 变更摘要（水印配色、角度、平铺间距）
---------------------------------------
[新增] 5 个预设水印色（红/白/黑/灰/蓝），点色块即换，预览同步刷新。
[新增] 角度滑杆 -45°~+45°，单点与平铺都生效。
[新增] 平铺间距 110%~320%，只在勾选平铺时可用。
[修正] 描边判定阈值从 128 降到 100：主题红亮度约 120，原先被判为"深色"配了白描边，
       在浅色底上等于没有；同时描边加粗到 max(2, size/14)，不透明度提到与文字同级。
[修正] 平铺补上"最后一行/列贴边"，避免间距偏大时边缘留一条完全干净的白带。

v5.7 变更摘要（目标体积压缩）
---------------------------------------
[新增] 目标体积：勾选后按目标 KB 二分质量，取"能达标里的最高质量"。
       仅对 JPG / WEBP 生效，无损格式下整组自动禁用；不改变尺寸。
[新增] 报告增加"质量"列；压到质量 1 仍超标时用 * 标出并汇总告警。
[提示] 质量被压到 20 以下时汇总提醒"先用 Resize 缩尺寸"。

v5.6 变更摘要（水印增强，保持"可选"语义）
---------------------------------------
[新增] 水印九宫格定位（3×3），替代原来写死的右下角。
[新增] 透明度 0–100% 可调，0% 等于不画（alpha 为 0 直接返回原图）。
[新增] 平铺模式：交错铺满整幅，位置参数在该模式下不生效。
[新增] 实时预览：改文字 / 调滑杆 / 换位置，案卷卡缩略图立刻重绘。
[约束] 水印始终是可选功能：未勾选时整组控件置灰、预览不叠层、处理流程
       根本不会调用 _apply_watermark，也不会写入任何水印像素。

v5.4 变更摘要（视觉方向：暗房 + 案卷纸）
---------------------------------------
[视觉] 右侧工作区统一压深，唯一浅色面是取证卡——把「左深右浅」的割裂变成
        「暗房 / 摊开的案卷」叙事，配合取景框、红章与案卷编号。
[视觉] 证据清单由 Listbox 换成 Treeview：可给每行状态着色、可右对齐尺寸列。
[新增] 证物格进度：一行方格替代进度条，绿=完成 / 红=失败 / 黄=处理中 / 灰=待处理，
        点格子跳到该证据，已完成的再点一次就用预览窗打开成品大图。
[新增] 成品大图预览窗：独立 Toplevel，可缩放（适应窗口 / 1:1 / 25%-200%）、
        可拖动平移、可与原图切换对比、可跳转输出目录。
[视觉] 取景框用 512px 图标资产替代手绘椭圆，与标题栏图标同源。

v5.3 摘要
---------
[P0] 工作线程不再直接操作 Tk 控件：所有 UI 更新统一走 queue + 主线程泵。
[P0] process_images 全流程 try/finally，任何异常都不会再让「开始」按钮永久禁用。
[P0] resize 输入改为合法校验 + 安全解析。
[P0] 补 EXIF 方向校正（ImageOps.exif_transpose）。
[P0] 水印字号按短边自适应、位置收敛到画布内。
[P0] 同名输出不再静默覆盖，冲突时自动追加 _1/_2。
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import platform
import queue
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk

# 拖拽是可降级能力：缺库或打包缺 tkdnd 时程序照常启动，只是不能拖文件
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except Exception:  # pragma: no cover
    DND_FILES = None
    TkinterDnD = None
    DND_AVAILABLE = False

# ============================ 常量 ============================

APP_NAME = "侦探工具箱"
APP_VERSION = "v5.14.1"
WINDOW_TITLE = f"APTX-4869 图像情报分析终端 (Intelligence Analysis Terminal) {APP_VERSION}"

OUTPUT_DIRNAME = "resolved_cases"
REPORT_PREFIX = "结案报告"
SUPPORTED_EXTS = (
    ".jpg", ".jpeg", ".png", ".bmp", ".webp",
    ".ico", ".tif", ".tiff", ".gif",
)
TARGET_FORMATS = ("JPG", "PNG", "BMP", "WEBP", "ICO")
DEFAULT_MAX_PX = 1080
# 监听轮询与静置：文件要「连续两次观测一致」且「首次见到已过 2 秒」才算写完
WATCH_POLL_SECONDS = 1.2
WATCH_SETTLE_SECONDS = 2.0
ICON_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

FONT_CANDIDATES = (
    "msyh.ttc", "msyhbd.ttc", "simhei.ttf", "arial.ttf",
    "PingFang.ttc", "Hiragino Sans GB.ttc",
    "DejaVuSans.ttf", "NotoSansCJK-Regular.ttc",
)

# === 暗房配色 ===
C = {
    "bg": "#101A24",
    "rail": "#16222E",
    "line": "#26333F",
    "sunken": "#0A1218",
    "hover": "#22303D",
    "text": "#E9EFF4",
    "text2": "#8FA0B0",
    "text3": "#5A6B7A",
    "red": "#E24B4A",
    "red_dark": "#C0392B",
    "blue": "#378ADD",
    "green": "#1D9E75",
    "amber": "#BA7517",
    # === 案卷纸 ===
    "paper": "#F4F1EA",
    "paper_line": "#D9D2C2",
    "paper_text": "#2C2C2A",
    "paper_muted": "#8A8272",
    "stamp": "#A32D2D",
}

# 水印九宫格：键 -> (横向比例, 纵向比例)
WM_POSITIONS = {
    "tl": (0.0, 0.0), "tc": (0.5, 0.0), "tr": (1.0, 0.0),
    "ml": (0.0, 0.5), "mc": (0.5, 0.5), "mr": (1.0, 0.5),
    "bl": (0.0, 1.0), "bc": (0.5, 1.0), "br": (1.0, 1.0),
}
WM_POSITION_ORDER = ("tl", "tc", "tr", "ml", "mc", "mr", "bl", "bc", "br")

# 水印预设色：白/黑/灰用于深浅不同的底图，红蓝保留主题色
WM_COLORS = (
    ("红", "#E74C3C"),
    ("白", "#FFFFFF"),
    ("黑", "#1A1A1A"),
    ("灰", "#9AA5B1"),
    ("蓝", "#4A9EFF"),
)

# 内置预设：只在代码里，不写进配置文件，删不掉也改不坏
BUILTIN_PRESETS = {
    "微信配图": {"target_format": "JPG", "enable_resize": True, "resize_width": "1280",
             "target_size_enabled": True, "target_kb": "300", "enable_watermark": False},
    "网页 WEBP": {"target_format": "WEBP", "enable_resize": True, "resize_width": "1600",
              "target_size_enabled": True, "target_kb": "200", "enable_watermark": False},
    "图标 ICO": {"target_format": "ICO", "enable_resize": False,
             "target_size_enabled": False, "enable_watermark": False},
    "原图直转": {"target_format": "JPG", "enable_resize": False,
             "target_size_enabled": False, "enable_watermark": False},
}

# 勾选"保留拍摄信息"时只带走这几项，GPS / MakerNote 一律不保留
EXIF_KEEP_TAGS = (271, 272, 306, 36867)   # Make / Model / DateTime / DateTimeOriginal

STATUS_COLORS = {0: "#22303D", 1: "#BA7517", 2: "#1D9E75", 3: "#E24B4A"}
STATUS_TEXT = {0: "待处理", 1: "处理中", 2: "已完成", 3: "失败"}

# ============================ 语言包 ============================
# 键就是界面上的中文原文：新增控件时忘了加翻译也不会报错，只是仍显示中文。
# 带 {占位符} 的条目用 trf() 取值——先翻成目标语言再填值，
# 这样不同语种的语序不会互相别扭。
_ZH_RE = re.compile(r"[\u4e00-\u9fff]")

I18N_EN = {
    # ---- 侧栏 ----
    "更换调查员": "Character",
    "未开启": "Not running",
    "选择目录": "Folder…",
    "开启监听": "Start Watch",
    "停止监听": "Stop Watch",
    "打开案件目录": "Open Output",
    "监听中 · 已收 {n}\n{name}": "Watching · {n} received\n{name}",
    "未开启\n{name}": "Not running\n{name}",
    "选择要监听的目录": "Choose the folder to watch",
    # ---- 分区标题 ----
    "01 · EVIDENCE LIST  证据清单": "01 · EVIDENCE LIST",
    "02 · ANALYSIS CONFIG  分析配置": "02 · ANALYSIS CONFIG",
    # ---- 证据清单 ----
    "浏览并挑选图片": "Browse & Pick",
    "浏览并挑选图片 (按住 Ctrl 多选)": "Browse & Pick Images (Ctrl to multi-select)",
    "导入目录": "Import Folder",
    "移除选中": "Remove Selected",
    "文件名": "File Name",
    "尺寸": "Size",
    "分辨率": "Dimensions",
    "状态": "Status",
    "证物格": "Evidence Grid",
    "0 项": "0 items",
    "{n} 项": "{n} items",
    "尚无证物": "No evidence yet",
    "绿=完成  红=失败  黄=处理中  点击查看":
        "Green=Done  Red=Failed  Yellow=Working  Click to view",
    # ---- 状态词 ----
    "待处理": "Pending",
    "处理中": "Working",
    "已完成": "Done",
    "失败": "Failed",
    # ---- 分析配置 ----
    "预设": "Preset",
    "另存": "Save As",
    "删除": "Delete",
    "保存预设": "Save Preset",
    "提示": "Notice",
    "重名": "Duplicate Name",
    "删除预设": "Delete Preset",
    "给这套参数起个名字：": "Name this parameter set:",
    "px 等比": "px long edge",
    "目标体积 ≤": "Target ≤",
    "颜色": "Color",
    "位置": "Position",
    "透明度": "Opacity",
    "平铺": "Tile",
    "角度": "Angle",
    "间距": "Spacing",
    "重命名": "Rename",
    "可用 {name} {i} {n} {date}，如 CASE-{i:03}":
        "Placeholders: {name} {i} {n} {date}, e.g. CASE-{i:03}",
    "保留拍摄信息（不含 GPS）": "Keep capture info (no GPS)",
    "输出到": "Output to",
    "默认目录": "default folder",
    "默认": "Default",
    "开始推理": "Start Processing",
    "取消": "Cancel",
    "重试失败": "Retry Failed",
    "重试失败 ({n})": "Retry Failed ({n})",
    "导出报告": "Export Report",
    # ---- 案卷卡 ----
    "案卷 · FORENSIC": "CASE · FORENSIC",
    "密级 · 机密": "CLASSIFIED",
    "类型": "Type",
    "体积": "Size",
    "拍摄": "Taken",
    "设备": "Device",
    "查看成品大图": "View Output",
    "计算 SHA256": "Compute SHA256",
    "选择调查员图片": "Choose Character Image",
    "移除此线索": "Remove this item",
    "清空列表": "Clear list",
    "未计算": "Not computed",
    "计算中...": "Computing...",
    "无法读取": "Unreadable",
    " (文件)": " (file)",
    # ---- 预览窗 ----
    "成品预览 · ": "Output Preview · ",
    "原图预览 · ": "Original Preview · ",
    "{w} × {h} · 显示 {pct}% · {size}": "{w} × {h} · showing {pct}% · {size}",
    "关闭": "Close",
    "对比原图": "Compare Original",
    "所在目录": "Open Folder",
    "适应窗口": "Fit Window",
    "预览 · ": "Preview · ",
    "原图": "Original",
    "成品": "Output",
    " · 显示 ": " · showing ",
    "  ·  原图": "  ·  Original",
    # ---- 输出目录 ----
    "源图所在目录": "Source folder",
    "默认 · ": "Default · ",
    "选择输出目录": "Choose Output Folder",
    "选择输出目录…": "Output Folder…",
    # ---- 内置预设名 ----
    "微信配图": "WeChat",
    "网页 WEBP": "Web WEBP",
    "图标 ICO": "Icon ICO",
    "原图直转": "Direct Convert",
    # ---- 动作标签词（拼进日志用） ----
    "开始": "Start",
    "重试": "Retry",
    "监听": "Watch",
    # ---- 结案报告表头 ----
    "序号": "No.",
    "源尺寸": "Source Size",
    "成品尺寸": "Output Size",
    "源体积": "Source File Size",
    "成品体积": "Output File Size",
    "体积变化": "Size Change",
    "质量": "Quality",
    "耗时(ms)": "Time (ms)",
    "成品文件": "Output File",
    "错误原因": "Error",
    # ---- 日志 ----
    "拖拽导入不可用（缺少 tkinterdnd2），请用「浏览并挑选图片」。":
        "Drag & drop unavailable (tkinterdnd2 missing) — use “Browse & Pick”.",
    "拖拽导入已启用：图片或文件夹可直接拖进窗口。":
        "Drag & drop enabled — drop images or folders into the window.",
    "拖拽导入初始化失败: {err}": "Drag & drop init failed: {err}",
    "处理进行中，暂不接收拖入文件。":
        "Processing in progress — dropped files are ignored.",
    "拖入的内容里没有支持的图片格式。":
        "No supported image format in the dropped content.",
    "已套用预设：{name}": "Preset applied: {name}",
    "预设已保存：{name}": "Preset saved: {name}",
    "预设已删除：{name}": "Preset deleted: {name}",
    "目标体积数值无效，本次已忽略该选项。":
        "Invalid target size — the option was ignored this time.",
    "[ERROR] 无法读取目录: {err}": "[ERROR] Cannot read folder: {err}",
    "所选文件已在清单中，已跳过。":
        "Already on the list — skipped.",
    "{label} +{n} (共 {total} 项)": "{label} +{n} ({total} total)",
    "处理进行中，暂不能修改清单。":
        "Processing in progress — the list cannot be modified.",
    "[WARN] 预览失败 {name}: {err}": "[WARN] Preview failed for {name}: {err}",
    "[WARN] 找不到可预览的文件: {target}": "[WARN] No previewable file found: {target}",
    "[ERROR] 无法预览 {name}: {err}": "[ERROR] Cannot preview {name}: {err}",
    "[ERROR] 打开预览失败: {err}": "[ERROR] Failed to open preview: {err}",
    "输出目录改为: {path}": "Output folder changed: {path}",
    "输出目录恢复默认（源图目录 / resolved_cases）。":
        "Output folder reset to default (source folder / resolved_cases).",
    "已发出取消指令，等待当前这张处理完…":
        "Cancel requested — finishing the current file…",
    "Resize 数值无效，已回退为 {px}px。": "Invalid Resize value — fell back to {px}px.",
    "{label}处理 {n} 项 → {dest}": "{label} processing {n} items → {dest}",
    "输出目录: {path}": "Output folder: {path}",
    "监听目录已设为: {path}": "Watch folder set: {path}",
    "开始监听: {path}（文件写完后自动处理）":
        "Watching: {path} (files are processed once fully written)",
    "已停止监听。": "Stopped watching.",
    "[WATCH] 扫描失败: {err}": "[WATCH] Scan failed: {err}",
    "=== 结案：成功 {ok}，失败 {failed}，用时 {t}s{tail} ===":
        "=== Case closed: {ok} ok, {failed} failed, {t}s{tail} ===",
    "    {name}: {reason}": "    {name}: {reason}",
    "[WARN] {n} 个文件压到质量 1 仍超过目标体积，报告里用 * 标出；可配合 Resize 先缩小尺寸。":
        "[WARN] {n} files still exceed the target size at quality 1 (marked * in the report); resize them first.",
    "[WARN] {n} 个文件为达标把质量压到 20 以下，画质可能明显下降；建议先勾 Resize 缩小尺寸，再压体积。":
        "[WARN] {n} files were pushed below quality 20 to meet the target; quality may visibly drop — resize first, then compress.",
    "结案报告: {path}": "Case report: {path}",
    # ---- 进度与结案摘要 ----
    "进度 {done}/{total}\n{pct}%": "Progress {done}/{total}\n{pct}%",
    "成功 {ok} / 失败 {failed}\n用时 {t}s": "Done {ok} / Failed {failed}\nElapsed {t}s",
    "\n已取消": "\nCancelled",
    "成功 {ok} / 共 {total}": "Done {ok} / Total {total}",
    "（已取消）": " (cancelled)",
    "\n用时 {t}s\n输出: {dir}": "\nElapsed {t}s\nOutput: {dir}",
    "\n\n失败 {n} 项，可点「重试失败」只重跑这些。":
        "\n\n{n} failed — click “Retry Failed” to rerun just those.",
    "\n\n{n} 项未能压到目标体积，详见报告。":
        "\n\n{n} files could not reach the target size — see the report.",
    "\n\n已生成结案报告，点「导出报告」查看。":
        "\n\nCase report generated — click “Export Report” to view.",
    # ---- 弹窗 ----
    "「{name}」是内置预设，请换个名字。":
        "“{name}” is a built-in preset — pick another name.",
    "请先在下拉框里选择一个预设。":
        "Select a preset from the dropdown first.",
    "内置预设不能删除，但它不会影响你自己保存的预设。":
        "Built-in presets cannot be deleted; your own presets are unaffected.",
    "确定删除「{name}」？": "Delete “{name}”?",
    "该文件无法解码：\n{name}\n\n{err}": "Cannot decode:\n{name}\n\n{err}",
    "无法打开预览窗口：\n{err}": "Cannot open the preview window:\n{err}",
    "还没有生成过结案报告。": "No case report has been generated yet.",
    "输出目录尚不存在，请先执行一次处理。":
        "The output folder does not exist yet — run a batch first.",
    "请先往证据清单里添加图片。": "Add images to the evidence list first.",
    # ---- 关于对话框 ----
    "关于": "About",
    "关于 APTX-4869": "About APTX-4869",
    "应用": "Application",
    "版本": "Version",
    "构建时间": "Built",
    "数字签名": "Digital signature",
    "已签名": "Signed",
    "未签名（个人项目，未购买代码签名证书）":
        "Not signed (personal project, no code-signing certificate)",
    "不适用（未打包运行）": "N/A (running from source)",
    "配置目录": "Config folder",
    "许可证": "License",
    "个人项目，未附带开源许可": "个人项目，未附带开源许可",
    "MIT 许可 · 可自由使用、修改与再分发": "MIT License — free to use, modify and redistribute",
    "复制校验和": "Copy checksum",
    "已复制到剪贴板": "Copied to clipboard",
    "打开配置目录": "Open config folder",
    "计算中…": "Computing…",
    "无法预览": "Cannot Preview",
    "预览失败": "Preview Failed",
    "成功": "Success",
    "失败: {err}": "Failed: {err}",
    "[CANCELLED] 已停止，剩余 {n} 项未处理":
        "[CANCELLED] Stopped — {n} items left unprocessed",
    "[PARALLEL] 并行处理，工作线程 {n}": "[PARALLEL] Processing in parallel, {n} worker threads",
    "[CANCELLED] 已停止，正在退出工作线程…":
        "[CANCELLED] Stopped — shutting down worker threads…",
    "[WARN] 结案报告写入失败: {err}": "[WARN] Failed to write the case report: {err}",
    "结案报告": "case_report",
    "侦探工具箱": "Detective Toolbox",
    "APTX-4869 图像情报分析终端 (Intelligence Analysis Terminal) ":
        "APTX-4869 Intelligence Analysis Terminal ",
    "语言已切换为 {lang}": "Language switched to {lang}",
}


# ============================ 语言注册表 ============================
# 加一门语言 = 在这里加一条 + 写一份对应的文案字典。
# 字典的键就是界面上的中文原文（见 I18N_EN）；查不到就原样显示中文。
# 中文自己不需要字典（原文即译文），所以 dict 留空。
LANGS = {
    "zh": {"label": "中文", "dict": {}},
    "en": {"label": "English", "dict": I18N_EN},
}


def lang_code_of(label: str) -> str | None:
    """把下拉框里的显示名（"中文" / "English"）映射回语言代码。"""
    for code, meta in LANGS.items():
        if meta["label"] == label:
            return code
    return None


# ============================ 工具函数 ============================

def pe_has_signature(path: str) -> bool | None:
    """看 PE 文件里有没有证书表。True=已签名，False=未签名，None=不是 PE 文件。

    不去调 WinVerifyTrust：那要配一串结构体，容易写错。
    直接读 PE 头的安全目录更直白——那一项非空就说明带 Authenticode 签名。
    """
    try:
        with open(path, "rb") as fp:
            head = fp.read(0x1000)
        if head[:2] != b"MZ":
            return None
        pe_off = int.from_bytes(head[0x3C:0x40], "little")
        if head[pe_off:pe_off + 4] != b"PE\0\0":
            return None
        coff = pe_off + 4
        opt = coff + 20
        magic = int.from_bytes(head[opt:opt + 2], "little")
        dd = opt + (96 if magic == 0x10B else 112)
        sec = dd + 4 * 8          # 数据目录第 5 项 = 安全（证书）目录
        size = int.from_bytes(head[sec + 4:sec + 8], "little")
        return size > 0
    except (OSError, ValueError, IndexError):
        return None


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fp:
        for chunk in iter(lambda: fp.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resource_path(name: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def human_size(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024 or unit == "GB":
            return f"{num_bytes:.0f} {unit}" if unit == "B" else f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} GB"


# ============================ 配置持久化 ============================

SETTINGS_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"),
                            "DetectiveToolbox")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "lang": "zh",
    "target_format": "JPG",
    "enable_resize": False,
    "resize_width": str(DEFAULT_MAX_PX),
    "enable_watermark": False,
    "watermark_text": "TOP SECRET",
    "wm_position": "br",
    "wm_opacity": 70,
    "wm_tile": False,
    "wm_color": "#E74C3C",
    "wm_angle": 0,
    "wm_gap": 180,
    "target_size_enabled": False,
    "target_kb": "500",
    "keep_meta": False,
    "watch_dir": "",
    "rename_enabled": False,
    "rename_pattern": "CASE-{i:03}",
    "presets": {},
    "output_dir": "",
    "last_open_dir": "",
}


def load_settings() -> dict:
    """读不到或读坏了都退回默认值，绝不让配置问题挡住启动。"""
    data = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as fp:
            saved = json.load(fp)
        if isinstance(saved, dict):
            for key in DEFAULT_SETTINGS:
                if key in saved:
                    data[key] = saved[key]
    except (OSError, ValueError):
        pass
    return data


def save_settings(data: dict) -> None:
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        tmp = SETTINGS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)
        os.replace(tmp, SETTINGS_FILE)   # 原子替换，避免写一半断电留下坏文件
    except OSError:
        pass


def short_path(path: str, limit: int = 62) -> str:
    """长路径保留尾部（目录名比盘符更有信息量）。"""
    if len(path) <= limit:
        return path
    return "…" + path[-(limit - 1):]


def enable_dpi_awareness() -> None:
    if platform.system() != "Windows":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def load_font(size: int):
    for name in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def fit_watermark_font(draw, text: str, img_w: int, base_size: int, margin: int):
    size = max(8, base_size)
    while size > 8:
        font = load_font(size)
        stroke = max(2, int(round(size / 14)))
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
        if bbox[2] - bbox[0] <= img_w - 2 * margin:
            return font, stroke, bbox
        size -= 2
    font = load_font(size)
    stroke = max(2, int(round(size / 14)))
    return font, stroke, draw.textbbox((0, 0), text, font=font, stroke_width=stroke)


def make_stamp(text: str = "TOP SECRET", size: int = 16, angle: float = 12) -> Image.Image:
    """预渲染一枚斜置红章。Tk 不能旋转文字，只能先生成 PNG 再贴。"""
    font = load_font(size)
    gap = max(2, size // 6)
    widths = []
    for ch in text:
        box = font.getbbox(ch)
        widths.append(box[2] - box[0])
    text_w = sum(widths) + gap * max(0, len(text) - 1)
    pad = 12
    img = Image.new("RGBA", (int(text_w) + pad * 2, size * 2 + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color = (163, 45, 45)
    draw.rectangle([3, 3, img.width - 4, img.height - 4], outline=color + (215,), width=2)
    x = pad
    for ch, w in zip(text, widths):
        draw.text((x, pad - 2), ch, font=font, fill=color + (230,))
        x += w + gap
    return img.rotate(angle, expand=True, resample=Image.BICUBIC)


# ============================ 成品预览窗 ============================

class PreviewWindow(tk.Toplevel):
    """独立预览窗：看成品大图，可缩放平移，可与原图切换对比。"""

    ZOOMS = (0.25, 0.33, 0.5, 0.67, 0.75, 1.0, 1.5, 2.0)

    def __init__(self, master, path: str, original_path: str | None = None, tr=None):
        super().__init__(master)
        self.path = path
        self.original_path = original_path
        self.showing_original = False
        # 预览窗不在主控件树里，语言得由外面传进来
        self._tr = tr or (lambda s: s)

        self.title(self._tr("成品预览 · ") + os.path.basename(path))
        self.configure(bg=C["bg"])
        self.geometry("1100x780")
        self.minsize(640, 480)
        try:
            self.iconbitmap(resource_path("conan_hd.ico"))
        except Exception:
            pass

        self.img = self._load(path)
        self.scale: float | None = None
        self._photo = None

        bar = tk.Frame(self, bg=C["rail"], height=46)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        tk.Label(bar, text=os.path.basename(path), bg=C["rail"], fg=C["text"],
                 font=("Microsoft YaHei UI", 9)).pack(side="left", padx=14)

        self.lbl_info = tk.Label(bar, text="", bg=C["rail"], fg=C["text3"],
                                 font=("Consolas", 8))
        self.lbl_info.pack(side="left", padx=10)

        ttk.Button(bar, text=self._tr("关闭"), command=self.destroy).pack(
            side="right", padx=(4, 12), pady=6)
        if original_path:
            ttk.Button(bar, text=self._tr("对比原图"), command=self.toggle_original).pack(
                side="right", padx=4, pady=6)
        ttk.Button(bar, text=self._tr("所在目录"), command=self.open_folder).pack(
            side="right", padx=4, pady=6)
        ttk.Button(bar, text="1:1", command=lambda: self.set_zoom(1.0)).pack(
            side="right", padx=4, pady=6)
        ttk.Button(bar, text=self._tr("适应窗口"), command=self.fit_window).pack(
            side="right", padx=4, pady=6)

        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(body, bg=C["sunken"], highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(body, orient="vertical", command=self.canvas.yview)
        hsb = ttk.Scrollbar(body, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        self._item = self.canvas.create_image(0, 0, anchor="nw")
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<plus>", lambda e: self.step_zoom(1))
        self.bind("<equal>", lambda e: self.step_zoom(1))
        self.bind("<minus>", lambda e: self.step_zoom(-1))

        self.after(80, self._render)

    @staticmethod
    def _load(path: str) -> Image.Image:
        with Image.open(path) as raw:
            return ImageOps.exif_transpose(raw).convert("RGB")

    def fit_window(self) -> None:
        self.scale = None
        self._render()

    def set_zoom(self, value: float) -> None:
        self.scale = value
        self._render()

    def step_zoom(self, direction: int) -> None:
        cur = self.scale if self.scale else self._fit_scale()
        if direction > 0:
            larger = [z for z in self.ZOOMS if z > cur + 1e-6]
            if larger:
                self.set_zoom(larger[0])
        else:
            smaller = [z for z in self.ZOOMS if z < cur - 1e-6]
            if smaller:
                self.set_zoom(smaller[-1])

    def _fit_scale(self) -> float:
        cw = max(self.canvas.winfo_width(), 1)
        ch = max(self.canvas.winfo_height(), 1)
        return min(cw / self.img.width, ch / self.img.height, 1.0)

    def _on_resize(self, _event=None) -> None:
        if self.scale is None:
            self._render()

    def _on_wheel(self, event) -> None:
        self.step_zoom(1 if event.delta > 0 else -1)

    def _on_press(self, event) -> None:
        self.canvas.scan_mark(event.x, event.y)

    def _on_drag(self, event) -> None:
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def toggle_original(self) -> None:
        if not self.original_path or not os.path.exists(self.original_path):
            return
        self.showing_original = not self.showing_original
        target = self.original_path if self.showing_original else self.path
        self.img = self._load(target)
        key = "原图预览 · " if self.showing_original else "成品预览 · "
        self.title(self._tr(key) + os.path.basename(target))
        self.scale = None
        self._render()

    def open_folder(self) -> None:
        ImageProcessorPro._open_path(os.path.dirname(self.path))

    def _render(self) -> None:
        if self.img.width <= 0 or self.img.height <= 0:
            return
        scale = max(0.02, self.scale if self.scale else self._fit_scale())
        target_w = max(1, int(self.img.width * scale))
        target_h = max(1, int(self.img.height * scale))

        if (target_w, target_h) == self.img.size:
            frame = self.img
        else:
            resample = Image.Resampling.LANCZOS if scale < 1 else Image.Resampling.BICUBIC
            frame = self.img.resize((target_w, target_h), resample)

        self._photo = ImageTk.PhotoImage(frame)
        self.canvas.itemconfig(self._item, image=self._photo)
        # 图片比画布小时居中，而不是贴在左上角留一大片空
        cw = max(self.canvas.winfo_width(), target_w)
        ch = max(self.canvas.winfo_height(), target_h)
        self.canvas.coords(self._item, (cw - target_w) // 2, (ch - target_h) // 2)
        self.canvas.config(scrollregion=(0, 0, cw, ch))

        try:
            size = human_size(os.path.getsize(self.path))
        except OSError:
            size = "—"
        self.lbl_info.config(
            text=self._tr("{w} × {h} · 显示 {pct}% · {size}").format(
                w=self.img.width, h=self.img.height, pct=int(scale * 100), size=size)
                 + (self._tr("  ·  原图") if self.showing_original else ""))


# ============================ 关于对话框 ============================

class AboutWindow(tk.Toplevel):
    """版本、构建信息、签名状态、配置目录。

    存在的理由很实际：程序没做代码签名，下载的人需要自己确认来源。
    这一页把能自证的东西都摆出来——版本号、构建时间、体积、SHA256、签名状态。
    """

    def __init__(self, master, tr=None):
        super().__init__(master)
        self._tr = tr or (lambda s: s)
        self._digest = ""
        self.title(self._tr("关于 APTX-4869"))
        self.configure(bg=C["bg"])
        self.geometry("480x430")
        self.resizable(False, False)
        self.transient(master)

        head = tk.Frame(self, bg=C["bg"])
        head.pack(fill="x", padx=18, pady=(16, 0))
        tk.Label(head, text="APTX-4869", font=self._tr_font(20, "bold"),
                 bg=C["bg"], fg=C["text"]).pack(anchor="w")
        tk.Label(head, text="图像情报分析终端 · Intelligence Analysis Terminal",
                 font=("Microsoft YaHei UI", 8), bg=C["bg"],
                 fg=C["text3"]).pack(anchor="w")

        self.body = tk.Frame(self, bg=C["bg"])
        self.body.pack(fill="both", expand=True, padx=18, pady=(12, 0))
        body = self.body
        self.rows = {}
        exe_path = sys.executable if getattr(sys, "frozen", False) else \
            os.path.abspath(__file__)

        built = ""
        size = ""
        try:
            built = time.strftime("%Y-%m-%d %H:%M",
                                  time.localtime(os.path.getmtime(exe_path)))
            size = human_size(os.path.getsize(exe_path))
        except OSError:
            pass

        signed = pe_has_signature(exe_path)
        if signed is None:
            sig_text = self._tr("不适用（未打包运行）")
        else:
            sig_text = self._tr("已签名") if signed else \
                self._tr("未签名（个人项目，未购买代码签名证书）")

        items = [
            ("应用", "APTX-4869 图像情报分析终端"),
            ("版本", APP_VERSION),
            ("构建时间", built),
            ("体积", size),
            ("数字签名", sig_text),
            ("配置目录", SETTINGS_DIR),
            ("许可证", self._tr("MIT 许可 · 可自由使用、修改与再分发")),
        ]
        for i, (label, value) in enumerate(items):
            tk.Label(body, text=self._tr(label), width=10, anchor="w",
                     font=("Microsoft YaHei UI", 8), bg=C["bg"],
                     fg=C["text3"]).grid(row=i, column=0, sticky="w", pady=3)
            tk.Label(body, text=value, anchor="w", wraplength=330,
                     font=("Microsoft YaHei UI", 8), bg=C["bg"],
                     fg=C["text"]).grid(row=i, column=1, sticky="w", pady=3)

        sha_row = len(items)
        tk.Label(body, text="SHA256", width=10, anchor="w",
                 font=("Microsoft YaHei UI", 8), bg=C["bg"],
                 fg=C["text3"]).grid(row=sha_row, column=0, sticky="w", pady=3)
        self.lbl_sha = tk.Label(body, text=self._tr("计算中…"), anchor="w",
                                wraplength=330, font=("Consolas", 7),
                                bg=C["bg"], fg=C["text2"])
        self.lbl_sha.grid(row=sha_row, column=1, sticky="w", pady=3)

        bar = tk.Frame(self, bg=C["bg"])
        bar.pack(fill="x", side="bottom", padx=18, pady=(0, 16))
        ttk.Button(bar, text=self._tr("复制校验和"), command=self._copy_sha).pack(
            side="left")
        ttk.Button(bar, text=self._tr("打开配置目录"), command=self._open_cfg).pack(
            side="left", padx=6)
        ttk.Button(bar, text=self._tr("关闭"), command=self.destroy).pack(side="right")

        # 校验和直接在主线程算：19MB 约 60ms，无感。
        # 放后台线程反而危险——线程里调 self.after 属于跨线程操作 Tk。
        self.after(60, self._calc_sha)

    @staticmethod
    def _tr_font(size: int, weight: str = "normal"):
        system = platform.system()
        family = "Impact" if system == "Windows" else "Arial Black"
        return (family, size, weight)

    def _calc_sha(self) -> None:
        exe_path = sys.executable if getattr(sys, "frozen", False) else \
            os.path.abspath(__file__)
        try:
            digest = file_sha256(exe_path)
        except OSError:
            digest = ""
        self._set_sha(digest)

    def _set_sha(self, digest: str) -> None:
        self._digest = digest
        self.lbl_sha.config(text=digest[:32] + "\n" + digest[32:] if digest else "—")

    def _copy_sha(self) -> None:
        if not self._digest:
            return
        self.clipboard_clear()
        self.clipboard_append(self._digest)
        self.lbl_sha.config(text=self._tr("已复制到剪贴板"))

    def _open_cfg(self) -> None:
        try:
            os.startfile(SETTINGS_DIR)       # noqa: S606 - Windows 专有
        except OSError:
            pass


# ============================ 主应用 ============================

class ImageProcessorPro:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.geometry("1200x920")
        self.root.minsize(1060, 840)

        system = platform.system()
        title_font = "Impact" if system == "Windows" else "Arial Black"
        body_font = "Microsoft YaHei UI" if system == "Windows" else "Helvetica Neue"
        mono_font = "Consolas" if system == "Windows" else "Menlo"
        self.fonts = {
            "h1": (title_font, 18),
            "h2": (title_font, 11),
            "body": (body_font, 9),
            "small": (body_font, 8),
            "tiny": (body_font, 7),
            "mono": (mono_font, 8),
            "mono_md": (mono_font, 9),
        }

        self.root.configure(bg=C["bg"])

        # 先读配置，再建变量，避免建完又被覆盖
        self.settings = load_settings()

        # 语言：zh = 中文原文（不查表），en = 走 I18N_EN 语言包
        self.lang = str(self.settings.get("lang", "zh"))
        if self.lang not in ("zh", "en"):
            self.lang = "zh"
        # 控件文案登记表：(控件, 原文)，切换语言时按表重刷
        self._i18n_reg: list[tuple] = []
        self.root.title(self._window_title())

        self.source_files: list[str] = []
        self.status: dict[str, int] = {}
        self.results: dict[str, str] = {}
        # 每张图的成品尺寸文案（"1600×1200"）。切语言要重建清单，
        # 不能指望从表格里读回旧值——重建时表格已经被清空了。
        self.sizes: dict[str, str] = {}
        self.failed_paths: list[str] = []
        self.report_path: str | None = None
        self.target_format = tk.StringVar(value=str(self.settings["target_format"]))
        self.enable_resize = tk.BooleanVar(value=bool(self.settings["enable_resize"]))
        self.resize_width = tk.StringVar(value=str(self.settings["resize_width"]))
        self.enable_watermark = tk.BooleanVar(value=bool(self.settings["enable_watermark"]))
        self.watermark_text = tk.StringVar(value=str(self.settings["watermark_text"]))
        self.wm_position = tk.StringVar(value=str(self.settings.get("wm_position", "br")))
        self.wm_opacity = tk.IntVar(value=int(self.settings.get("wm_opacity", 70)))
        self.wm_tile = tk.BooleanVar(value=bool(self.settings.get("wm_tile", False)))
        self.wm_color = tk.StringVar(value=str(self.settings.get("wm_color", "#E74C3C")))
        self.wm_angle = tk.IntVar(value=int(self.settings.get("wm_angle", 0)))
        self.wm_gap = tk.IntVar(value=int(self.settings.get("wm_gap", 180)))
        self.enable_target_size = tk.BooleanVar(value=bool(self.settings.get("target_size_enabled", False)))
        self.target_kb = tk.StringVar(value=str(self.settings.get("target_kb", "500")))
        self.keep_meta = tk.BooleanVar(value=bool(self.settings.get("keep_meta", False)))
        self.rename_enabled = tk.BooleanVar(value=bool(self.settings.get("rename_enabled", False)))
        # 并行处理：默认开。PIL 的解码/缩放/编码是 C 扩展，会释放 GIL，
        # 所以多线程能真提速；不需要多进程，也就没有 pickle / freeze_support 的坑。
        # 想关掉就在 settings.json 把 parallel 设成 false。
        self.parallel = tk.BooleanVar(value=bool(self.settings.get("parallel", True)))
        # 监听状态：不持久化「是否在监听」，只记住上次选过的目录
        self._watch_dir = str(self.settings.get("watch_dir", ""))
        self._watching = False
        self._watch_count = 0
        self._watch_exclude = ""
        self._watch_thread: threading.Thread | None = None
        self._stop_watch = threading.Event()
        self._seen_watch: set = set()
        self._pending_watch: dict = {}
        self._watch_queue: list[str] = []
        self.rename_pattern = tk.StringVar(value=str(self.settings.get("rename_pattern", "CASE-{i:03}")))
        self.preset_name = tk.StringVar(value="")
        self.user_presets: dict = dict(self.settings.get("presets") or {})
        self.output_dir = tk.StringVar(value=str(self.settings["output_dir"]))
        self.output_hint = tk.StringVar(value="")
        self.case_no = tk.StringVar(value="CASE No. 04869-00")
        self.last_open_dir = str(self.settings["last_open_dir"]) or os.path.expanduser("~")
        self.last_output_dir: str | None = None
        self._cancel = threading.Event()
        self._alive = True          # 窗口还活着；关闭后为 False，UI 泵随之停下
        self._closed = False

        self.char_photo = None
        self.detail_photo = None
        self._stamp_photo = None
        self._char_source: str | None = None
        self._vf_width = 0
        self._cell_rects: list[tuple[float, float, float, float, str]] = []
        self._running = False
        self._ui_queue: queue.Queue = queue.Queue()
        self._preview: PreviewWindow | None = None
        self._about: AboutWindow | None = None
        # tk.Variable 一旦被 GC，会在 __del__ 里调 tk.call("unset", ...)。
        # 那个调用可能发生在后台线程上（非主线程调 Tcl 会破坏解释器状态，
        # 表现为控件命令凭空消失："invalid command name"）。
        # 所以凡是会短命的 tk 变量，都挂在 app 上由主线程持有。

        self._setup_styles()
        self._setup_ui()
        self._collect_i18n_widgets()
        if self.lang == "en":
            self._apply_language()
        self._fit_window()
        self._apply_window_icon()
        self._setup_dnd()
        self._refresh_output_hint()
        self._refresh_presets()
        self._setup_shortcuts()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._after_id = self.root.after(40, self._pump_ui_queue)

    # ------------------------------------------------------------------
    # 配置保存
    # ------------------------------------------------------------------
    def _current_settings(self) -> dict:
        return {
            "target_format": self.target_format.get(),
            "enable_resize": bool(self.enable_resize.get()),
            "resize_width": self.resize_width.get(),
            "enable_watermark": bool(self.enable_watermark.get()),
            "watermark_text": self.watermark_text.get(),
            "wm_position": self.wm_position.get(),
            "wm_opacity": int(self.wm_opacity.get()),
            "wm_tile": bool(self.wm_tile.get()),
            "wm_color": self.wm_color.get(),
            "wm_angle": int(self.wm_angle.get()),
            "wm_gap": int(self.wm_gap.get()),
            "target_size_enabled": bool(self.enable_target_size.get()),
            "target_kb": self.target_kb.get(),
            "keep_meta": bool(self.keep_meta.get()),
            "parallel": bool(self.parallel.get()),
            "lang": self.lang,
            "rename_enabled": bool(self.rename_enabled.get()),
            "rename_pattern": self.rename_pattern.get(),
            "watch_dir": self._watch_dir,
            "presets": self.user_presets,
            "output_dir": self.output_dir.get(),
            "last_open_dir": self.last_open_dir,
        }

    def _save_settings(self) -> None:
        self.settings = self._current_settings()
        save_settings(self.settings)

    def _on_close(self) -> None:
        if self._closed:            # 幂等：destroy 可能经 WM_DELETE_WINDOW 再次进来
            return
        self._closed = True
        self._alive = False         # 通知 UI 泵停下来
        self._cancel.set()          # 让后台线程尽快收手，避免关窗后还在写文件
        self._watching = False
        self._stop_watch.set()
        # 副窗要在主线程里显式销毁：让它们的 tk 资源在正确的线程释放
        for win in (self._about, self._preview):
            try:
                if win is not None and win.winfo_exists():
                    win.destroy()
            except Exception:
                pass
        self._save_settings()
        try:
            if self._after_id:
                self.root.after_cancel(self._after_id)
        except Exception:
            pass
        self.root.destroy()

    # ------------------------------------------------------------------
    # 拖拽导入（可降级）
    # ------------------------------------------------------------------
    def _setup_dnd(self) -> None:
        if not (DND_AVAILABLE and hasattr(self.root, "drop_target_register")):
            self.log(self.tr("拖拽导入不可用（缺少 tkinterdnd2），请用「浏览并挑选图片」。"), "dim")
            return
        try:
            for widget in (self.root, self.tree, self.cells):
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._on_drop)
            self.log(self.tr("拖拽导入已启用：图片或文件夹可直接拖进窗口。"), "dim")
        except Exception as exc:
            print(f"[dnd] disabled: {exc}", file=sys.stderr)
            self.log(self.trf("拖拽导入初始化失败: {err}", err=exc), "err")

    # ------------------------------------------------------------------
    # 语言切换
    # ------------------------------------------------------------------
    def _window_title(self) -> str:
        return f"{self.tr('APTX-4869 图像情报分析终端 (Intelligence Analysis Terminal) ')}{APP_VERSION}"

    def tr(self, text: str) -> str:
        """按当前语言取文案；语言包里没有就原样返回（中文即原文）。"""
        return LANGS.get(self.lang, {}).get("dict", {}).get(text, text)

    def trf(self, template: str, **kw) -> str:
        """带占位符的文案：先翻成目标语言再填值，语序才不会互相别扭。"""
        return self.tr(template).format(**kw)

    def _collect_i18n_widgets(self) -> None:
        """登记所有可翻译的控件文案。

        走控件树而不是在每个创建处包 tr()：以后新增控件忘了加翻译也不会报错，
        只是那一条仍是中文。登记的是中文原文，所以切回中文不会变成"英文→英文"。
        """
        self._i18n_reg = []

        def walk(widget):
            for child in widget.winfo_children():
                try:
                    txt = child.cget("text")
                except Exception:
                    txt = None
                if isinstance(txt, str) and txt and _ZH_RE.search(txt):
                    self._i18n_reg.append((child, "text", txt))
                walk(child)

        walk(self.root)
        for col in ("#0", "size", "state"):
            try:
                self._i18n_reg.append(
                    (self.tree, f"heading:{col}", self.tree.heading(col, "text")))
            except Exception:
                pass

    def _apply_language(self) -> None:
        """把登记过的文案按当前语言重刷一遍。"""
        for widget, kind, original in self._i18n_reg:
            try:
                if kind.startswith("heading:"):
                    widget.heading(kind.split(":", 1)[1], text=self.tr(original))
                else:
                    widget.config(text=self.tr(original))
            except Exception:
                pass
        # 运行时才生成的文案要单独刷
        # 预览窗与关于窗是独立 Toplevel，登记不到控件树里，直接销毁重建：
        # 重建时用的是当前语言，重新打开就是新的语言
        for attr in ("_preview", "_about"):
            win = getattr(self, attr, None)
            try:
                if win is not None and win.winfo_exists():
                    win.destroy()
            except Exception:
                pass
            setattr(self, attr, None)
        self._update_watch_ui()
        self._refresh_output_hint()
        self._refresh_presets()
        self._refresh_progress_label()
        self._draw_cells()
        self._refresh_tree()
        selected = self._selected_path()
        if selected:
            self._show_detail(selected)

    def _on_lang_change(self, event=None) -> None:
        code = lang_code_of(self.cmb_lang.get())
        if code:
            self.lang = code
        self.root.title(self._window_title())
        self._apply_language()
        self._save_settings()
        self.log(self.trf("语言已切换为 {lang}", lang=self.cmb_lang.get()), "dim")
        self._fit_window()

    def _setup_shortcuts(self) -> None:
        """全局快捷键：Ctrl+O 加图、Ctrl+Enter 开始、Esc 取消。"""
        self.root.bind_all("<Control-o>", lambda e: self._on_ctrl_o())
        self.root.bind_all("<Control-Return>", lambda e: self._on_ctrl_enter())
        self.root.bind_all("<Escape>", lambda e: self._on_escape())

    def _on_ctrl_o(self) -> None:
        if not self._running:
            self.select_files()

    def _on_ctrl_enter(self) -> None:
        if not self._running:
            self.start_thread()

    def _on_escape(self) -> None:
        if self._running:
            self.cancel_processing()

    def _on_drop(self, event):
        if self._running:
            self.log(self.tr("处理进行中，暂不接收拖入文件。"), "err")
            return
        try:
            items = list(self.root.tk.splitlist(event.data))
        except Exception:
            items = str(event.data).split()
        files: list[str] = []
        for item in items:
            if os.path.isdir(item):
                files.extend(self._scan_dir(item))
            elif item.lower().endswith(SUPPORTED_EXTS) and os.path.isfile(item):
                files.append(item)
        if not files:
            self.log(self.tr("拖入的内容里没有支持的图片格式。"), "err")
            return
        if os.path.dirname(files[0]):
            self.last_open_dir = os.path.dirname(files[0])
        self._add_files(files, label="Dropped")

    # ------------------------------------------------------------------
    # 线程安全通道
    # ------------------------------------------------------------------
    def _post(self, fn, *args, **kwargs) -> None:
        self._ui_queue.put((fn, args, kwargs))

    def _pump_ui_queue(self) -> None:
        if not self._alive:
            return
        try:
            while True:
                fn, args, kwargs = self._ui_queue.get_nowait()
                try:
                    fn(*args, **kwargs)
                except Exception as exc:
                    print(f"[ui-queue] {exc}", file=sys.stderr)
        except queue.Empty:
            pass
        if not self._alive:
            return
        try:
            self._after_id = self.root.after(40, self._pump_ui_queue)
        except tk.TclError:
            pass      # 窗口已销毁，泵自然停止

    def _fit_window(self) -> None:
        """按内容实际请求高度定窗口，避免高分屏/小屏上日志区被挤出窗口。

        必须先把重绘跑完再量：刚建完控件时 ttk 样式与字体度量还没落到
        winfo_reqheight 上，量出来的值偏小，窗口定小后日志区就只剩两行。
        """
        for _ in range(2):
            self.root.update_idletasks()
            self.root.update()
        need_h = self.content.winfo_reqheight() + 64
        need_w = max(1200, self.content.winfo_reqwidth() + 320)
        avail_h = self.root.winfo_screenheight() - 100
        avail_w = self.root.winfo_screenwidth() - 80
        width = int(min(need_w, avail_w))
        height = int(min(need_h, avail_h))
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(min(1060, width), min(height, avail_h))

    # ------------------------------------------------------------------
    # 样式（全域深色）
    # ------------------------------------------------------------------
    def _setup_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=C["bg"])

        style.configure("TButton", font=self.fonts["body"], background=C["hover"],
                        foreground="#C9D6E0", borderwidth=0, focusthickness=0, padding=(10, 6))
        style.map("TButton",
                  background=[("active", "#2C3D4D"), ("disabled", "#1A2632")],
                  foreground=[("disabled", C["text3"])])

        style.configure("Red.TButton", background=C["red"], foreground="white",
                        font=self.fonts["h2"], padding=(10, 9))
        style.map("Red.TButton",
                  background=[("active", C["red_dark"]), ("disabled", "#3A2A2A")],
                  foreground=[("disabled", "#7A5A5A")])

        style.configure("Paper.TButton", background="#EDE6D6", foreground=C["paper_text"],
                        font=self.fonts["small"], borderwidth=0, padding=(8, 5))
        style.map("Paper.TButton",
                  background=[("active", "#E2D9C4"), ("disabled", "#F3EFE6")],
                  foreground=[("disabled", "#BCB6A8")])

        style.configure("Stamp.TButton", background=C["stamp"], foreground="white",
                        font=self.fonts["small"], borderwidth=0, padding=(8, 6))
        style.map("Stamp.TButton",
                  background=[("active", "#8A2323"), ("disabled", "#D8CEC0")],
                  foreground=[("disabled", "#FAF7F1")])

        style.configure("TCombobox", fieldbackground=C["sunken"], background=C["hover"],
                        foreground=C["text"], arrowcolor=C["text2"],
                        bordercolor=C["line"], lightcolor=C["sunken"], darkcolor=C["sunken"],
                        insertcolor=C["text"], padding=3)
        style.map("TCombobox",
                  fieldbackground=[("readonly", C["sunken"]), ("disabled", "#1A2632")],
                  foreground=[("readonly", C["text"]), ("disabled", C["text3"])],
                  selectbackground=[("readonly", C["sunken"])],
                  selectforeground=[("readonly", C["text"])])

        style.configure("TEntry", fieldbackground=C["sunken"], foreground=C["text"],
                        insertcolor=C["text"], bordercolor=C["line"],
                        lightcolor=C["sunken"], darkcolor=C["sunken"], padding=3)
        style.map("TEntry", fieldbackground=[("disabled", "#1A2632")])

        style.configure("Treeview", background=C["sunken"], fieldbackground=C["sunken"],
                        foreground="#C9D6E0", borderwidth=0, rowheight=24,
                        font=self.fonts["mono_md"])
        style.map("Treeview", background=[("selected", C["hover"])],
                  foreground=[("selected", "#FFFFFF")])
        style.configure("Treeview.Heading", background=C["rail"], foreground=C["text3"],
                        relief="flat", font=self.fonts["tiny"], padding=(4, 5))
        style.map("Treeview.Heading", background=[("active", C["hover"])])

        style.configure("Vertical.TScrollbar", background=C["hover"], troughcolor=C["sunken"],
                        bordercolor=C["sunken"], arrowcolor=C["text2"])
        style.configure("Horizontal.TScrollbar", background=C["hover"], troughcolor=C["sunken"],
                        bordercolor=C["sunken"], arrowcolor=C["text2"])

        self.root.option_add("*TCombobox*Listbox.background", C["sunken"])
        self.root.option_add("*TCombobox*Listbox.foreground", C["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", C["red"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
        self.root.option_add("*TCombobox*Listbox.font", self.fonts["mono_md"])

    def _apply_window_icon(self) -> None:
        for name in ("conan_hd.ico", "conan.ico"):
            path = resource_path(name)
            if os.path.exists(path):
                try:
                    self.root.iconbitmap(path)
                    return
                except Exception:
                    continue

    def _checkbox(self, parent, text, variable, command=None):
        return tk.Checkbutton(
            parent, text=text, variable=variable, command=command,
            bg=C["bg"], fg="#C9D6E0", activebackground=C["bg"], activeforeground="#FFFFFF",
            selectcolor=C["sunken"], font=self.fonts["body"], bd=0,
            highlightthickness=0, anchor="w",
        )

    # ------------------------------------------------------------------
    # 水印控件（整组随勾选状态启用/禁用）
    # ------------------------------------------------------------------
    def _wm_config(self) -> dict:
        return {
            "text": self.watermark_text.get().strip(),
            "pos": self.wm_position.get(),
            "opacity": max(0, min(100, int(self.wm_opacity.get()))),
            "tile": bool(self.wm_tile.get()),
            "color": self.wm_color.get(),
            "angle": int(self.wm_angle.get()),
            "gap": int(self.wm_gap.get()),
        }

    def _update_wm_widgets(self) -> None:
        on = bool(self.enable_watermark.get())
        tile = on and bool(self.wm_tile.get())
        self.ent_watermark.config(state="normal" if on else "disabled")
        self.scale_opacity.state(["!disabled"] if on else ["disabled"])
        self.scale_angle.state(["!disabled"] if on else ["disabled"])
        # 间距只在平铺模式下有意义
        self.scale_gap.state(["!disabled"] if tile else ["disabled"])
        self.wm_grid.config(cursor="hand2" if on else "")
        self.wm_colors.config(cursor="hand2" if on else "")

        dim = C["text3"] if on else "#3E4E5C"
        dim_gap = C["text3"] if tile else "#3E4E5C"
        for widget in (self.lbl_wm_pos, self.lbl_wm_op, self.lbl_opacity,
                       self.lbl_wm_angle, self.lbl_angle, self.lbl_wm_color):
            widget.config(fg=dim)
        for widget in (self.lbl_wm_gap, self.lbl_gap):
            widget.config(fg=dim_gap)
        self.chk_tile.config(state="normal" if on else "disabled",
                             fg="#C9D6E0" if on else "#3E4E5C")
        self._draw_wm_grid()
        self._draw_wm_colors()

    @staticmethod
    def _extract_exif(raw) -> bytes | None:
        """只带回拍摄信息白名单，GPS / MakerNote 一律丢弃。"""
        try:
            src = raw.getexif()
        except Exception:
            return None
        picked = {tag: src[tag] for tag in EXIF_KEEP_TAGS if tag in src}
        if not picked:
            return None
        try:
            out = Image.Exif()
            for tag, value in picked.items():
                out[tag] = value
            return out.tobytes()
        except Exception:
            return None

    # ------------------------------------------------------------------
    # 预设方案
    # ------------------------------------------------------------------
    def _preset_payload(self) -> dict:
        return {
            "target_format": self.target_format.get(),
            "enable_resize": bool(self.enable_resize.get()),
            "resize_width": self.resize_width.get(),
            "enable_watermark": bool(self.enable_watermark.get()),
            "watermark_text": self.watermark_text.get(),
            "wm_position": self.wm_position.get(),
            "wm_opacity": int(self.wm_opacity.get()),
            "wm_tile": bool(self.wm_tile.get()),
            "wm_color": self.wm_color.get(),
            "wm_angle": int(self.wm_angle.get()),
            "wm_gap": int(self.wm_gap.get()),
            "target_size_enabled": bool(self.enable_target_size.get()),
            "target_kb": self.target_kb.get(),
            "keep_meta": bool(self.keep_meta.get()),
        }

    def _preset_key(self, display: str) -> str:
        """把（可能已翻译的）下拉框显示名映射回内部键。

        要在所有语言的字典里反查，这样换语言后内置预设仍能对上。
        """
        for meta in LANGS.values():
            for zh_name, translated in meta.get("dict", {}).items():
                if translated == display and zh_name in BUILTIN_PRESETS:
                    return zh_name
        return display

    def _refresh_presets(self) -> None:
        current = self._preset_key(self.preset_name.get())
        names = [self.tr(n) for n in BUILTIN_PRESETS] + list(self.user_presets.keys())
        self.cmb_preset.config(values=names)
        # 显示名随语言变，键不变：切换语言后仍选中同一个预设
        display = self.tr(current) if current in BUILTIN_PRESETS else current
        self.preset_name.set(display if display in names else "")

    def _apply_preset(self) -> None:
        name = self.preset_name.get()
        key = self._preset_key(name)
        data = BUILTIN_PRESETS.get(key) or self.user_presets.get(key)
        if not data:
            return
        self.target_format.set(data.get("target_format", self.target_format.get()))
        self.enable_resize.set(bool(data.get("enable_resize", False)))
        self.resize_width.set(str(data.get("resize_width", DEFAULT_MAX_PX)))
        self.enable_watermark.set(bool(data.get("enable_watermark", False)))
        self.watermark_text.set(data.get("watermark_text", self.watermark_text.get()))
        self.wm_position.set(data.get("wm_position", "br"))
        self.wm_opacity.set(int(data.get("wm_opacity", 70)))
        self.wm_tile.set(bool(data.get("wm_tile", False)))
        self.wm_color.set(data.get("wm_color", "#E74C3C"))
        self.wm_angle.set(int(data.get("wm_angle", 0)))
        self.wm_gap.set(int(data.get("wm_gap", 180)))
        self.enable_target_size.set(bool(data.get("target_size_enabled", False)))
        self.target_kb.set(str(data.get("target_kb", "500")))
        self.keep_meta.set(bool(data.get("keep_meta", False)))

        # 把滑杆也拨到对应位置，否则界面显示和实际配置会不一致
        self.scale_opacity.set(self.wm_opacity.get())
        self.scale_angle.set(self.wm_angle.get())
        self.scale_gap.set(self.wm_gap.get())
        self._update_wm_widgets()
        self._update_target_widgets()
        self._on_wm_change()
        self.log(self.trf("已套用预设：{name}", name=name), "dim")

    def _save_preset(self) -> None:
        name = simpledialog.askstring(self.tr("保存预设"), self.tr("给这套参数起个名字："),
                                    parent=self.root)
        if not name or not name.strip():
            return
        name = name.strip()
        if self._preset_key(name) in BUILTIN_PRESETS:
            messagebox.showwarning(self.tr("重名"),
                                    self.trf("「{name}」是内置预设，请换个名字。", name=name))
            return
        self.user_presets[name] = self._preset_payload()
        self._save_settings()
        self._refresh_presets()
        self.preset_name.set(name)
        self.log(self.trf("预设已保存：{name}", name=name), "ok")

    def _delete_preset(self) -> None:
        name = self.preset_name.get()
        if not name:
            messagebox.showinfo(self.tr("提示"), self.tr("请先在下拉框里选择一个预设。"))
            return
        key = self._preset_key(name)
        if key in BUILTIN_PRESETS:
            messagebox.showinfo(self.tr("提示"),
                                    self.tr("内置预设不能删除，但它不会影响你自己保存的预设。"))
            return
        if not messagebox.askyesno(self.tr("删除预设"), self.trf("确定删除「{name}」？", name=name)):
            return
        self.user_presets.pop(key, None)
        self._save_settings()
        self._refresh_presets()
        self.log(self.trf("预设已删除：{name}", name=name), "dim")

    def _update_rename_widgets(self) -> None:
        on = bool(self.rename_enabled.get())
        if hasattr(self, "ent_rename"):
            self.ent_rename.config(state="normal" if on else "disabled")
        if hasattr(self, "lbl_rename"):
            self.lbl_rename.config(fg=C["text3"] if on else "#3E4E5C")

    @staticmethod
    def _render_name_pattern(pattern: str, stem: str, index: int, total: int) -> str:
        """把 {name}/{i}/{n}/{date} 渲染成文件名主体；{i:03} 表示补零到 3 位。"""
        def repl(match):
            token = match.group(1)
            key, _, spec = token.partition(":")
            key = key.strip().lower()
            spec = spec.strip()
            if key == "name":
                value = stem
            elif key == "i":
                value = str(index)
            elif key == "n":
                value = str(total)
            elif key == "date":
                value = time.strftime("%Y%m%d")
            else:
                return match.group(0)      # 未知占位符原样保留，方便用户看出写错了
            if spec.isdigit() and key in ("i", "n"):
                value = value.zfill(int(spec))
            return value

        rendered = re.sub(r"\{([^{}]+)\}", repl, pattern)
        # Windows 文件名非法字符一律替换，避免整批失败
        rendered = re.sub(r'[\\/:*?"<>|]', "_", rendered).strip(" .")
        return rendered or stem

    def _update_target_widgets(self) -> None:
        """目标体积只对 JPG / WEBP 有意义，无损格式下整组禁用。"""
        lossy = self.target_format.get().upper() in ("JPG", "WEBP")
        if hasattr(self, "chk_target"):
            self.chk_target.config(state="normal" if lossy else "disabled",
                                   fg="#C9D6E0" if lossy else "#3E4E5C")
        if hasattr(self, "ent_target"):
            on = lossy and bool(self.enable_target_size.get())
            self.ent_target.config(state="normal" if on else "disabled")
        if hasattr(self, "lbl_target_unit"):
            self.lbl_target_unit.config(fg=C["text3"] if lossy else "#3E4E5C")

    def _target_bytes(self) -> int:
        """返回目标字节数；未启用、格式不支持或数值非法时返回 0。"""
        if not self.enable_target_size.get():
            return 0
        if self.target_format.get().upper() not in ("JPG", "WEBP"):
            return 0
        raw = self.target_kb.get().strip()
        if raw.isdigit() and int(raw) > 0:
            return int(raw) * 1024
        self.log(self.tr("目标体积数值无效，本次已忽略该选项。"), "err")
        return 0

    def _on_wm_toggle(self) -> None:
        self._update_wm_widgets()
        self._on_wm_change()

    def _on_wm_toggle_tile(self) -> None:
        self._update_wm_widgets()
        self._on_wm_change()

    def _on_angle(self, value) -> None:
        angle = int(round(float(value)))
        self.wm_angle.set(angle)
        if hasattr(self, "lbl_angle"):
            self.lbl_angle.config(text=f"{angle}°")
        if self.enable_watermark.get():
            self._on_wm_change()

    def _on_gap(self, value) -> None:
        gap = max(110, min(320, int(round(float(value)))))
        self.wm_gap.set(gap)
        if hasattr(self, "lbl_gap"):
            self.lbl_gap.config(text=f"{gap}%")
        if self.enable_watermark.get() and self.wm_tile.get():
            self._on_wm_change()

    def _draw_wm_colors(self) -> None:
        canvas = self.wm_colors
        canvas.delete("all")
        enabled = bool(self.enable_watermark.get())
        current = self.wm_color.get().upper()
        self._color_cells = []
        x = 1
        for name, value in WM_COLORS:
            box = 16
            selected = value.upper() == current
            outline = C["red"] if selected else (C["line"] if enabled else "#1A2632")
            canvas.create_rectangle(x, 1, x + box, 1 + box, fill=value, outline=outline,
                                    width=2 if selected else 1)
            self._color_cells.append((value, x, 1, x + box, 1 + box))
            x += box + 6

    def _on_wm_color_click(self, event) -> None:
        if not self.enable_watermark.get():
            return
        for value, x0, y0, x1, y1 in getattr(self, "_color_cells", []):
            if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                self.wm_color.set(value)
                self._draw_wm_colors()
                self._on_wm_change()
                return

    def _on_wm_change(self) -> None:
        """任一水印参数变化：刷新案卷卡缩略图，做到所见即所得。"""
        self._render_watermark_preview()

    def _draw_wm_grid(self) -> None:
        canvas = self.wm_grid
        canvas.delete("all")
        enabled = bool(self.enable_watermark.get())
        cell, gap, pad = 12, 3, 3
        current = self.wm_position.get()
        self._grid_cells = []
        for index, key in enumerate(WM_POSITION_ORDER):
            row, col = divmod(index, 3)
            x = pad + col * (cell + gap)
            y = pad + row * (cell + gap)
            selected = (key == current)
            if selected:
                fill = C["red"] if enabled else "#4A3A3A"
            else:
                fill = C["hover"] if enabled else "#1A2632"
            canvas.create_rectangle(x, y, x + cell, y + cell, fill=fill,
                                    outline=C["line"] if enabled else "#1A2632")
            self._grid_cells.append((key, x, y, x + cell, y + cell))

    def _on_wm_grid_click(self, event) -> None:
        if not self.enable_watermark.get():
            return
        for key, x0, y0, x1, y1 in getattr(self, "_grid_cells", []):
            if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                self.wm_position.set(key)
                self._draw_wm_grid()
                self._on_wm_change()
                return

    def _on_opacity(self, value) -> None:
        percent = max(0, min(100, int(float(value))))
        self.wm_opacity.set(percent)
        if hasattr(self, "lbl_opacity"):
            self.lbl_opacity.config(text=f"{percent}%")
        if self.enable_watermark.get():
            self._on_wm_change()

    def _render_watermark_preview(self) -> None:
        """基于已缓存的缩略图重绘水印，避免每次拖动滑杆都重新读盘解码。"""
        base = getattr(self, "_preview_base", None)
        if not base:
            return
        path, image = base
        if path != self._selected_path():
            return
        frame = image
        if self.enable_watermark.get():
            cfg = self._wm_config()
            if cfg["text"]:
                frame = self._apply_watermark(image.convert("RGBA"), cfg).convert("RGB")
        self.detail_photo = ImageTk.PhotoImage(frame)
        self.thumb_label.config(image=self.detail_photo, text="")

    # ------------------------------------------------------------------
    # 界面
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        outer = tk.Frame(self.root, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        rail = tk.Frame(outer, bg=C["rail"], width=160)
        rail.pack(side="left", fill="y")
        rail.pack_propagate(False)

        self.canvas_char = tk.Canvas(rail, bg=C["rail"], height=172, highlightthickness=0)
        self.canvas_char.pack(fill="x", pady=(18, 0))
        self._draw_viewfinder()
        # 构造阶段 canvas 宽度尚未确定（winfo_width 返回 1），必须等真实布局后再画一次，
        # 否则图标与文字会以 x=0.5 居中、被两侧裁掉。
        self.canvas_char.bind("<Configure>", self._on_vf_resize)

        ttk.Button(rail, text="更换调查员", command=self.load_character_image).pack(
            pady=(0, 0), padx=8, fill="x")

        tk.Label(rail, text="SYSTEM STATUS", bg=C["rail"], fg=C["text3"],
                 font=self.fonts["tiny"]).pack(anchor="w", padx=16, pady=(26, 4))
        self.lbl_status = tk.Label(rail, text="WAITING", bg=C["rail"], fg=C["blue"],
                                   font=("Consolas", 10, "bold"))
        self.lbl_status.pack(anchor="w", padx=16)
        self.lbl_progress = tk.Label(rail, text="", bg=C["rail"], fg=C["text3"],
                                     font=self.fonts["tiny"], justify="left")
        self.lbl_progress.pack(anchor="w", padx=16, pady=(6, 0))

        tk.Label(rail, text="FOLDER WATCH", bg=C["rail"], fg=C["text3"],
                 font=self.fonts["tiny"]).pack(anchor="w", padx=16, pady=(20, 2))
        self.lbl_watch = tk.Label(rail, text="未开启", bg=C["rail"], fg=C["text3"],
                                  font=self.fonts["small"], wraplength=128, justify="left")
        self.lbl_watch.pack(anchor="w", padx=16)
        self.btn_watch_dir = ttk.Button(rail, text="选择目录", command=self._choose_watch_dir)
        self.btn_watch_dir.pack(fill="x", padx=8, pady=(6, 4))
        self.btn_watch = ttk.Button(rail, text="开启监听", command=self._toggle_watch)
        self.btn_watch.pack(fill="x", padx=8)

        ttk.Button(rail, text="关于", command=self.open_about).pack(
            side="bottom", fill="x", padx=8, pady=(0, 4))
        self.btn_open_folder = ttk.Button(rail, text="打开案件目录", command=self.open_output_folder,
                                          state="disabled")
        self.btn_open_folder.pack(side="bottom", fill="x", padx=8, pady=(0, 16))

        content = tk.Frame(outer, bg=C["bg"])
        content.pack(side="left", fill="both", expand=True, padx=(18, 0))
        self.content = content

        header = tk.Frame(content, bg=C["bg"])
        header.pack(fill="x", pady=(0, 6))
        tk.Label(header, text="CASE FILE", font=self.fonts["h1"], bg=C["bg"],
                 fg=C["text"]).pack(side="left")
        # 版本徽标兼作「关于」入口：点它能看构建信息、签名状态和校验和
        self.lbl_version = tk.Label(header, text=APP_VERSION, bg=C["blue"], fg="white",
                                    padx=6, font=self.fonts["tiny"], cursor="hand2")
        self.lbl_version.pack(side="left", padx=10)
        self.lbl_version.bind("<Button-1>", lambda e: self.open_about())
        # 语言切换：下拉里的选项由注册表生成，加语言不用改这里
        self.cmb_lang = ttk.Combobox(
            header, values=[meta["label"] for meta in LANGS.values()],
            state="readonly", width=8, font=self.fonts["small"])
        self.cmb_lang.pack(side="left", padx=(16, 0))
        self.cmb_lang.set(LANGS.get(self.lang, LANGS["zh"])["label"])
        self.cmb_lang.bind("<<ComboboxSelected>>", self._on_lang_change)
        tk.Label(header, textvariable=self.case_no, bg=C["bg"], fg=C["text3"],
                 font=self.fonts["mono"]).pack(side="right")

        self._section(content, "01 · EVIDENCE LIST  证据清单", pady=(4, 4))

        bar = tk.Frame(content, bg=C["bg"])
        bar.pack(fill="x", pady=(0, 8))
        self.btn_add = ttk.Button(bar, text="浏览并挑选图片", command=self.select_files)
        self.btn_add.pack(side="left", padx=(0, 6))
        self.btn_folder = ttk.Button(bar, text="导入目录", command=self.select_folder)
        self.btn_folder.pack(side="left", padx=(0, 6))
        self.btn_remove = ttk.Button(bar, text="移除选中", command=self.remove_selected)
        self.btn_remove.pack(side="left")

        body = tk.Frame(content, bg=C["bg"])
        body.pack(fill="x")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, minsize=270, weight=0)
        body.grid_rowconfigure(0, weight=1)

        tree_wrap = tk.Frame(body, bg=C["sunken"])
        tree_wrap.grid(row=0, column=0, sticky="nsew")

        self.tree = ttk.Treeview(tree_wrap, columns=("size", "state"), show="tree headings",
                                 selectmode="extended", height=7)
        self.tree.heading("#0", text="文件名", anchor="w")
        self.tree.heading("size", text="尺寸", anchor="e")
        self.tree.heading("state", text="状态", anchor="w")
        self.tree.column("#0", width=260, minwidth=150, stretch=True, anchor="w")
        self.tree.column("size", width=96, minwidth=80, stretch=False, anchor="e")
        self.tree.column("state", width=92, minwidth=72, stretch=False, anchor="w")

        tvsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tvsb.set)
        tvsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        for code, fg in ((0, "#C9D6E0"), (1, C["amber"]), (2, C["green"]), (3, C["red"])):
            self.tree.tag_configure(str(code), foreground=fg)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Delete>", lambda e: self.remove_selected())
        self.tree.bind("<BackSpace>", lambda e: self.remove_selected())
        self.tree.bind("<Double-1>", lambda e: self.open_preview())
        self._create_context_menu()

        self._build_paper_card(body)

        cells_row = tk.Frame(content, bg=C["bg"])
        cells_row.pack(fill="x", pady=(8, 0))
        tk.Label(cells_row, text="证物格", bg=C["bg"], fg=C["text3"],
                 font=self.fonts["tiny"]).pack(side="left")
        self.lbl_cells = tk.Label(cells_row, text="0 项", bg=C["bg"], fg=C["text3"],
                                  font=self.fonts["tiny"])
        self.lbl_cells.pack(side="left", padx=(6, 0))
        tk.Label(cells_row, text="绿=完成  红=失败  黄=处理中  点击查看", bg=C["bg"],
                 fg=C["text3"], font=self.fonts["tiny"]).pack(side="right")

        self.cells = tk.Canvas(content, height=22, bg=C["bg"], highlightthickness=0, bd=0)
        self.cells.pack(fill="x", pady=(3, 0))
        self.cells.bind("<Configure>", lambda e: self._draw_cells())
        self.cells.bind("<Button-1>", self._on_cell_click)
        self.cells.bind("<Motion>", self._on_cell_hover)
        self.cells.bind("<Leave>", lambda e: self.cells.configure(cursor=""))

        sec = tk.Frame(content, bg=C["bg"])
        sec.pack(fill="x", pady=(10, 4))
        tk.Label(sec, text="02 · ANALYSIS CONFIG  分析配置", font=self.fonts["tiny"],
                 fg=C["blue"], bg=C["bg"]).pack(side="left")
        self.btn_preset_del = ttk.Button(sec, text="删除", width=6, command=self._delete_preset)
        self.btn_preset_del.pack(side="right")
        ttk.Button(sec, text="另存", width=6, command=self._save_preset).pack(
            side="right", padx=(0, 4))
        self.cmb_preset = ttk.Combobox(sec, textvariable=self.preset_name, width=14,
                                       state="readonly")
        self.cmb_preset.pack(side="right", padx=(6, 4))
        self.cmb_preset.bind("<<ComboboxSelected>>", lambda e: self._apply_preset())
        tk.Label(sec, text="预设", font=self.fonts["tiny"], fg=C["text3"],
                 bg=C["bg"]).pack(side="right")

        opts = tk.Frame(content, bg=C["bg"])
        opts.pack(fill="x")

        tk.Label(opts, text="Format", bg=C["bg"], fg=C["text2"],
                 font=self.fonts["body"]).grid(row=0, column=0, sticky="w")
        self.cmb_format = ttk.Combobox(opts, values=list(TARGET_FORMATS),
                                       textvariable=self.target_format, width=7, state="readonly")
        self.cmb_format.grid(row=0, column=1, padx=(8, 18), sticky="w")
        self.cmb_format.bind("<<ComboboxSelected>>", lambda e: self._update_target_widgets())

        self._checkbox(opts, "Resize", self.enable_resize).grid(row=0, column=2, sticky="w")
        vcmd = (self.root.register(self._validate_digits), "%P")
        ttk.Entry(opts, textvariable=self.resize_width, width=6,
                  validate="key", validatecommand=vcmd).grid(row=0, column=3, padx=(6, 0), sticky="w")
        tk.Label(opts, text="px 等比", bg=C["bg"], fg=C["text3"],
                 font=self.fonts["tiny"]).grid(row=0, column=4, padx=(4, 18), sticky="w")

        # 目标体积：独立开关，与格式联动（无损格式下自动禁用）
        self.chk_target = self._checkbox(opts, "目标体积 ≤", self.enable_target_size,
                                         command=self._update_target_widgets)
        self.chk_target.grid(row=0, column=5, sticky="w")
        self.ent_target = ttk.Entry(opts, textvariable=self.target_kb, width=5,
                                    validate="key", validatecommand=vcmd)
        self.ent_target.grid(row=0, column=6, padx=(6, 2), sticky="w")
        self.lbl_target_unit = tk.Label(opts, text="KB", bg=C["bg"], fg=C["text3"],
                                        font=self.fonts["tiny"])
        self.lbl_target_unit.grid(row=0, column=7, padx=(2, 0), sticky="w")

        # --- 水印：整组控件只在勾选后可用，未勾选时全部置灰 ---
        self.chk_watermark = self._checkbox(opts, "Watermark", self.enable_watermark,
                                            command=self._on_wm_toggle)
        self.chk_watermark.grid(row=1, column=2, sticky="w", pady=(8, 0))

        self.ent_watermark = ttk.Entry(opts, textvariable=self.watermark_text, width=30)
        self.ent_watermark.grid(row=1, column=3, padx=(6, 0), pady=(8, 0), sticky="w")
        self.ent_watermark.bind("<KeyRelease>", lambda e: self._on_wm_change())

        self.lbl_wm_color = tk.Label(opts, text="颜色", bg=C["bg"], fg=C["text3"],
                                     font=self.fonts["tiny"])
        self.lbl_wm_color.grid(row=1, column=4, padx=(18, 4), pady=(8, 0), sticky="w")
        self.wm_colors = tk.Canvas(opts, width=110, height=18, bg=C["bg"],
                                   highlightthickness=0, bd=0, cursor="hand2")
        self.wm_colors.grid(row=1, column=5, columnspan=3, pady=(8, 0), sticky="w")
        self.wm_colors.bind("<Button-1>", self._on_wm_color_click)

        self.wm_tools = tk.Frame(opts, bg=C["bg"])
        self.wm_tools.grid(row=2, column=1, columnspan=7, sticky="w", pady=(6, 0), padx=(8, 0))

        self.lbl_wm_pos = tk.Label(self.wm_tools, text="位置", bg=C["bg"], fg=C["text3"],
                                   font=self.fonts["tiny"])
        self.lbl_wm_pos.pack(side="left")
        self.wm_grid = tk.Canvas(self.wm_tools, width=48, height=48, bg=C["bg"],
                                 highlightthickness=0, bd=0, cursor="hand2")
        self.wm_grid.pack(side="left", padx=(6, 14))
        self.wm_grid.bind("<Button-1>", self._on_wm_grid_click)

        self.lbl_wm_op = tk.Label(self.wm_tools, text="透明度", bg=C["bg"], fg=C["text3"],
                                  font=self.fonts["tiny"])
        self.lbl_wm_op.pack(side="left")
        # 标签必须先于 Scale 创建：ttk.Scale 在 set() 时就会触发 command 回调
        self.lbl_opacity = tk.Label(self.wm_tools, text=f"{self.wm_opacity.get()}%",
                                    bg=C["bg"], fg=C["text2"], font=self.fonts["tiny"], width=4)
        self.scale_opacity = ttk.Scale(self.wm_tools, from_=0, to=100, orient="horizontal",
                                       length=96, command=self._on_opacity)
        self.scale_opacity.set(self.wm_opacity.get())
        self.scale_opacity.pack(side="left", padx=(6, 4))
        self.lbl_opacity.pack(side="left")

        self.chk_tile = self._checkbox(self.wm_tools, "平铺", self.wm_tile,
                                       command=self._on_wm_toggle_tile)
        self.chk_tile.pack(side="left", padx=(12, 0))

        self.lbl_wm_angle = tk.Label(self.wm_tools, text="角度", bg=C["bg"], fg=C["text3"],
                                     font=self.fonts["tiny"])
        self.lbl_wm_angle.pack(side="left", padx=(16, 0))
        self.lbl_angle = tk.Label(self.wm_tools, text=f"{self.wm_angle.get()}°",
                                  bg=C["bg"], fg=C["text2"], font=self.fonts["tiny"], width=4)
        self.scale_angle = ttk.Scale(self.wm_tools, from_=-45, to=45, orient="horizontal",
                                     length=84, command=self._on_angle)
        self.scale_angle.set(self.wm_angle.get())
        self.scale_angle.pack(side="left", padx=(6, 4))
        self.lbl_angle.pack(side="left")

        self.lbl_wm_gap = tk.Label(self.wm_tools, text="间距", bg=C["bg"], fg=C["text3"],
                                   font=self.fonts["tiny"])
        self.lbl_wm_gap.pack(side="left", padx=(16, 0))
        self.lbl_gap = tk.Label(self.wm_tools, text=f"{self.wm_gap.get()}%",
                                bg=C["bg"], fg=C["text2"], font=self.fonts["tiny"], width=4)
        self.scale_gap = ttk.Scale(self.wm_tools, from_=110, to=320, orient="horizontal",
                                   length=84, command=self._on_gap)
        self.scale_gap.set(self.wm_gap.get())
        self.scale_gap.pack(side="left", padx=(6, 4))
        self.lbl_gap.pack(side="left")

        meta_row = tk.Frame(opts, bg=C["bg"])
        meta_row.grid(row=3, column=0, columnspan=8, sticky="w", pady=(6, 0))

        self.chk_rename = self._checkbox(meta_row, "重命名", self.rename_enabled,
                                         command=self._update_rename_widgets)
        self.chk_rename.pack(side="left")
        self.ent_rename = ttk.Entry(meta_row, textvariable=self.rename_pattern, width=18)
        self.ent_rename.pack(side="left", padx=(6, 6))
        self.lbl_rename = tk.Label(meta_row, text="可用 {name} {i} {n} {date}，如 CASE-{i:03}",
                                   bg=C["bg"], fg=C["text3"], font=self.fonts["tiny"])
        self.lbl_rename.pack(side="left")

        # 默认清空全部元数据；勾上只带回拍摄信息，GPS 无论如何都不保留
        self.chk_meta = self._checkbox(meta_row, "保留拍摄信息（不含 GPS）", self.keep_meta)
        self.chk_meta.pack(side="left", padx=(22, 0))
        self._update_rename_widgets()

        self._draw_wm_grid()
        self._update_wm_widgets()
        self._update_target_widgets()

        out_row = tk.Frame(content, bg=C["bg"])
        out_row.pack(fill="x", pady=(10, 0))
        tk.Label(out_row, text="输出到", bg=C["bg"], fg=C["text2"],
                 font=self.fonts["body"]).pack(side="left")
        tk.Label(out_row, textvariable=self.output_hint, bg=C["bg"], fg=C["text3"],
                 font=self.fonts["tiny"], anchor="w").pack(
            side="left", padx=(8, 6), fill="x", expand=True)
        ttk.Button(out_row, text="默认", command=self.reset_output_dir).pack(side="right")
        self.btn_choose_out = ttk.Button(out_row, text="选择输出目录…",
                                         command=self.choose_output_dir)
        self.btn_choose_out.pack(side="right", padx=(0, 4))

        run_row = tk.Frame(content, bg=C["bg"])
        run_row.pack(fill="x", pady=(10, 6))
        self.btn_run = ttk.Button(run_row, text="开始推理", style="Red.TButton",
                                  command=self.start_thread)
        self.btn_run.pack(side="left", fill="x", expand=True)
        self.btn_cancel = ttk.Button(run_row, text="取消", command=self.cancel_processing,
                                     state="disabled")
        self.btn_cancel.pack(side="left", padx=(6, 0))
        self.btn_retry = ttk.Button(run_row, text="重试失败", command=self.retry_failed,
                                    state="disabled")
        self.btn_retry.pack(side="left", padx=(6, 0))
        self.btn_report = ttk.Button(run_row, text="导出报告", command=self.open_report,
                                     state="disabled")
        self.btn_report.pack(side="left", padx=(6, 0))

        log_wrap = tk.Frame(content, bg=C["sunken"])
        log_wrap.pack(fill="both", expand=True)
        self.log_area = tk.Text(log_wrap, height=4, bg=C["sunken"], fg=C["text2"],
                                font=self.fonts["mono"], relief="flat", bd=0,
                                padx=6, pady=4, insertbackground=C["text"], wrap="char")
        log_vsb = ttk.Scrollbar(log_wrap, orient="vertical", command=self.log_area.yview)
        self.log_area.configure(yscrollcommand=log_vsb.set)
        log_vsb.pack(side="right", fill="y")
        self.log_area.pack(side="left", fill="both", expand=True, padx=(10, 6), pady=6)

        self.log_area.tag_config("ok", foreground=C["green"])
        self.log_area.tag_config("err", foreground=C["red"])
        self.log_area.tag_config("dim", foreground=C["text3"])
        self.log_area.config(state="disabled")
        self.log("TERMINAL READY. WAITING FOR EVIDENCE...", "dim")

    def _section(self, parent, text: str, pady=(8, 2)) -> None:
        tk.Label(parent, text=text, font=self.fonts["tiny"], fg=C["blue"],
                 bg=C["bg"]).pack(anchor="w", pady=pady)

    # ------------------------------------------------------------------
    # 取景框
    # ------------------------------------------------------------------
    def _on_vf_resize(self, event) -> None:
        if abs(event.width - self._vf_width) > 2:
            self._vf_width = event.width
            self._draw_viewfinder()

    def _draw_viewfinder(self, image_path: str | None = None) -> None:
        self.canvas_char.delete("all")
        if image_path:
            self._char_source = image_path
        cw = max(self.canvas_char.winfo_width(), 140)
        cx = cw / 2
        box, cy = 96, 76
        half = box / 2

        source = self._char_source or resource_path(os.path.join("assets", "app_icon_512.png"))
        drawn = False
        if os.path.exists(source):
            try:
                with Image.open(source) as raw:
                    pic = raw.convert("RGBA")
                side = max(pic.size)
                canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
                canvas.paste(pic, ((side - pic.width) // 2, (side - pic.height) // 2))
                canvas = canvas.resize((int(box - 10), int(box - 10)), Image.LANCZOS)
                self.char_photo = ImageTk.PhotoImage(canvas)
                self.canvas_char.create_image(cx, cy, image=self.char_photo, anchor="center")
                drawn = True
            except Exception:
                drawn = False

        b, ln = half + 8, 14
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            x, y = cx + dx * b, cy + dy * b
            self.canvas_char.create_line(x, y, x - dx * ln, y, fill=C["red"], width=2)
            self.canvas_char.create_line(x, y, x, y - dy * ln, fill=C["red"], width=2)

        if not drawn:
            self.canvas_char.create_text(cx, cy, text="NO ICON", fill=C["text3"],
                                         font=("Consolas", 8))

        self.canvas_char.create_text(cx, 142, text="EDOGAWA CONAN", fill=C["text2"],
                                     font=("Segoe UI", 8, "bold"))
        self.canvas_char.create_text(cx, 157, text="INTELLIGENCE TERMINAL", fill=C["text3"],
                                     font=("Segoe UI", 7))

    def load_character_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title=self.tr("选择调查员图片"), initialdir=self.last_open_dir,
            filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if not file_path:
            return
        self.last_open_dir = os.path.dirname(file_path)
        self._draw_viewfinder(file_path)
        self.log(f"INVESTIGATOR UPDATED: {os.path.basename(file_path)}", "ok")

    # ------------------------------------------------------------------
    # 案卷纸卡片
    # ------------------------------------------------------------------
    def _build_paper_card(self, parent) -> None:
        card = tk.Frame(parent, bg=C["paper"], width=270)
        card.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        self.card = card

        head = tk.Frame(card, bg=C["paper"], height=24)
        head.pack(fill="x", padx=10, pady=(6, 0))
        head.pack_propagate(False)
        tk.Label(head, text="案卷 · FORENSIC", bg=C["paper"], fg=C["paper_muted"],
                 font=self.fonts["tiny"]).pack(side="left")
        tk.Label(head, text="密级 · 机密", bg=C["paper"], fg=C["stamp"],
                 font=self.fonts["tiny"]).pack(side="right")
        tk.Frame(card, height=1, bg=C["paper_line"]).pack(fill="x", padx=10, pady=(4, 0))

        thumb_holder = tk.Frame(card, bg=C["sunken"], height=80)
        thumb_holder.pack(fill="x", padx=10, pady=(8, 0))
        thumb_holder.pack_propagate(False)
        self.thumb_holder = thumb_holder
        self.thumb_label = tk.Label(thumb_holder, bg=C["sunken"], fg=C["text3"],
                                    text="NO EVIDENCE SELECTED", font=self.fonts["tiny"],
                                    cursor="hand2")
        self.thumb_label.pack(expand=True)
        self.thumb_label.bind("<Button-1>", lambda e: self.open_preview())

        meta = tk.Frame(card, bg=C["paper"])
        meta.pack(fill="x", padx=10, pady=(8, 0))
        self.detail_vars: dict[str, tk.StringVar] = {}
        rows = (
            ("name", "文件名"), ("kind", "类型"), ("size", "分辨率"), ("bytes", "体积"),
            ("shot", "拍摄"), ("device", "设备"), ("hash", "SHA256"),
        )
        for row, (key, label) in enumerate(rows):
            # 不写死 width：定宽 5 字符会把 "SHA256" 截成 "SHA25"
            tk.Label(meta, text=label, bg=C["paper"], fg=C["paper_muted"],
                     font=self.fonts["tiny"], anchor="w").grid(
                row=row, column=0, sticky="nw")
            var = tk.StringVar(value="—")
            self.detail_vars[key] = var
            tk.Label(meta, textvariable=var, bg=C["paper"], fg=C["paper_text"],
                     font=self.fonts["tiny"], anchor="w", justify="left",
                     wraplength=180).grid(row=row, column=1, sticky="w", padx=(6, 0))

        self.btn_preview = ttk.Button(card, text="查看成品大图", style="Stamp.TButton",
                                      command=self.open_preview, state="disabled")
        self.btn_preview.pack(side="bottom", fill="x", padx=10, pady=(4, 8))
        self.btn_hash = ttk.Button(card, text="计算 SHA256", style="Paper.TButton",
                                   command=self._compute_hash, state="disabled")
        self.btn_hash.pack(side="bottom", fill="x", padx=10, pady=(4, 0))

        # 印章压在缩略图右下角：像把章盖在案卷照片上，也不遮挡任何字段
        self._stamp_photo = ImageTk.PhotoImage(make_stamp("TOP SECRET", size=13, angle=10))
        self.stamp_label = tk.Label(thumb_holder, image=self._stamp_photo, bg=C["sunken"], bd=0)

    # ------------------------------------------------------------------
    # 文件操作
    # ------------------------------------------------------------------
    def select_files(self) -> None:
        patterns = " ".join(f"*{ext}" for ext in SUPPORTED_EXTS)
        files = filedialog.askopenfilenames(
            title=self.tr("浏览并挑选图片 (按住 Ctrl 多选)"),
            initialdir=self.last_open_dir,
            filetypes=[("Images", patterns), ("All Files", "*.*")])
        if not files:
            return
        self.last_open_dir = os.path.dirname(files[0])
        self._add_files(list(files))

    def _scan_dir(self, path: str) -> list[str]:
        try:
            names = sorted(os.listdir(path))
        except OSError as exc:
            self.log(self.trf("[ERROR] 无法读取目录: {err}", err=exc), "err")
            return []
        return [os.path.join(path, n) for n in names
                if n.lower().endswith(SUPPORTED_EXTS) and os.path.isfile(os.path.join(path, n))]

    def select_folder(self) -> None:
        path = filedialog.askdirectory(initialdir=self.last_open_dir)
        if not path:
            return
        self.last_open_dir = path
        self._add_files(self._scan_dir(path), label=f"Imported folder: {path}")

    def _add_files(self, files: list[str], label: str = "") -> None:
        existing = set(self.source_files)
        new_files = [f for f in files if f not in existing]
        if not new_files:
            self.log(self.tr("所选文件已在清单中，已跳过。"), "dim")
            return
        self.source_files.extend(new_files)
        for f in new_files:
            self.status[f] = 0
        self._refresh_tree()
        self.log(self.trf("{label} +{n} (共 {total} 项)",
                            label=label or "Added", n=len(new_files),
                            total=len(self.source_files)))

    def remove_selected(self) -> None:
        if self._running:
            self.log(self.tr("处理进行中，暂不能修改清单。"), "err")
            return
        selected = self.tree.selection()
        if not selected:
            return
        for path in selected:
            if path in self.source_files:
                self.source_files.remove(path)
                self.status.pop(path, None)
                self.results.pop(path, None)
                self.sizes.pop(path, None)
        self._refresh_tree()
        self.log(f"Removed {len(selected)} items.", "dim")

    def clear_list(self) -> None:
        if self._running:
            self.log(self.tr("处理进行中，暂不能修改清单。"), "err")
            return
        self.source_files = []
        self.status.clear()
        self.results.clear()
        self.sizes.clear()
        self._refresh_tree()
        self.log("EVIDENCE LIST CLEARED.", "dim")

    def _refresh_tree(self) -> None:
        """重建清单。切语言、加文件、删文件都走这里。

        必须按 status/sizes 里记录的真实状态渲染：这个函数以前写死成"待处理"，
        加文件时看着没问题，但 v5.13 起切语言也调用它，结果处理完的图会全部
        退回"待处理"、尺寸列变空、右侧详情卡被清空。
        """
        selected = self._selected_path()
        self.tree.delete(*self.tree.get_children())
        for path in self.source_files:
            code = self.status.get(path, 0)
            self.tree.insert("", "end", iid=path,
                             text=os.path.basename(path),
                             values=(self.sizes.get(path, ""), self.tr(STATUS_TEXT[code])),
                             tags=(str(code),))
        count = len(self.source_files)
        if not self._running:
            self.lbl_status.config(text=f"READY · {count}", fg=C["blue"])
        self.case_no.set(f"CASE No. 04869-{count:02d}")
        # 选中的文件还在清单里就恢复选中与详情；被删掉了才清空
        if selected and selected in self.source_files:
            self.tree.selection_set(selected)
            self._show_detail(selected)
        else:
            self._clear_detail()
        self._draw_cells()
        self._refresh_output_hint()

    def _mark(self, path: str, code: int, size_text: str = "") -> None:
        """主线程回调：更新某一行的状态与证物格。"""
        self.status[path] = code
        if size_text:
            self.sizes[path] = size_text
        if self.tree.exists(path):
            values = self.tree.item(path, "values")
            new_size = size_text or (values[0] if values else "")
            self.tree.item(path, values=(new_size, self.tr(STATUS_TEXT[code])), tags=(str(code),))
            if code == 1:
                self.tree.see(path)
        self._draw_cells()

    # ------------------------------------------------------------------
    # 证物格
    # ------------------------------------------------------------------
    def _draw_cells(self) -> None:
        self.cells.delete("all")
        self._cell_rects.clear()
        width = max(self.cells.winfo_width(), 10)
        total = len(self.source_files)
        self.lbl_cells.config(text=self.trf("{n} 项", n=total))
        if total == 0:
            self.cells.create_text(2, 11, anchor="w", text=self.tr("尚无证物"),
                                   fill=C["text3"], font=self.fonts["tiny"])
            return

        limit = 120
        shown = self.source_files[:limit]
        gap = 4 if len(shown) <= 40 else 3
        cell_w = (width - gap * max(len(shown) - 1, 1)) / max(len(shown), 1)
        # 文件少时不要把方格拉成一条色带，18px 封顶后左对齐
        cell_w = max(6.0, min(cell_w, 18.0))
        cell_h, y = 14, 4
        for i, path in enumerate(shown):
            x = i * (cell_w + gap)
            code = self.status.get(path, 0)
            fill = STATUS_COLORS.get(code, STATUS_COLORS[0])
            self.cells.create_rectangle(x, y, x + cell_w, y + cell_h, fill=fill,
                                        outline="", width=0)
            self._cell_rects.append((x, y, x + cell_w, y + cell_h, path))
        if total > limit:
            self.cells.create_text(width - 2, y + cell_h / 2, anchor="e",
                                   text=f"+{total - limit}", fill=C["text3"],
                                   font=self.fonts["tiny"])

    def _cell_at(self, x: float, y: float) -> str | None:
        for x0, y0, x1, y1, path in self._cell_rects:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return path
        return None

    def _on_cell_hover(self, event) -> None:
        path = self._cell_at(event.x, event.y)
        self.cells.configure(cursor="hand2" if path else "")
        self.cells.delete("tip")
        if path:
            x = max(4, min(event.x, self.cells.winfo_width() - 150))
            self.cells.create_text(x, 2, anchor="nw",
                                   text=f"{os.path.basename(path)} · "
                                        f"{self.tr(STATUS_TEXT[self.status.get(path, 0)])}",
                                   fill=C["text2"], font=self.fonts["tiny"], tags="tip")

    def _on_cell_click(self, event) -> None:
        path = self._cell_at(event.x, event.y)
        if not path:
            return
        if self.tree.exists(path):
            self.tree.selection_set(path)
            self.tree.focus(path)
            self.tree.see(path)
            self._show_detail(path)
        if self.status.get(path) == 2 and path in self.results:
            self.open_preview()

    # ------------------------------------------------------------------
    # 案卷卡内容
    # ------------------------------------------------------------------
    def _on_select(self, _event=None) -> None:
        path = self._selected_path()
        if not path:
            self._clear_detail()
            return
        self._show_detail(path)

    def _selected_path(self) -> str | None:
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _clear_detail(self) -> None:
        for var in getattr(self, "detail_vars", {}).values():
            var.set("—")
        self._preview_base = None
        if hasattr(self, "thumb_label"):
            self.detail_photo = None
            self.thumb_label.config(image="", text="NO EVIDENCE SELECTED")
        if hasattr(self, "btn_hash"):
            self.btn_hash.config(state="disabled")
        if hasattr(self, "btn_preview"):
            self.btn_preview.config(state="disabled")
        # 空态不盖印章，否则会压住 "NO EVIDENCE SELECTED"
        if hasattr(self, "stamp_label"):
            self.stamp_label.place_forget()

    def _show_detail(self, path: str) -> None:
        if not hasattr(self, "detail_vars"):
            return
        self.detail_vars["name"].set(os.path.basename(path))
        self.detail_vars["hash"].set(self.tr("未计算"))
        preview_source = self.results.get(path, path)
        self.btn_preview.config(state="normal" if os.path.exists(preview_source) else "disabled")

        try:
            stat = os.stat(path)
            self.detail_vars["bytes"].set(human_size(stat.st_size))
            self.detail_vars["shot"].set(
                time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime))
                + self.tr(" (文件)"))
        except OSError:
            self.detail_vars["bytes"].set("—")

        try:
            with Image.open(path) as raw:
                ext = (raw.format or os.path.splitext(path)[1].lstrip(".")).upper()
                self.detail_vars["kind"].set(f"{ext} · {raw.mode}")
                self.detail_vars["size"].set(f"{raw.width} × {raw.height}")
                exif = raw.getexif()
                shot = exif.get(36867) or exif.get(306)
                if shot:
                    self.detail_vars["shot"].set(str(shot).replace(":", "-", 2))
                make, model = exif.get(271, ""), exif.get(272, "")
                device = " ".join(x for x in (str(make).strip(), str(model).strip()) if x)
                self.detail_vars["device"].set(device or "—")

                try:
                    raw.draft("RGB", (272, 160))
                except Exception:
                    pass
                preview = raw.convert("RGB")
                preview.thumbnail((248, 80), Image.Resampling.LANCZOS)
                self._preview_base = (path, preview)
            self._render_watermark_preview()
            self.stamp_label.place(relx=1.0, rely=1.0, x=-4, y=-2, anchor="se")
            self.btn_hash.config(state="normal")
        except Exception as exc:
            self.detail_vars["kind"].set(self.tr("无法读取"))
            self.detail_vars["size"].set("—")
            self.detail_vars["device"].set("—")
            self.thumb_label.config(image="", text="PREVIEW UNAVAILABLE")
            self.btn_hash.config(state="disabled")
            self.log(self.trf("[WARN] 预览失败 {name}: {err}",
                                    name=os.path.basename(path), err=exc), "err")

    def _compute_hash(self) -> None:
        path = self._selected_path()
        if not path:
            return
        self.detail_vars["hash"].set(self.tr("计算中..."))
        self.btn_hash.config(state="disabled")

        def worker():
            try:
                digest = hashlib.sha256()
                with open(path, "rb") as fp:
                    for chunk in iter(lambda: fp.read(1 << 20), b""):
                        digest.update(chunk)
                self._post(self._set_hash_result, digest.hexdigest()[:32], path)
            except Exception as exc:
                self._post(self._set_hash_result, self.trf("失败: {err}", err=exc), path)

        threading.Thread(target=worker, daemon=True).start()

    def _set_hash_result(self, value: str, path: str) -> None:
        if self._selected_path() == path:
            self.detail_vars["hash"].set(value)
            self.btn_hash.config(state="normal")

    # ------------------------------------------------------------------
    # 成品预览
    # ------------------------------------------------------------------
    def open_preview(self) -> None:
        path = self._selected_path()
        if not path:
            return
        target = self.results.get(path)
        if not target or not os.path.exists(target):
            target = path
        if not os.path.exists(target):
            self.log(self.trf("[WARN] 找不到可预览的文件: {target}", target=target), "err")
            return
        # 失败项没有成品，会回退到原图；原图可能是损坏文件。先真正解码一次
        # （draft 只解小图，成本低），别让 Toplevel 开出来再崩。
        try:
            with Image.open(target) as probe:
                probe.draft("RGB", (64, 64))
                probe.load()
        except Exception as exc:
            self.log(self.trf("[ERROR] 无法预览 {name}: {err}",
                                    name=os.path.basename(target), err=exc), "err")
            messagebox.showerror(self.tr("无法预览"),
                                    self.trf("该文件无法解码：\n{name}\n\n{err}",
                                            name=os.path.basename(target), err=exc))
            return
        try:
            if self._preview is not None and self._preview.winfo_exists():
                self._preview.destroy()
            self._preview = PreviewWindow(self.root, target, original_path=path, tr=self.tr)
            self._preview.focus_set()
        except Exception as exc:
            self.log(self.trf("[ERROR] 打开预览失败: {err}", err=exc), "err")
            messagebox.showerror(self.tr("预览失败"),
                                    self.trf("无法打开预览窗口：\n{err}", err=exc))
            if self._preview is not None:
                try:
                    self._preview.destroy()
                except Exception:
                    pass
                self._preview = None

    # ------------------------------------------------------------------
    # 输出目录 / 取消 / 重试 / 报告
    # ------------------------------------------------------------------
    def _refresh_output_hint(self) -> None:
        custom = self.output_dir.get().strip()
        if custom:
            self.output_hint.set(short_path(custom))
            return
        base = (os.path.dirname(self.source_files[0]) if self.source_files
                else self.tr("源图所在目录"))
        self.output_hint.set(self.tr("默认 · ")
                              + short_path(os.path.join(base, OUTPUT_DIRNAME)))

    def choose_output_dir(self) -> None:
        initial = self.output_dir.get().strip() or self.last_open_dir
        path = filedialog.askdirectory(title=self.tr("选择输出目录"), initialdir=initial)
        if not path:
            return
        self.output_dir.set(path)
        self._refresh_output_hint()
        self.log(self.trf("输出目录改为: {path}", path=path), "dim")

    def reset_output_dir(self) -> None:
        self.output_dir.set("")
        self._refresh_output_hint()
        self.log(self.tr("输出目录恢复默认（源图目录 / resolved_cases）。"), "dim")

    def cancel_processing(self) -> None:
        if not self._running:
            return
        self._cancel.set()
        self.btn_cancel.config(state="disabled")
        self.log(self.tr("已发出取消指令，等待当前这张处理完…"), "err")

    def retry_failed(self) -> None:
        if self._running or not self.failed_paths:
            return
        self.start_thread(only_failed=True)

    def _set_report(self, path: str) -> None:
        self.report_path = path

    def open_report(self) -> None:
        if self.report_path and os.path.exists(self.report_path):
            self._open_path(self.report_path)
        elif self.last_output_dir:
            self._open_path(self.last_output_dir)
        else:
            messagebox.showinfo("Info", self.tr("还没有生成过结案报告。"))

    def open_about(self) -> None:
        """打开关于对话框：版本、构建信息、签名状态、配置目录、校验和。"""
        if self._about is not None and self._about.winfo_exists():
            self._about.lift()
            self._about.focus_set()
            return
        self._about = AboutWindow(self.root, tr=self.tr)
        self._about.focus_set()

    def open_output_folder(self) -> None:
        target = self.last_output_dir
        if not target or not os.path.isdir(target):
            messagebox.showinfo("Info", self.tr("输出目录尚不存在，请先执行一次处理。"))
            return
        self._open_path(target)

    @staticmethod
    def _open_path(path: str) -> None:
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 右键菜单
    # ------------------------------------------------------------------
    def _create_context_menu(self) -> None:
        self.context_menu = tk.Menu(self.root, tearoff=0, bg=C["rail"], fg=C["text"],
                                    activebackground=C["hover"], activeforeground="#FFFFFF",
                                    bd=0)
        self.context_menu.add_command(label="查看成品大图", command=self.open_preview)
        self.context_menu.add_command(label="移除此线索", command=self.remove_selected)
        self.context_menu.add_command(label="清空列表", command=self.clear_list)

        def do_popup(event):
            try:
                row = self.tree.identify_row(event.y)
                if row:
                    self.tree.selection_set(row)
                    self.tree.focus(row)
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

        self.tree.bind("<Button-3>", do_popup)

    # ------------------------------------------------------------------
    # 日志
    # ------------------------------------------------------------------
    def log(self, msg: str, tag: str | None = None) -> None:
        stamp = time.strftime("%H:%M:%S")
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, f"[{stamp}] {msg}\n", tag or ())
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")

    # ------------------------------------------------------------------
    # 处理
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_digits(proposed: str) -> bool:
        return proposed == "" or (proposed.isdigit() and len(proposed) <= 5)

    def _collect_options(self) -> dict:
        max_px = DEFAULT_MAX_PX
        raw = self.resize_width.get().strip()
        if raw.isdigit() and int(raw) > 0:
            max_px = int(raw)
        elif self.enable_resize.get():
            self.log(self.trf("Resize 数值无效，已回退为 {px}px。", px=DEFAULT_MAX_PX), "err")
        return {
            "paths": list(self.source_files),
            "target_ext": self.target_format.get().lower(),
            "resize": bool(self.enable_resize.get()),
            "max_px": max_px,
            "watermark": bool(self.enable_watermark.get()),
            "wm": self._wm_config(),
            "target_bytes": self._target_bytes(),
            "keep_meta": bool(self.keep_meta.get()),
            "parallel": bool(self.parallel.get()),
            "rename_pattern": self.rename_pattern.get().strip()
            if self.rename_enabled.get() else "",
            "output_dir": self.output_dir.get().strip(),
        }

    def _set_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for btn in (self.btn_add, self.btn_folder, self.btn_remove, self.btn_choose_out):
            btn.config(state=state)
        self.btn_run.config(state=state)
        self.btn_cancel.config(state="disabled" if enabled else "normal")
        self._update_retry_label()
        if enabled:
            self.btn_retry.config(state="normal" if self.failed_paths else "disabled")
            self.btn_report.config(state="normal" if self.report_path else "disabled")
        else:
            self.btn_retry.config(state="disabled")
            self.btn_report.config(state="disabled")
        self._running = not enabled

    def _update_retry_label(self) -> None:
        count = len(self.failed_paths)
        self.btn_retry.config(
            text=self.trf("重试失败 ({n})", n=count) if count else self.tr("重试失败"))

    def start_thread(self, only_failed: bool = False) -> None:
        if self._running:
            return
        if not self.source_files:
            messagebox.showwarning("No Evidence", self.tr("请先往证据清单里添加图片。"))
            return

        paths = list(self.failed_paths) if only_failed else list(self.source_files)
        if not paths:
            return
        self._run_paths(paths, reset_results=not only_failed,
                        label="重试" if only_failed else "开始", silent=False)

    def _run_paths(self, paths: list[str], reset_results: bool = False,
                   label: str = "开始", silent: bool = False) -> bool:
        """跑一批指定文件。监听模式复用同一条管线，只是不弹汇总框。"""
        if self._running or not paths:
            return False

        options = self._collect_options()
        options["paths"] = paths
        options["silent"] = silent
        if reset_results:
            self.results.clear()
        for path in paths:
            self.status[path] = 0
        self.failed_paths = []
        self._refresh_tree()
        self._save_settings()
        self._cancel.clear()
        self._set_controls_enabled(False)
        self.lbl_status.config(text="PROCESSING", fg=C["red"])
        self.lbl_progress.config(text="")
        # 记下本次实际输出目录，监听线程要拿它排除自身产物，否则会自噬
        self._watch_exclude = self._effective_output_dir(options)
        self.log(self.trf("{label}处理 {n} 项 → {dest}",
                            label=self.tr(label), n=len(paths),
                            dest=options["output_dir"] or self.tr("默认目录")), "dim")
        threading.Thread(target=self.process_images, args=(options,), daemon=True).start()
        return True

    @staticmethod
    def _effective_output_dir(options: dict) -> str:
        custom = (options.get("output_dir") or "").strip()
        if custom:
            return os.path.abspath(custom)
        paths = options.get("paths") or []
        if not paths:
            return ""
        return os.path.abspath(os.path.join(os.path.dirname(paths[0]), OUTPUT_DIRNAME))

    # ------------------------------------------------------------------
    # 文件夹监听
    # ------------------------------------------------------------------
    def _choose_watch_dir(self) -> None:
        initial = self._watch_dir or self.last_open_dir
        path = filedialog.askdirectory(title=self.tr("选择要监听的目录"), initialdir=initial)
        if not path:
            return
        self._watch_dir = path
        self.last_open_dir = path
        self._save_settings()
        self._update_watch_ui()
        self.log(self.trf("监听目录已设为: {path}", path=path), "dim")

    def _toggle_watch(self) -> None:
        if self._watching:
            self._stop_watching()
            return
        if not self._watch_dir or not os.path.isdir(self._watch_dir):
            self._choose_watch_dir()
            if not self._watch_dir or not os.path.isdir(self._watch_dir):
                return

        self._watching = True
        self._watch_count = 0
        self._watch_queue.clear()
        self._seen_watch.clear()
        self._pending_watch.clear()
        self._stop_watch.clear()
        self._watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._watch_thread.start()
        self._update_watch_ui()
        self.log(self.trf("开始监听: {path}（文件写完后自动处理）",
                                  path=self._watch_dir), "ok")

    def _stop_watching(self) -> None:
        self._watching = False
        self._stop_watch.set()
        self._update_watch_ui()
        self.log(self.tr("已停止监听。"), "dim")

    def _watch_loop(self) -> None:
        """后台轮询：只收「尺寸与修改时间连续两次不变」的文件。"""
        while not self._stop_watch.is_set():
            try:
                ready = self._scan_watch_dir()
            except Exception as exc:
                self._post(self.log, self.trf("[WATCH] 扫描失败: {err}", err=exc), "err")
                ready = []
            if ready:
                self._post(self._on_watch_files, ready)
            self._stop_watch.wait(WATCH_POLL_SECONDS)

    def _scan_watch_dir(self) -> list[str]:
        if not self._watch_dir:
            return []
        try:
            names = os.listdir(self._watch_dir)
        except OSError:
            return []

        exclude = self._watch_exclude or ""
        now = time.time()
        ready: list[str] = []
        for name in names:
            if not name.lower().endswith(SUPPORTED_EXTS):
                continue
            full = os.path.join(self._watch_dir, name)
            if not os.path.isfile(full):
                continue
            # 排除自己的输出目录，否则处理产物会被当成新文件再次处理，无限循环
            if exclude:
                try:
                    if os.path.abspath(full).startswith(exclude + os.sep):
                        continue
                except OSError:
                    pass
            try:
                st = os.stat(full)
            except OSError:
                continue

            key = (full, st.st_size, st.st_mtime)
            if key in self._seen_watch:
                continue

            prev = self._pending_watch.get(full)
            if prev and prev[0] == st.st_size and prev[1] == st.st_mtime:
                # 连续两次观测一致，且已过静置时间，才认为写完了
                if now - prev[2] >= WATCH_SETTLE_SECONDS:
                    self._seen_watch.add(key)
                    self._pending_watch.pop(full, None)
                    ready.append(full)
                    continue
                continue
            # 首次见到 / 还在变化：记录当前快照与首次时间
            self._pending_watch[full] = (st.st_size, st.st_mtime, prev[2] if prev else now)
        return ready

    def _on_watch_files(self, paths: list[str]) -> None:
        if not paths or not self._watching:
            return
        self._add_files(paths, label="WATCH")
        self._watch_count += len(paths)
        self._update_watch_ui()
        if self._running:
            self._watch_queue.extend(paths)     # 正忙，等这一轮结束再处理
            return
        self._run_paths(paths, reset_results=False, label="监听", silent=True)

    def _update_watch_ui(self) -> None:
        if not hasattr(self, "lbl_watch"):
            return
        # 侧栏只有 128px 宽，只显示目录名，完整路径在处理日志里
        name = os.path.basename(self._watch_dir.rstrip("\\/")) or self._watch_dir
        if self._watching:
            self.btn_watch.config(text=self.tr("停止监听"))
            self.lbl_watch.config(
                text=self.trf("监听中 · 已收 {n}\n{name}", n=self._watch_count, name=name),
                fg=C["green"])
        elif self._watch_dir:
            self.btn_watch.config(text=self.tr("开启监听"))
            self.lbl_watch.config(text=self.trf("未开启\n{name}", name=name), fg=C["text3"])
        else:
            self.btn_watch.config(text=self.tr("开启监听"))
            self.lbl_watch.config(text=self.tr("未开启"), fg=C["text3"])

    def process_images(self, options: dict) -> None:
        paths: list[str] = options["paths"]
        total = len(paths)
        summary = {"total": total, "ok": 0, "failed": 0, "errors": [],
                   "failed_paths": [], "elapsed": 0.0, "cancelled": False,
                   "oversize": 0, "lowq": 0, "report": None,
                   "silent": bool(options.get("silent"))}
        records: list[dict] = []
        started = time.perf_counter()
        try:
            if not paths:
                return
            custom = options.get("output_dir") or ""
            output_dir = custom or os.path.join(os.path.dirname(paths[0]), OUTPUT_DIRNAME)
            os.makedirs(output_dir, exist_ok=True)
            self.last_output_dir = output_dir
            self._post(self._set_output_dir, output_dir)
            self._post(self.log, self.trf("输出目录: {path}", path=output_dir), "dim")

            # 主线程预分配输出路径：并行时多个线程同时写盘，先占好名字就不会抢同一个文件。
            # 序号与重命名规则在这里一次性算好，报告里的顺序也由它定。
            ext = options["target_ext"]
            plan = []
            reserved: set[str] = set()
            for index, path in enumerate(paths):
                stem = os.path.splitext(os.path.basename(path))[0]
                pattern = options.get("rename_pattern") or ""
                if pattern:
                    stem = self._render_name_pattern(pattern, stem, index + 1, total)
                save_path = self._unique_path(output_dir, stem, ext, reserved)
                reserved.add(save_path)
                plan.append((path, index + 1, save_path))

            parallel = (options.get("parallel", True) and total > 1
                        and (os.cpu_count() or 1) > 1)
            if parallel:
                self._process_parallel(plan, options, output_dir, total, summary, records)
            else:
                self._process_serial(plan, options, output_dir, total, summary, records)

            report = self._write_report(output_dir, records)
            if report:
                summary["report"] = report
                self._post(self._set_report, report)
        except Exception as exc:
            summary["errors"].append(("(setup)", str(exc)))
            self._post(self.log, f"[FATAL] {exc}", "err")
        finally:
            summary["elapsed"] = time.perf_counter() - started
            self._post(self._finish, summary)

    def _run_one(self, path: str, options: dict, output_dir: str,
                 seq: int, total: int, save_path: str) -> dict:
        """单图处理：在 worker 线程里跑，不碰任何 Tk；返回结构化结果给主协调线程。"""
        t0 = time.perf_counter()
        try:
            info = self._process_one(path, options, output_dir, seq, total, save_path)
            return {"path": path, "ok": True, "info": info, "error": None,
                    "cost": (time.perf_counter() - t0) * 1000}
        except Exception as exc:
            return {"path": path, "ok": False, "info": None, "error": str(exc),
                    "cost": (time.perf_counter() - t0) * 1000}

    def _consume(self, res: dict, total: int, summary: dict, records: list) -> None:
        """把单图结果落到 UI 与统计里；只在主协调线程调用，避免并发改共享状态。"""
        path = res["path"]
        name = os.path.basename(path)
        self._post(self._register_result, path, res["info"]["saved"] if res["ok"] else "")
        if res["ok"]:
            info = res["info"]
            summary["ok"] += 1
            self._post(self.log,
                       f"Resolved: {name} → {os.path.basename(info['saved'])}", "ok")
            self._post(self._mark, path, 2, f"{info['out_size'][0]}×{info['out_size'][1]}")
            if info.get("oversize"):
                summary["oversize"] += 1
            if info.get("quality") and info["quality"] < 20:
                summary["lowq"] += 1
            records.append({"name": name, "source": path, "status": self.tr("成功"),
                            "src_size": info["src_size"], "out_size": info["out_size"],
                            "src_bytes": info["src_bytes"], "out_bytes": info["out_bytes"],
                            "cost": res["cost"], "saved": info["saved"], "error": "",
                            "quality": info.get("quality"),
                            "oversize": info.get("oversize", False)})
        else:
            summary["failed"] += 1
            summary["failed_paths"].append(path)
            summary["errors"].append((name, res["error"]))
            self._post(self.log, f"[ERROR] {name}: {res['error']}", "err")
            self._post(self._mark, path, 3)
            records.append({"name": name, "source": path, "status": self.tr("失败"),
                            "src_size": None, "out_size": None,
                            "src_bytes": self._safe_size(path), "out_bytes": 0,
                            "cost": res["cost"], "saved": "", "error": res["error"],
                            "quality": None, "oversize": False})

    def _process_serial(self, plan, options, output_dir, total, summary, records) -> None:
        for index, (path, seq, save_path) in enumerate(plan):
            if self._cancel.is_set():
                summary["cancelled"] = True
                self._post(self.log, self.trf("[CANCELLED] 已停止，剩余 {n} 项未处理",
                                               n=total - index), "err")
                return
            self._post(self._mark, path, 1)
            res = self._run_one(path, options, output_dir, seq, total, save_path)
            self._consume(res, total, summary, records)
            self._post(self._set_progress, index + 1, total)

    def _process_parallel(self, plan, options, output_dir, total, summary, records) -> None:
        workers = min(os.cpu_count() or 4, 8)
        self._post(self.log, self.trf("[PARALLEL] 并行处理，工作线程 {n}", n=workers), "dim")
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(self._run_one, path, options, output_dir, seq, total, save_path): path
                       for path, seq, save_path in plan}
            for fut in as_completed(futures):
                if self._cancel.is_set():
                    summary["cancelled"] = True
                    self._post(self.log, self.tr("[CANCELLED] 已停止，正在退出工作线程…"), "err")
                    ex.shutdown(wait=False, cancel_futures=True)
                    break
                res = fut.result()
                self._consume(res, total, summary, records)
                done += 1
                self._post(self._set_progress, done, total)

    @staticmethod
    def _safe_size(path: str) -> int:
        try:
            return os.path.getsize(path)
        except OSError:
            return 0

    def _write_report(self, output_dir: str, records: list[dict]) -> str | None:
        """结案报告：每张图的前后尺寸、体积变化、耗时与失败原因。"""
        if not records:
            return None
        stamp = time.strftime("%Y%m%d_%H%M%S")
        prefix = self.tr(REPORT_PREFIX)
        path = os.path.join(output_dir, f"{prefix}_{stamp}.csv")
        if os.path.exists(path):      # 同一秒内跑两次时不要互相覆盖
            path = self._unique_path(output_dir, f"{prefix}_{stamp}", "csv")
        try:
            # utf-8-sig：不带 BOM 时 Excel 打开中文会乱码
            with open(path, "w", newline="", encoding="utf-8-sig") as fp:
                writer = csv.writer(fp)
                writer.writerow([self.tr("序号"), self.tr("文件名"), self.tr("状态"),
                                 self.tr("源尺寸"), self.tr("成品尺寸"),
                                 self.tr("源体积"), self.tr("成品体积"), self.tr("体积变化"),
                                 self.tr("质量"), self.tr("耗时(ms)"),
                                 self.tr("成品文件"), self.tr("错误原因")])
                for i, r in enumerate(records, 1):
                    src = f"{r['src_size'][0]}×{r['src_size'][1]}" if r["src_size"] else "—"
                    out = f"{r['out_size'][0]}×{r['out_size'][1]}" if r["out_size"] else "—"
                    if r["src_bytes"] and r["out_bytes"]:
                        delta = (r["out_bytes"] - r["src_bytes"]) / r["src_bytes"] * 100
                        change = f"{delta:+.1f}%"
                    else:
                        change = "—"
                    writer.writerow([
                        i, r["name"], r["status"], src, out,
                        human_size(r["src_bytes"]) if r["src_bytes"] else "—",
                        human_size(r["out_bytes"]) if r["out_bytes"] else "—",
                        change,
                        (f"{r['quality']}" + ("*" if r.get("oversize") else ""))
                        if r.get("quality") else "—",
                        f"{r['cost']:.0f}",
                        os.path.basename(r["saved"]) if r["saved"] else "—",
                        r["error"],
                    ])
            return path
        except OSError as exc:
            self._post(self.log, self.trf("[WARN] 结案报告写入失败: {err}", err=exc), "err")
            return None

    def _process_one(self, path: str, options: dict, output_dir: str,
                     seq: int = 1, total: int = 1, save_path: str | None = None) -> dict:
        ext = options["target_ext"]
        src_bytes = self._safe_size(path)
        os.makedirs(output_dir, exist_ok=True)   # 兜底：目录被外部删掉也不至于整批失败
        with Image.open(path) as raw:
            # 大图缩放前先让解码器按目标尺寸降采样：8000px 的图直接解全会吃几个 GB，
            # draft 在 load 阶段就把尺寸压下来（仅对支持的分页/大图格式有效，失败忽略）。
            if options["resize"] and options["max_px"] > 0 and raw.format in ("JPEG", "PNG", "WEBP", "TIFF"):
                try:
                    raw.draft("RGB", (options["max_px"], options["max_px"]))
                except Exception:
                    pass
            # 先取 EXIF 再转：convert() 之后原始元数据就没了
            exif_bytes = self._extract_exif(raw) if options.get("keep_meta") else None
            img = ImageOps.exif_transpose(raw)
            img = img.convert("RGBA")
            src_size = img.size

            if options["resize"] and options["max_px"] > 0:
                img.thumbnail((options["max_px"], options["max_px"]), Image.Resampling.LANCZOS)

            if options["watermark"] and options["wm"]["text"]:
                img = self._apply_watermark(img, options["wm"])

            if ext in ("jpg", "bmp"):
                flat = Image.new("RGB", img.size, (255, 255, 255))
                flat.paste(img, mask=img.split()[3])
                out_img = flat
            else:
                out_img = img
            out_size = out_img.size
        stem = os.path.splitext(os.path.basename(path))[0]
        pattern = options.get("rename_pattern") or ""
        if pattern:
            stem = self._render_name_pattern(pattern, stem, seq, total)
        # save_path 由主线程预分配（并行时避免并发抢同一文件名）；没传则现算
        if not save_path:
            save_path = self._unique_path(output_dir, stem, ext)

        target = options.get("target_bytes", 0)
        quality = None
        if target and ext in ("jpg", "webp"):
            quality, payload = self._encode_to_target(out_img, ext, target, exif_bytes)
            with open(save_path, "wb") as fp:
                fp.write(payload)
        else:
            out_img.save(save_path, **self._save_params(ext, out_img, exif_bytes))

        out_bytes = self._safe_size(save_path)
        return {
            "saved": save_path,
            "src_size": src_size,
            "out_size": out_size,
            "src_bytes": src_bytes,
            "out_bytes": out_bytes,
            "quality": quality,
            "oversize": bool(target and ext in ("jpg", "webp") and out_bytes > target),
        }

    @staticmethod
    def _encode_to_target(img: Image.Image, ext: str, target_bytes: int,
                          exif_bytes: bytes | None = None) -> tuple[int, bytes]:
        """在内存里二分质量，返回 (最终质量, 编码后的字节)。

        搜索与最终写入用同一套参数（不启用 optimize），保证搜到的大小就是落盘大小；
        这样一张图最多 7 次内存编码，不产生临时文件。
        """
        fmt = "JPEG" if ext == "jpg" else "WEBP"

        def encode(q: int) -> bytes:
            buf = io.BytesIO()
            kw = {"quality": q}
            if exif_bytes:
                kw["exif"] = exif_bytes
            if ext == "jpg":
                img.save(buf, format=fmt, **kw)
            else:
                img.save(buf, format=fmt, method=4, **kw)
            return buf.getvalue()

        lo, hi, best = 1, 95, None
        while lo <= hi:
            mid = (lo + hi) // 2
            data = encode(mid)
            if len(data) <= target_bytes:
                best = (mid, data)
                lo = mid + 1
            else:
                hi = mid - 1
        if best:
            return best
        # 最低质量仍超标：用 q=1 交出，交给上层标记 oversize
        return 1, encode(1)

    @staticmethod
    def _save_params(ext: str, img: Image.Image, exif_bytes: bytes | None = None) -> dict:
        params: dict = {}
        if ext == "jpg":
            params = {"quality": 95, "optimize": True}
        elif ext == "webp":
            params = {"quality": 95, "method": 6}
        elif ext == "ico":
            sizes = [s for s in ICON_SIZES if s[0] <= min(img.size) and s[1] <= min(img.size)]
            params = {"sizes": sizes or [(min(img.size[0], 256), min(img.size[1], 256))]}
        # EXIF 只写进 jpg / webp，其它格式没有承载位置
        if exif_bytes and ext in ("jpg", "webp"):
            params["exif"] = exif_bytes
        return params

    @staticmethod
    def _unique_path(output_dir: str, stem: str, ext: str,
                     reserved: set | None = None) -> str:
        """找一个不撞名的输出路径。

        reserved 是本批已预分配的名字：预分配发生在写盘之前，磁盘上还没有文件，
        只看 os.path.exists 会让同名文件全算到同一个路径上（后写的覆盖先写的）。
        """
        taken = reserved or set()

        def free(path: str) -> bool:
            return not os.path.exists(path) and path not in taken

        candidate = os.path.join(output_dir, f"{stem}.{ext}")
        if free(candidate):
            return candidate
        for n in range(1, 1000):
            candidate = os.path.join(output_dir, f"{stem}_{n}.{ext}")
            if free(candidate):
                return candidate
        return os.path.join(output_dir, f"{stem}_{int(time.time())}.{ext}")

    def _apply_watermark(self, img: Image.Image, cfg: dict) -> Image.Image:
        """按配置绘制水印。

        只在水印被勾选时才会被调用；cfg 由主线程一次性采集，子线程不读 Tk 变量。
        文字先渲染成小贴图（sprite），需要角度就旋转一次，再按位置/平铺贴上去。
        """
        text = (cfg.get("text") or "").strip()
        if not text:
            return img

        w, h = img.size
        margin = max(6, int(min(w, h) * 0.02))
        base_size = max(10, int(min(w, h) * 0.04))
        opacity = max(0, min(100, int(cfg.get("opacity", 70))))
        alpha = int(round(255 * opacity / 100))
        if alpha <= 0:
            return img

        color = self._parse_color(cfg.get("color", "#E74C3C"))
        angle = max(-45, min(45, int(cfg.get("angle", 0) or 0)))
        gap = max(110, min(320, int(cfg.get("gap", 180) or 180)))

        probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        font, stroke, _bbox = fit_watermark_font(probe, text, w, base_size, margin)

        sprite = self._make_text_sprite(text, font, stroke, alpha, color)
        if angle:
            sprite = sprite.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)

        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))

        # --- 平铺：按 sprite 尺寸 × 间距倍率交错铺满，位置参数在此模式下不生效 ---
        if cfg.get("tile"):
            step_x = max(int(sprite.width * gap / 100), 4)
            step_y = max(int(sprite.height * gap / 100 * 1.15), 4)

            ys = []
            y = -sprite.height // 2
            while y < h:
                ys.append(y)
                y += step_y
            # 补一行贴住底边：否则间距偏大时底部会留一条完全干净的白带
            if not ys or ys[-1] + sprite.height < h:
                ys.append(max(0, h - sprite.height))

            for row, y in enumerate(ys):
                xs = []
                x = -step_x // 2 + (step_x // 2 if row % 2 else 0)
                while x < w:
                    xs.append(x)
                    x += step_x
                # 同理补一列贴住右边
                if not xs or xs[-1] + sprite.width < w:
                    xs.append(max(0, w - sprite.width))
                for x in xs:
                    layer.paste(sprite, (x, y), sprite)
            return Image.alpha_composite(img, layer)

        # --- 单点：九宫格定位 ---
        ratio_x, ratio_y = WM_POSITIONS.get(cfg.get("pos", "br"), (1.0, 1.0))
        sw, sh = sprite.size
        if ratio_x <= 0:
            x = margin
        elif ratio_x >= 1:
            x = w - margin - sw
        else:
            x = (w - sw) // 2
        if ratio_y <= 0:
            y = margin
        elif ratio_y >= 1:
            y = h - margin - sh
        else:
            y = (h - sh) // 2

        # 收敛到画布内：贴图比图还大时贴边，别整段画到外面等于没加水印
        x = max(0, min(x, w - sw)) if sw <= w else max(margin // 2, 0)
        y = max(0, min(y, h - sh)) if sh <= h else max(margin // 2, 0)
        layer.paste(sprite, (x, y), sprite)
        return Image.alpha_composite(img, layer)

    @staticmethod
    def _parse_color(value: str) -> tuple[int, int, int]:
        try:
            raw = str(value).lstrip("#")
            if len(raw) == 6:
                return tuple(int(raw[i:i + 2], 16) for i in (0, 2, 4))
        except (ValueError, TypeError):
            pass
        return (231, 76, 60)

    @staticmethod
    def _make_text_sprite(text: str, font, stroke: int, alpha: int,
                          color: tuple[int, int, int]) -> Image.Image:
        """把文字渲染成紧贴边界的透明贴图；描边色按文字亮度自动取反，保证可读。"""
        box = font.getbbox(text, stroke_width=stroke)
        pad = stroke + 2
        width = max(1, box[2] - box[0] + pad * 2)
        height = max(1, box[3] - box[1] + pad * 2)
        sprite = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(sprite)
        luminance = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
        # 阈值取 100（不是 128）：主题红 #E74C3C 亮度约 120，用 128 会判成"深色"而配白描边，
        # 白描边在浅色底上等于没有；降到 100 后红字会配黑描边，浅底上才立得住。
        stroke_rgb = (0, 0, 0) if luminance > 100 else (255, 255, 255)
        draw.text((pad - box[0], pad - box[1]), text, font=font,
                  fill=color + (alpha,), stroke_width=stroke,
                  stroke_fill=stroke_rgb + (alpha,))
        return sprite

    def _set_output_dir(self, path: str) -> None:
        self.last_output_dir = path

    def _register_result(self, source: str, output: str) -> None:
        self.results[source] = output
        if self._selected_path() == source:
            self.btn_preview.config(state="normal")

    def _refresh_progress_label(self) -> None:
        """按当前语言重刷进度/结案标签。

        这两处文案是运行时拼出来的，控件登记表里没有它们；不重刷的话，
        处理完再切语言，左侧状态区会一直停在旧语言。
        """
        st = getattr(self, "_finish_state", None)
        if st:
            self.lbl_progress.config(
                text=self.trf("成功 {ok} / 失败 {failed}\n用时 {t}s",
                              ok=st["ok"], failed=st["failed"],
                              t=f"{st['elapsed']:.1f}")
                     + (self.tr("\n已取消") if st["cancelled"] else ""))
            return
        pr = getattr(self, "_progress_state", None)
        if pr:
            done, total = pr
            pct = int(done / total * 100) if total else 0
            self.lbl_progress.config(text=self.trf("进度 {done}/{total}\n{pct}%",
                                                  done=done, total=total, pct=pct))

    def _set_progress(self, done: int, total: int) -> None:
        self._progress_state = (done, total)
        pct = int(done / total * 100) if total else 0
        self.lbl_progress.config(text=self.trf("进度 {done}/{total}\n{pct}%",
                                            done=done, total=total, pct=pct))

    def _finish(self, summary: dict) -> None:
        total, ok, failed = summary["total"], summary["ok"], summary["failed"]
        elapsed = summary["elapsed"]
        cancelled = summary.get("cancelled", False)

        # 先落状态，再恢复按钮：_set_controls_enabled 会据此决定重试/报告按钮是否可点
        self.failed_paths = list(summary.get("failed_paths") or [])
        if summary.get("report"):
            self.report_path = summary["report"]

        if total == 0:
            self.lbl_status.config(text="WAITING", fg=C["red"])
        elif cancelled:
            self.lbl_status.config(text=f"STOPPED {ok}/{total}", fg=C["amber"])
        elif failed == 0:
            self.lbl_status.config(text=f"CLOSED {ok}/{total}", fg=C["green"])
        else:
            self.lbl_status.config(text=f"{ok}/{total} · {failed} FAIL", fg=C["red"])

        self._finish_state = {"ok": ok, "failed": failed,
                              "elapsed": elapsed, "cancelled": cancelled}
        self.lbl_progress.config(
            text=self.trf("成功 {ok} / 失败 {failed}\n用时 {t}s",
                          ok=ok, failed=failed, t=f"{elapsed:.1f}")
                 + (self.tr("\n已取消") if cancelled else ""))
        self._set_controls_enabled(True)
        if self.last_output_dir and os.path.isdir(self.last_output_dir):
            self.btn_open_folder.config(state="normal")

        tail = "（已取消）" if cancelled else ""
        self.log(self.trf("=== 结案：成功 {ok}，失败 {failed}，用时 {t}s{tail} ===",
                                 ok=ok, failed=failed, t=f"{elapsed:.1f}", tail=tail),
                 "ok" if failed == 0 and not cancelled else "err")
        for name, reason in summary["errors"][:10]:
            self.log(self.trf("    {name}: {reason}", name=name, reason=reason), "dim")
        if summary.get("oversize"):
            self.log(self.trf("[WARN] {n} 个文件压到质量 1 仍超过目标体积，"
                                 "报告里用 * 标出；可配合 Resize 先缩小尺寸。",
                                 n=summary["oversize"]), "err")
        if summary.get("lowq"):
            self.log(self.trf("[WARN] {n} 个文件为达标把质量压到 20 以下，画质可能明显下降；"
                                 "建议先勾 Resize 缩小尺寸，再压体积。",
                                 n=summary["lowq"]), "err")
        if self.report_path:
            self.log(self.trf("结案报告: {path}", path=self.report_path), "dim")

        for path in self.source_files:
            if self.status.get(path) == 2 and path in self.results:
                self.tree.selection_set(path)
                self.tree.focus(path)
                self.tree.see(path)
                break

        if total:
            detail = self.trf("成功 {ok} / 共 {total}", ok=ok, total=total)
            if cancelled:
                detail += self.tr("（已取消）")
            detail += self.trf("\n用时 {t}s\n输出: {dir}",
                               t=f"{elapsed:.1f}", dir=self.last_output_dir)
            if failed:
                detail += self.trf("\n\n失败 {n} 项，可点「重试失败」只重跑这些。", n=failed)
            if summary.get("oversize"):
                detail += self.trf("\n\n{n} 项未能压到目标体积，详见报告。",
                                   n=summary["oversize"])
            if self.report_path:
                detail += self.tr("\n\n已生成结案报告，点「导出报告」查看。")
            # 监听模式不弹框，否则每落一批文件就打断一次
            if not summary.get("silent"):
                messagebox.showinfo("Result", detail)

        if self._watching and self._watch_queue:
            queued = list(self._watch_queue)
            self._watch_queue.clear()
            self.root.after(60, lambda: self._run_paths(
                queued, reset_results=False, label="监听", silent=True))


def create_root() -> tk.Tk:
    """优先用带拖拽支持的 Tk 根窗口；失败就退回普通 Tk，保证程序总能起来。"""
    if DND_AVAILABLE and TkinterDnD is not None:
        try:
            return TkinterDnD.Tk()
        except Exception as exc:  # pragma: no cover
            print(f"[dnd] fallback to plain Tk: {exc}", file=sys.stderr)
    return tk.Tk()


if __name__ == "__main__":
    enable_dpi_awareness()
    root = create_root()
    app = ImageProcessorPro(root)
    root.mainloop()
