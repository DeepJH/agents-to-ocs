"""
配置文件：管理服务端口、默认模型、并发控制与存储路径
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 服务监听地址与端口
HOST = os.getenv("OCS_HOST", "127.0.0.1")
PORT = int(os.getenv("OCS_PORT", "8788"))

# agy CLI 相关配置
AGY_BIN = os.getenv("AGY_BIN", "agy")
DEFAULT_MODEL = os.getenv("OCS_MODEL", "gemini-3.8-flash-high")
REASONING_EFFORT = os.getenv("OCS_EFFORT", "")

# 并发与超时控制 (防打爆与避免 OCS 60s 超时)
MAX_CONCURRENCY = int(os.getenv("OCS_MAX_CONCURRENCY", "3"))
TIMEOUT_SECONDS = int(os.getenv("OCS_TIMEOUT", "50"))

# 题库缓存设置
ENABLE_CACHE = os.getenv("OCS_ENABLE_CACHE", "true").lower() in ("true", "1", "yes")
DB_PATH = Path(os.getenv("OCS_DB_PATH", str(BASE_DIR / "cache.db")))
