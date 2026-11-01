"""
Agent 驱动工厂模块
"""
from typing import Dict, List, Optional, Any
from .base import BaseAgentRunner
from .agy import AgyRunner
from .claude import ClaudeRunner
from .codex import CodexRunner

_RUNNERS: Dict[str, BaseAgentRunner] = {
    "agy": AgyRunner(),
    "claude": ClaudeRunner(),
    "codex": CodexRunner(),
}

def get_runner(name: str) -> BaseAgentRunner:
    """根据名称获取对应的 Agent 驱动"""
    key = str(name).strip().lower()
    if key not in _RUNNERS:
        supported = ", ".join(_RUNNERS.keys())
        raise ValueError(f"不支持的 Agent 类型: '{name}'。当前支持: {supported}")
    return _RUNNERS[key]

def list_runners() -> List[Dict[str, Any]]:
    """列出所有支持的 Agent 及其系统就绪状态"""
    results = []
    for key, runner in _RUNNERS.items():
        ok, msg = runner.check_available()
        results.append({
            "key": key,
            "name": runner.display_name,
            "binary": runner.binary_name,
            "available": ok,
            "status": msg,
            "default_model": runner.default_model,
            "models": runner.get_supported_models(),
        })
    return results

def get_supported_agent_keys() -> List[str]:
    """返回支持的 Agent 键名列表"""
    return list(_RUNNERS.keys())
