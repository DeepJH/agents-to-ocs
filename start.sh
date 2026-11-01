#!/usr/bin/env bash
# ==============================================================================
# Linux / macOS 一键依赖自检与启动脚本 (自动处理 PEP 668 虚拟环境隔离)
# ==============================================================================
set -e

# 控制台色彩定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}          agent-to-ocs 题库服务 - 一键自检与启动 (Linux)              ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 1. 查找系统 Python 3
PYTHON_BIN=""
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo -e "${RED}[错误] 未检测到 Python 3 环境。请先安装 Python 3.8+。${NC}"
    exit 1
fi

PY_VER=$($PYTHON_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}[✔] 检测到 Python 版本: $PY_VER ($PYTHON_BIN)${NC}"

# 2. 检查 agy CLI 是否就绪
if command -v agy &>/dev/null; then
    echo -e "${GREEN}[✔] 检测到 agy CLI 正常安装 ($(which agy))${NC}"
else
    echo -e "${YELLOW}[警告] 未在环境变量 PATH 中找到 'agy' 命令。${NC}"
    echo -e "${YELLOW}      请确保已安装 Google Antigravity CLI 并已正确配置环境。${NC}"
fi

# 3. 检查并建立虚拟环境 (彻底规避 Linux PEP 668 externally-managed-environment 限制)
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/python" ]; then
    echo -e "${YELLOW}[!] 正在创建独立虚拟环境 (.venv)，以规避 Linux 系统级 pip 限制...${NC}"
    if ! $PYTHON_BIN -m venv "$VENV_DIR" 2>/dev/null; then
        echo -e "${RED}[错误] 无法创建 Python 虚拟环境。${NC}"
        echo -e "${YELLOW}提示：很多 Linux 发行版（如 Ubuntu/Debian）需要单独安装 venv 模块：${NC}"
        echo -e "${BLUE}  Debian/Ubuntu : sudo apt update && sudo apt install python3-venv python3-pip -y${NC}"
        echo -e "${BLUE}  CentOS/RHEL   : sudo yum install python3-virtualenv -y${NC}"
        echo -e "${BLUE}  Arch Linux    : sudo pacman -S python-virtualenv --noconfirm${NC}"
        exit 1
    fi
    echo -e "${GREEN}[✔] 虚拟环境创建成功: $VENV_DIR${NC}"
else
    echo -e "${GREEN}[✔] 虚拟环境已就绪: $VENV_DIR${NC}"
fi

# 4. 依赖完整性自检与自动安装
echo -e "${BLUE}[*] 正在自检 Python 运行依赖...${NC}"
NEED_INSTALL=0
if ! "$VENV_DIR/bin/python" -c "import fastapi, uvicorn, pydantic" &>/dev/null; then
    NEED_INSTALL=1
fi

if [ $NEED_INSTALL -eq 1 ]; then
    echo -e "${YELLOW}[!] 检测到依赖尚未安装或不完整，正在自动从 requirements.txt 安装...${NC}"
    "$VENV_DIR/bin/pip" install --upgrade pip -q
    "$VENV_DIR/bin/pip" install -r requirements.txt
    echo -e "${GREEN}[✔] 依赖安装完成！${NC}"
else
    echo -e "${GREEN}[✔] 所有依赖库均已完整就绪。${NC}"
fi

# 5. 启动服务 (支持透传用户命令行参数，如 -h, -a, -m 等)
echo -e "${GREEN}[*] 启动 agent-to-ocs 桥接服务中...${NC}\n"
exec "$VENV_DIR/bin/python" main.py "$@"
