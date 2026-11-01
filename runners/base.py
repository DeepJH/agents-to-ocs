"""
Agent 驱动抽象基类
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any

class BaseAgentRunner(ABC):
    """所有 CLI Agent 驱动的抽象基类"""
    name: str = "base"
    display_name: str = "Base Agent"
    binary_name: str = ""
    default_model: str = ""
    supported_models: List[str] = []

    @abstractmethod
    def build_command(self, prompt: str, model: str, image_paths: List[str]) -> List[str]:
        """构造调用该 Agent CLI 的命令行参数列表"""
        pass

    @abstractmethod
    def check_available(self) -> Tuple[bool, str]:
        """检查该 Agent 命令是否在系统中可用及登录状态"""
        pass

    def get_supported_models(self) -> List[str]:
        """返回常用推荐模型列表"""
        return self.supported_models
