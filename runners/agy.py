"""
Google Antigravity (agy) CLI 驱动
"""
import shutil
from typing import List, Tuple
from .base import BaseAgentRunner

class AgyRunner(BaseAgentRunner):
    name = "agy"
    display_name = "Google Antigravity CLI"
    binary_name = "agy"
    default_model = "gemini-3.8-flash-high"
    supported_models = [
        "gemini-3.8-flash-high",
        "gemini-3.8-flash-medium",
        "gemini-3.8-flash-low",
        "claude-sonnet-4-6",
        "claude-opus-4-6-thinking",
        "gpt-oss-120b-medium",
    ]

    def check_available(self) -> Tuple[bool, str]:
        path = shutil.which(self.binary_name)
        if not path:
            return False, f"未在环境变量 PATH 中找到 '{self.binary_name}' 命令"
        return True, f"已就绪 ({path})"

    def build_command(self, prompt: str, model: str, image_paths: List[str]) -> List[str]:
        target_model = model or self.default_model
        cmd = [
            self.binary_name,
            "-p",
            prompt,
            "--model",
            target_model,
            "--dangerously-skip-permissions",
            "--disable-slash-commands",
        ]
        return cmd
