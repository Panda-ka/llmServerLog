import json
import time
from datetime import datetime
import asyncio
import logging
from urllib.parse import urljoin
import os

from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import httpx
import uvicorn

# === 配置区 ===
VLLM_BACKEND_URL = "http://192.168.1.1:8000/"
PROXY_PORT = 8000

current_time = datetime.now().strftime("%y%m%d")
LOG_FILE_PATH = f"./Log/openai_log_server_{current_time}.log"
os.makedirs("./Log", exist_ok=True)

LOGGABLE_PATHS = {
    "/v1/chat/completions",
    "/v1/completions",
}

app = FastAPI(title="Full OpenAI-compatible vLLM Proxy with Full Logging")

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy(request: Request, path: str):
    start_time = time.time()
    target_url = urljoin(VLLM_BACKEND_URL.rstrip("/") + "/", path.lstrip("/"))

    raw_body = await request.body()

    log_this = False
    user_prompt = "<not logged>"
    req_data = None

    if request.method in ("POST", "PUT") and f"/{path}" in LOGGABLE_PATHS:
        try:
            req_data = json.loads(raw_body)
            user_prompt = extract_prompt(req_data, path)
            log_this = True
        except Exception as e:
            logging.warning(f"Failed to parse request for logging: {e}")

    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}

    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=target_url,
                content=raw_body,
                headers=headers,
                params=request.query_params,
            )
        except Exception as e:
            return Response(content=f"Proxy error: {e}", status_code=502)

        # === 非流式：立即记录===
        if log_this and resp.status_code == 200:
            is_stream = bool(req_data and req_data.get("stream", False))
            if not is_stream:
                try:
                    resp_json = resp.json()
                    assistant_reply = extract_response(resp_json, path)
                    log_entry = {
                        "timestamp": datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{datetime.now().microsecond // 1000:03d}",
                        "path": f"/{path}",
                        "prompt": user_prompt,
                        "response": assistant_reply,
                        "stream": False,
                        "latency_sec": round(time.time() - start_time, 3),
                        "status_code": resp.status_code,
                    }
                    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                except Exception as e:
                    logging.error(f"Failed to log non-streaming response: {e}")

        # === 响应转发 ===
        if (
            resp.headers.get("transfer-encoding") == "chunked"
            or "text/event-stream" in resp.headers.get("content-type", "")
        ):
            # 流式响应：缓冲 chunks 用于日志
            full_content_lines = []

            async def stream_gen():
                async for chunk in resp.aiter_bytes():
                    yield chunk
                    # 尝试解码并提取 content（仅用于日志）
                    try:
                        chunk_str = chunk.decode("utf-8")
                        for line in chunk_str.splitlines():
                            if line.startswith("data: ") and line != "data: [DONE]":
                                data_part = line[6:]  # 移除 "data: "
                                if data_part.strip():
                                    try:
                                        delta = json.loads(data_part)
                                        content = delta.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                        if content:
                                            full_content_lines.append(content)
                                    except:
                                        pass
                    except UnicodeDecodeError:
                        pass  # 忽略无法解码的 chunk

                # 🌟 所有 chunks 发送完毕后，写入日志（在后台任务中）
                if log_this and resp.status_code == 200:
                    final_response = "".join(full_content_lines)
                    try:
                        log_entry = {
                            "timestamp": datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{datetime.now().microsecond // 1000:03d}",
                            "path": f"/{path}",
                            "prompt": user_prompt,
                            "response": final_response if final_response else "<empty response>",
                            "stream": True,
                            "latency_sec": round(time.time() - start_time, 3),
                            "status_code": resp.status_code,
                        }
                        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                    except Exception as e:
                        logging.error(f"Failed to log streaming response: {e}")

            return StreamingResponse(
                stream_gen(),
                status_code=resp.status_code,
                headers=dict(resp.headers),
            )
        else:
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers),
            )


# --- 工具函数---
def extract_prompt(data, path: str):
    if "/chat/completions" in path:
        messages = data.get("messages", [])
        return "\n".join(f"[{m.get('role')}]: {m.get('content')}" for m in messages)
    elif "/completions" in path:
        prompt = data.get("prompt", "")
        return str(prompt)[:500] + "..." if isinstance(prompt, str) and len(prompt) > 500 else str(prompt)
    return "<unknown prompt>"


def extract_response(data, path: str):
    try:
        if "/chat/completions" in path:
            return data["choices"][0]["message"]["content"]
        elif "/completions" in path:
            return data["choices"][0]["text"]
    except (KeyError, IndexError, TypeError):
        pass
    return "<unable to extract>"


# --- 主程序 ---
if __name__ == "__main__":
    print(f"🚀 Starting FULL vLLM proxy on port {PROXY_PORT}")
    print(f"📡 Backend: {VLLM_BACKEND_URL}")
    print(f"📝 Logged paths: {sorted(LOGGABLE_PATHS)}")
    print(f"📄 Log file: {LOG_FILE_PATH}\n")

    uvicorn.run(app, host="0.0.0.0", port=PROXY_PORT, log_level="info")