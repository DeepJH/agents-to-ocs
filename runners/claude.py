"""
Anthropic Claude Code CLI 驱动
"""
import shutil
from typing import List, Tuple
from .base import BaseAgentRunner

class ClaudeRunner(BaseAgentRunner):
    name = "claude"
    display_name = "Anthropic Claude Code"
    binary_name = "claude"
    default_model = "sonnet"
    supported_models = [
        "sonnet",
        "haiku",
        "opus",
        "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
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
            "--dangerously-skip-permissions",
        ]
        if target_model:
            cmd.extend(["--model", target_model])
        return cmd
