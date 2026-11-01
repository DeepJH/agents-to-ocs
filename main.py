"""
FastAPI 主服务模块：agent-to-ocs
连接各类本地 AI Agent CLI (agy, claude, codex) 与 OCS 网课助手题库接口
全面兼容 OCS 网课助手的测速 (HEAD)、搜题 (GET/POST/Form/JSON) 及各种 handler 规范
"""
import json
import urllib.parse
import uvicorn
from contextlib import asynccontextmanager
from typing import List, Dict, Any
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import (
    HOST,
    PORT,
    AGENT_NAME,
    MODEL_NAME,
    MAX_CONCURRENCY,
    TIMEOUT_SECONDS,
    runner_instance,
)
from cache_store import cache
from agent_runner import query_agent

def get_ocs_wrapper_config(base_url: str = f"http://{HOST}:{PORT}") -> List[Dict[str, Any]]:
    """生成给 OCS 网课助手一键导入的题库配置 JSON"""
    return [
        {
            "name": f"Agent 智能题库 ({AGENT_NAME.upper()} - {MODEL_NAME})",
            "homepage": "https://github.com/DeepJH/agent-to-ocs",
            "url": f"{base_url}/ocs",
            "method": "post",
            "type": "fetch",
            "contentType": "json",
            "responseType": "json",
            "headers": {
                "Content-Type": "application/json"
            },
            "data": {
                "title": "${title}",
                "options": "${options}",
                "type": "${type}",
                "images": {
                    "handler": "return (env) => Array.isArray(env.images) ? env.images : []"
                }
            },
            "handler": "return (res) => (res && res.answer) ? [res.title, res.answer] : undefined"
        }
    ]

@asynccontextmanager
async def lifespan(app: FastAPI):
    config_json = json.dumps(get_ocs_wrapper_config(), indent=2, ensure_ascii=False)
    print("\n" + "=" * 70)
    print("  🚀 agent-to-ocs 智能题库服务已成功启动！")
    print(f"  • 服务地址 : http://{HOST}:{PORT}")
    print(f"  • 题库端点 : http://{HOST}:{PORT}/ocs (兼容 /, /search, /query)")
    print(f"  • Agent驱动: {runner_instance.display_name} ({AGENT_NAME})")
    print(f"  • 推理模型 : {MODEL_NAME}")
    print(f"  • 并发限制 : {MAX_CONCURRENCY} 个进程并发")
    print("=" * 70)
    print("【OCS 网课助手一键配置代码】（直接复制下方整段 JSON 填入 OCS 题库配置中）：")
    print("-" * 70)
    print(config_json)
    print("-" * 70)
    print("💡 填写位置：OCS 悬浮窗 → 通用 → 全局设置 → 题库配置")
    print("💡 若遇到带图题目，请在 OCS 设置中确保开启【图片题优化】选项。")
    print("=" * 70 + "\n")
    yield

app = FastAPI(
    title="agent-to-ocs Bridge Service",
    description="将本地各 AI Agent CLI (agy, claude code, codex) 转化为 OCS 网课助手智能题库的桥接程序",
    version="2.0.0",
    lifespan=lifespan,
)

# 开放全量 CORS 跨域，支持预检 OPTIONS 及任意来源访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def build_ocs_response(code: int, title: str, answer: str, reason: str, cached: bool) -> Dict[str, Any]:
    """
    构造超级兼容的应答字典：同时满足各种 OCS handler 提取方式
    (res.answer / res.question / res.data.answer / res.answers 数组全覆盖)
    """
    ans_str = str(answer or "").strip()
    answers_list = [a.strip() for a in ans_str.split("#") if a.strip()] if ans_str else []

    payload = {
        "code": code,
        "status": 200 if code == 1 else 404,
        "success": code == 1,
        "agent": AGENT_NAME,
        "model": MODEL_NAME,
        "title": title,
        "question": title,
        "answer": ans_str,
        "answers": answers_list,
        "reason": reason,
        "cached": cached,
        "data": {
            "title": title,
            "question": title,
            "answer": ans_str,
            "answers": answers_list,
            "reason": reason,
            "cached": cached,
            "agent": AGENT_NAME,
            "model": MODEL_NAME,
        }
    }
    return payload

