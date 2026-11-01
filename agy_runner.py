"""
agy CLI 异步驱动模块：控制并发信号量、Base64 图片转临时文件、调用 agy 并解析结果
"""
import asyncio
import base64
import os
import shutil
import tempfile
from typing import List, Tuple, Optional
from config import AGY_BIN, DEFAULT_MODEL, REASONING_EFFORT, MAX_CONCURRENCY, TIMEOUT_SECONDS
from prompt_builder import build_prompt
from ocs_matcher import parse_model_json, normalize_answer_for_ocs

# 全局并发信号量，防止大量题目同时打爆本地进程或触发 API 限流
_semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

def _save_base64_images(raw_images: List[str]) -> List[str]:
    """将 Base64 图片保存为本地临时文件，便于多模态模型读取"""
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

async def query_agy(
    q_type: str,
    title: str,
    options: str,
    raw_images: Optional[List[str]] = None,
    model: str = DEFAULT_MODEL,
) -> Tuple[str, str]:
    """
    通过 agy CLI 提问并获取规范化的答案与理由
    """
    if not shutil.which(AGY_BIN):
        return "", f"未找到 '{AGY_BIN}' 命令，请检查环境变量或确认 Antigravity CLI 是否已安装。"

    temp_image_files = _save_base64_images(raw_images or [])

    try:
        prompt = build_prompt(q_type, title, options, temp_image_files)

        cmd = [
            AGY_BIN,
            "-p",
            prompt,
            "--model",
            model,
            "--dangerously-skip-permissions",
            "--disable-slash-commands",
        ]
        if REASONING_EFFORT and REASONING_EFFORT.strip():
            cmd.extend(["--effort", REASONING_EFFORT.strip()])

        async with _semaphore:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                return "", f"调用 agy 超时（限制 {TIMEOUT_SECONDS} 秒）"

            if proc.returncode != 0:
                err_msg = stderr_data.decode("utf-8", errors="ignore").strip()
                return "", f"agy 退出异常 (code {proc.returncode}): {err_msg[:200]}"

            raw_output = stdout_data.decode("utf-8", errors="ignore").strip()
            raw_answer, reason = parse_model_json(raw_output)

            # 根据 OCS 规则严格规范化
            final_answer = normalize_answer_for_ocs(q_type, raw_answer, options)
            return final_answer, reason

    finally:
        _cleanup_temp_files(temp_image_files)
