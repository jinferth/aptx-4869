@echo off
rem ============================================================
rem  APTX-4869 图像情报分析终端 · 一键构建
rem  双击即可。构建前会自动跑一遍回归测试。
rem ============================================================
setlocal
cd /d "%~dp0"

set "PY=D:\Python314\python.exe"
if not exist "%PY%" set "PY=python"

echo.
echo [1/2] 跑回归测试 ...
"%PY%" tests\run_all.py
if errorlevel 1 (
    echo.
    echo [中止] 回归未通过，先修好再打包。
    pause
    exit /b 1
)

echo.
echo [2/2] 构建 ...
"%PY%" build.py %*
if errorlevel 1 (
    echo.
    echo [中止] 构建失败。
    pause
    exit /b 1
)

echo.
echo 构建完成，发布件在 release\ 目录。
pause
