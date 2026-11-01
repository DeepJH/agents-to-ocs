@echo off
chcp 65001 >nul
:: ==============================================================================
:: Windows 一键依赖自检与启动脚本
:: ==============================================================================
title AGY to OCS 题库服务 - 一键自检启动

echo ======================================================================
echo            AGY to OCS 题库服务 - 一键自检与启动 (Windows)
echo ======================================================================

cd /d "%~dp0"

:: 1. 检查 Python
set PYTHON_CMD=
python --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON_CMD=python
) else (
    py -3 --version >nul 2>&1
    if %errorlevel% == 0 (
        set PYTHON_CMD=py -3
    )
)

if "%PYTHON_CMD%" == "" (
    echo [错误] 未检测到 Python，请先前往 https://www.python.org 安装 Python 3.8+ 并勾选 "Add to PATH"。
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('%PYTHON_CMD% --version') do echo [✔] 检测到 %%v

:: 2. 检查 agy
where agy >nul 2>&1
if %errorlevel% == 0 (
    echo [✔] 检测到 agy CLI 已安装
) else (
    echo [警告] 未在环境变量 PATH 中找到 "agy" 命令。
    echo       请确认已安装 Google Antigravity CLI 并将其路径加入系统环境变量。
)

:: 3. 检查虚拟环境
set VENV_DIR=%~dp0.venv
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [!] 正在创建独立虚拟环境 (.venv)...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo [错误] 虚拟环境创建失败，请检查 Python 安装是否完整。
        pause
        exit /b 1
    )
    echo [✔] 虚拟环境创建成功
) else (
    echo [✔] 虚拟环境已就绪
)

:: 4. 自检依赖
echo [*] 正在自检依赖库...
"%VENV_DIR%\Scripts\python.exe" -c "import fastapi, uvicorn, pydantic" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 检测到依赖尚未安装，正在自动执行 pip install...
    "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip -q
    "%VENV_DIR%\Scripts\pip.exe" install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败，请检查网络或配置代理镜像。
        pause
        exit /b 1
    )
    echo [✔] 依赖安装完成！
) else (
    echo [✔] 所有依赖库均已完整就绪。
)

:: 5. 启动服务
echo [*] 正在启动 AGY to OCS 题库服务...
echo.
"%VENV_DIR%\Scripts\python.exe" main.py

pause
