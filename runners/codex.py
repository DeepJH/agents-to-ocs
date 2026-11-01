"""
OpenAI Codex CLI 驱动
"""
import shutil
from typing import List, Tuple
from .base import BaseAgentRunner

class CodexRunner(BaseAgentRunner):
    name = "codex"
    display_name = "OpenAI Codex CLI"
    binary_name = "codex"
    default_model = "o3"
    supported_models = [
        "o3",
        "o3-mini",
        "gpt-4o",
        "gpt-4.5-preview",
        "o1",
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
            "exec",
            prompt,
            "--dangerously-bypass-approvals-and-sandbox",
            "--ephemeral",
        ]
        if target_model:
            cmd.extend(["-m", target_model])
        # Codex 原生支持 -i / --image 传入图片文件
        if image_paths:
            for img in image_paths:
                cmd.extend(["-i", img])
        return cmd
