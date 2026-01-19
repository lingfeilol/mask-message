@echo off
chcp 65001 >nul
title Musk Tweet ETF Monitor

echo ========================================
echo    Musk Tweet ETF Monitor 启动脚本
echo ========================================
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"
echo [信息] 工作目录: %CD%

:: 检查 Python 是否安装 (使用 call 防止 pyenv shim 终止脚本)
echo [信息] 检查 Python...
call python --version

echo [信息] 继续执行...

:: 检查虚拟环境是否存在
if not exist "venv\Scripts\activate.bat" (
    echo [信息] 创建虚拟环境...
    call python -m venv venv
    echo [信息] 虚拟环境创建完成
) else (
    echo [信息] 虚拟环境已存在
)

:: 激活虚拟环境
echo [信息] 激活虚拟环境...
call "venv\Scripts\activate.bat"

:: 安装依赖
echo [信息] 检查并安装依赖...
call pip install -r requirements.txt

:: 安装 Playwright 浏览器
echo [信息] 检查 Playwright 浏览器...
call playwright install chromium

:: 检查配置文件
if not exist "config.json" (
    echo [错误] 未找到 config.json 配置文件
    echo [提示] 请复制 config.example.json 并配置相关参数
    pause
    exit /b 1
)

:: 启动监控程序
echo.
echo [信息] 启动监控程序...
echo [提示] 按 Ctrl+C 可停止程序
echo ========================================
echo.

call python -m src.main %*

echo.
echo [信息] 程序已退出
pause