async def extract_request_params(request: Request) -> Dict[str, Any]:
    """
    智能提取参数：无缝兼容 JSON 请求体、Form 表单、以及 URL Query 参数
    """
    title = ""
    options = ""
    q_type = "single"
    images: List[str] = []

    # 1. 尝试从 Query 参数取值
    query_params = request.query_params
    title = query_params.get("title") or query_params.get("question") or query_params.get("q") or ""
    options = query_params.get("options") or query_params.get("option") or ""
    q_type = query_params.get("type") or q_type

    # 2. 如果是 POST 请求，解析请求体 (自适应 JSON、表单 x-www-form-urlencoded 或 raw 格式)
    if request.method.upper() == "POST":
        try:
            raw_body = await request.body()
            if raw_body:
                raw_text = raw_body.decode("utf-8", errors="ignore").strip()
                try:
                    body_obj = json.loads(raw_text)
                except Exception:
                    parsed = urllib.parse.parse_qs(raw_text)
                    if parsed:
                        body_obj = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in parsed.items()}
                    else:
                        body_obj = None
        except Exception:
            body_obj = None

        if isinstance(body_obj, dict):
            src = body_obj.get("data") if isinstance(body_obj.get("data"), dict) else body_obj
            title = src.get("title") or src.get("question") or src.get("q") or title
            options = src.get("options") or src.get("option") or options
            q_type = src.get("type") or q_type

            raw_images = src.get("images") or src.get("image") or []
            if isinstance(raw_images, list):
                images.extend([str(im).strip() for im in raw_images if isinstance(im, str) and im.strip()])
            elif isinstance(raw_images, str) and raw_images.strip():
                images.append(raw_images.strip())

    return {
        "title": str(title).strip(),
        "options": str(options).strip(),
        "type": str(q_type).strip().lower() if q_type else "single",
        "images": images,
    }

async def handle_search_or_ping(request: Request):
    """
    通用请求处理器：支持 HEAD 测速、健康检查与题目搜索
    """
    # 如果是 HEAD 请求（OCS 测速刷新专用）
    if request.method.upper() == "HEAD":
        return Response(status_code=200, headers={"X-Service": "agent-to-ocs", "Access-Control-Allow-Origin": "*"})

    params = await extract_request_params(request)
    title = params["title"]
    options = params["options"]
    q_type = params["type"]
    images = params["images"]

    # 探活或普通网页访问
    if not title and not images:
        return JSONResponse(content={
            "status": "online",
            "service": "agent-to-ocs",
            "agent": AGENT_NAME,
            "agent_display": runner_instance.display_name,
            "model": MODEL_NAME,
            "cached_count": cache.count(),
            "message": "agent-to-ocs 服务正常运行中",
        })

    # 1. 查询本地 SQLite 缓存（毫秒级直出）
    cached_record = cache.get(q_type, title, options)
    if cached_record and cached_record.get("answer"):
        return JSONResponse(content=build_ocs_response(
            code=1,
            title=title,
            answer=cached_record["answer"],
            reason=cached_record.get("reason", "来自本地题库缓存"),
            cached=True,
        ))

    # 2. 未命中缓存，调用当前配置的 Agent 推理
    answer, reason = await query_agent(
        q_type=q_type,
        title=title,
        options=options,
        raw_images=images,
        agent_name=AGENT_NAME,
        model=MODEL_NAME,
        concurrency=MAX_CONCURRENCY,
        timeout_seconds=TIMEOUT_SECONDS,
    )

    if answer:
        cache.set(
            q_type=q_type,
            title=title,
            options=options,
            answer=answer,
            reason=reason,
            model=f"{AGENT_NAME}:{MODEL_NAME}",
        )
        return JSONResponse(content=build_ocs_response(
            code=1,
            title=title,
            answer=answer,
            reason=reason,
            cached=False,
        ))
    else:
        return JSONResponse(content=build_ocs_response(
            code=0,
            title=title,
            answer="",
            reason=reason or "未能获取有效答案",
            cached=False,
        ))

# 多路由全映射：支持 /, /ocs, /search, /query 全路径和 HEAD/GET/POST
@app.api_route("/", methods=["GET", "POST", "HEAD"])
@app.api_route("/ocs", methods=["GET", "POST", "HEAD"])
@app.api_route("/search", methods=["GET", "POST", "HEAD"])
@app.api_route("/query", methods=["GET", "POST", "HEAD"])
@app.api_route("/health", methods=["GET", "HEAD"])
async def universal_endpoint(request: Request):
    return await handle_search_or_ping(request)

@app.get("/ocs-config")
async def export_config():
    """返回 OCS 格式的配置 JSON 对象"""
    return get_ocs_wrapper_config()

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
