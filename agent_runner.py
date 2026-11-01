"""
通用 Agent 异步调度与执行器
支持 agy、claude code、codex 等多种 CLI Agent，负责并发控制、多模态处理与答案自检
"""
import asyncio
import base64
import os
import tempfile
from typing import List, Tuple, Optional

from runners import get_runner
from prompt_builder import build_prompt
from ocs_matcher import parse_model_json, normalize_answer_for_ocs

# 信号量将在服务初始化时根据配置动态创建或复用
_semaphore = None

def get_semaphore(concurrency: int) -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(concurrency)
    return _semaphore

def _save_base64_images(raw_images: List[str]) -> List[str]:
    """将 Base64 图片保存为本地临时文件，便于多模态 Agent 读取"""
    saved_paths = []
    for idx, raw in enumerate(raw_images):
        if not isinstance(raw, str) or not raw.strip():
            continue
        s = raw.strip()
        ext = ".png"
        if s.startswith("data:image/"):
            try:
                header, s = s.split(";base64,", 1)
                mime = header.replace("data:image/", "")
                if "/" in mime:
                    mime = mime.split("/")[0]
                if mime.lower() in ("jpeg", "jpg"):
                    ext = ".jpg"
                elif mime.lower() == "webp":
                    ext = ".webp"
                elif mime.lower() == "gif":
                    ext = ".gif"
            except Exception:
                pass
        try:
            img_data = base64.b64decode(s)
            tmp = tempfile.NamedTemporaryFile(prefix=f"ocs_img_{idx}_", suffix=ext, delete=False)
            tmp.write(img_data)
            tmp.close()
            saved_paths.append(tmp.name)
        except Exception as e:
            print(f"[警告] 题目图片 Base64 解码失败: {e}")
    return saved_paths

def _cleanup_temp_files(paths: List[str]):
    """清理临时图片文件"""
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

async def query_agent(
    q_type: str,
    title: str,
    options: str,
    raw_images: Optional[List[str]] = None,
    agent_name: str = "agy",
    model: str = "",
    concurrency: int = 3,
    timeout_seconds: int = 50,
) -> Tuple[str, str]:
    """
    通过指定的 Agent CLI 提问并获取规范化答案与理由
    """
    try:
        runner = get_runner(agent_name)
    except Exception as e:
        return "", str(e)

    ok, status_msg = runner.check_available()
    if not ok:
        return "", f"Agent '{agent_name}' 不可用: {status_msg}"

    target_model = model or runner.default_model
    temp_image_files = _save_base64_images(raw_images or [])
    sem = get_semaphore(concurrency)

    try:
        prompt = build_prompt(q_type, title, options, temp_image_files)
        cmd = runner.build_command(prompt, target_model, temp_image_files)

        async with sem:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                return "", f"调用 Agent ({agent_name}) 超时（限制 {timeout_seconds} 秒）"

            if proc.returncode != 0:
                err_msg = stderr_data.decode("utf-8", errors="ignore").strip()
                if not err_msg:
                    err_msg = stdout_data.decode("utf-8", errors="ignore").strip()
                return "", f"Agent ({agent_name}) 退出异常 (code {proc.returncode}): {err_msg[:300]}"

            raw_output = stdout_data.decode("utf-8", errors="ignore").strip()
            raw_answer, reason = parse_model_json(raw_output)

            # 根据 OCS 规则严格规范化
            final_answer = normalize_answer_for_ocs(q_type, raw_answer, options)
            return final_answer, reason

    finally:
        _cleanup_temp_files(temp_image_files)
