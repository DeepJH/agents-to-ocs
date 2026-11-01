"""
配置与命令行参数解析模块
全面支持 CLI 参数 (-h, -a, -m, -p 等) 以及环境变量覆盖
"""
import argparse
import os
import sys
from pathlib import Path
from runners import get_runner, list_runners, get_supported_agent_keys

BASE_DIR = Path(__file__).resolve().parent

def build_parser() -> argparse.ArgumentParser:
    supported_keys = get_supported_agent_keys()
    parser = argparse.ArgumentParser(
        prog="agents-to-ocs",
        description="🚀 agents-to-ocs: 将各种本地 AI Agent CLI (agy, claude code, codex) 转化为 OCS 网课助手兼容的智能题库服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 1. 默认使用 agy (gemini-3.8-flash-high) 启动服务
  python main.py

  # 2. 切换为 Claude Code 并指定 sonnet 模型
  python main.py -a claude -m sonnet

  # 3. 切换为 OpenAI Codex 并指定 o3 模型
  python main.py -a codex -m o3

  # 4. 自定义监听端口为 9000，设置并发限制为 5
  python main.py -p 9000 -c 5

  # 5. 查看当前系统已安装的 Agent 就绪状态
  python main.py --list-agents

  # 6. 查看指定 Agent 的推荐可用模型
  python main.py -a agy --list-models
"""
    )

    parser.add_argument(
        "-a", "--agent",
        dest="agent",
        choices=supported_keys,
        default=os.getenv("OCS_AGENT", "agy"),
        help=f"指定后端 Agent CLI (可选: {', '.join(supported_keys)}, 默认: %(default)s)"
    )

    parser.add_argument(
        "-m", "--model",
        dest="model",
        default=os.getenv("OCS_MODEL", ""),
        help="指定推理模型名称 (留空则自动采用对应 Agent 的推荐默认模型)"
    )

    parser.add_argument(
        "-p", "--port",
        dest="port",
        type=int,
        default=int(os.getenv("OCS_PORT", "8788")),
        help="指定 HTTP 服务监听端口 (默认: %(default)s)"
    )

    parser.add_argument(
        "-H", "--host",
        dest="host",
        default=os.getenv("OCS_HOST", "127.0.0.1"),
        help="指定 HTTP 服务监听地址 (默认: %(default)s)"
    )

    parser.add_argument(
        "-c", "--concurrency",
        dest="concurrency",
        type=int,
        default=int(os.getenv("OCS_MAX_CONCURRENCY", "3")),
        help="设置最大并发 Agent 进程数，防止 API 限流或系统卡顿 (默认: %(default)s)"
    )

    parser.add_argument(
        "-t", "--timeout",
        dest="timeout",
        type=int,
        default=int(os.getenv("OCS_TIMEOUT", "50")),
        help="单题最大推理超时秒数 (默认: %(default)s)"
    )

    parser.add_argument(
        "--no-cache",
        dest="no_cache",
        action="store_true",
        default=os.getenv("OCS_ENABLE_CACHE", "true").lower() in ("false", "0", "no"),
        help="禁用本地 SQLite 题库缓存持久化"
    )

    parser.add_argument(
        "--clear-cache",
        dest="clear_cache",
        action="store_true",
        help="一键清空本地 SQLite 题库缓存并退出"
    )

    parser.add_argument(
        "--list-agents",
        dest="list_agents",
        action="store_true",
        help="列出当前系统所有支持的 Agent 类型及系统就绪状态并退出"
    )

    parser.add_argument(
        "--list-models",
        dest="list_models",
        action="store_true",
        help="列出当前所选 Agent 的推荐模型列表并退出"
    )

    return parser

# 解析全局参数
_parser = build_parser()

# 仅在非 pytest/模块引入时正常解析
if "pytest" in sys.modules:
    _args = _parser.parse_args([])
else:
    # 允许部分特定命令透传
    _args, _ = _parser.parse_known_args()

# 导出运行时配置
AGENT_NAME = _args.agent
runner_instance = get_runner(AGENT_NAME)
MODEL_NAME = _args.model or runner_instance.default_model
HOST = _args.host
PORT = _args.port
MAX_CONCURRENCY = _args.concurrency
TIMEOUT_SECONDS = _args.timeout
ENABLE_CACHE = not _args.no_cache
DB_PATH = Path(os.getenv("OCS_DB_PATH", str(BASE_DIR / "cache.db")))

# 处理 --clear-cache
if getattr(_args, "clear_cache", False):
    from cache_store import cache
    del_count = cache.clear()
    print(f"\n[✔] 已成功清空本地 SQLite 题库缓存 (共清理 {del_count} 条记录)。\n")
    sys.exit(0)

# 处理 --list-agents
if getattr(_args, "list_agents", False):
    print("\n" + "=" * 65)
    print("  🤖 agents-to-ocs: 支持的 Agent CLI 列表与本地环境检测")
    print("=" * 65)
    for item in list_runners():
        status_icon = "✔ 已就绪" if item["available"] else "✖ 未就绪"
        print(f"  • [{item['key']}] {item['name']}")
        print(f"      命令名   : {item['binary']}")
        print(f"      状态     : {status_icon} ({item['status']})")
        print(f"      默认模型 : {item['default_model']}")
        print(f"      推荐模型 : {', '.join(item['models'][:4])} 等")
        print("-" * 65)
    print()
    sys.exit(0)

# 处理 --list-models
if getattr(_args, "list_models", False):
    target_runner = get_runner(_args.agent)
    print("\n" + "=" * 60)
    print(f"  📋 Agent [{target_runner.display_name}] 常用推荐模型列表")
    print("=" * 60)
    print(f"  默认模型 : {target_runner.default_model}\n")
    print("  推荐可用模型:")
    for m in target_runner.get_supported_models():
        is_default = " (默认)" if m == target_runner.default_model else ""
        print(f"    - {m}{is_default}")
    print("=" * 60 + "\n")
    sys.exit(0)
