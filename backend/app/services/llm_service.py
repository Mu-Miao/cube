# app/services/llm_service.py
# LLM 服务封装
# 支持 off / api / local / auto 四种模式
# auto 模式：先试本地模型，LLM_LOCAL_TIMEOUT 秒内没结果就回退到云端 API

import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def _api_endpoint() -> tuple[str, str, str] | None:
    """返回云端 API 的 (base_url, api_key, model)。

    这里就是阿里云百炼 / OpenAI-compatible 云端模型的入口配置：
    - DASHSCOPE_API_KEY 优先，用于你放在 mac 环境变量里的百炼 Key。
    - LLM_API_KEY 保留作兼容旧配置。
    - LLM_API_BASE_URL / LLM_API_MODEL 来自 backend/.env 或环境变量。
    """
    api_key = settings.DASHSCOPE_API_KEY or settings.LLM_API_KEY
    if not api_key:
        return None
    return (
        settings.LLM_API_BASE_URL,
        api_key,
        settings.LLM_API_MODEL,
    )


def _local_endpoint() -> tuple[str, str, str] | None:
    """返回本地模型的 (base_url, api_key, model)"""
    return (
        settings.LLM_LOCAL_BASE_URL,
        "ollama",
        settings.LLM_LOCAL_MODEL,
    )


async def _call(base_url: str, api_key: str, model: str, messages: list[dict], timeout: int) -> Optional[str]:
    """实际调用 OpenAI-compatible 的非流式 chat completions 接口。

    AI 洞察页选择 LLM 时会走这里。对于阿里云百炼来说，最终请求地址是：
    {LLM_API_BASE_URL}/chat/completions
    """
    payload = {
        "model": model,
        "messages": messages,
        "temperature": settings.LLM_TEMPERATURE,
        "max_tokens": settings.LLM_MAX_TOKENS,
    }
    if settings.LLM_API_ENABLE_THINKING:
        # 阿里云百炼 qwen 深度思考模型参数，对应示例里的 extra_body={"enable_thinking": True}。
        payload["enable_thinking"] = True
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            resp = await client.post(
                f"{base_url}/chat/completions", json=payload, headers=headers
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning("LLM 调用失败 [%s]: %s", base_url, e)
        return None


async def _call_local(base_url: str, model: str, messages: list[dict], timeout: int) -> Optional[str]:
    """调用 Ollama 原生 API（支持 think:false 关闭 Qwen3 思考模式）"""
    # base_url 形如 http://localhost:11434/v1，改成 http://localhost:11434
    native_base = base_url.rstrip("/").removesuffix("/v1")
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "temperature": settings.LLM_TEMPERATURE,
            "num_predict": settings.LLM_MAX_TOKENS,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            resp = await client.post(
                f"{native_base}/api/chat", json=payload
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"].strip()
    except Exception as e:
        logger.warning("LLM 本地调用失败 [%s]: %s", native_base, e)
        return None


async def chat(prompt: str, system: Optional[str] = None) -> Optional[str]:
    """
    调用 LLM 生成文本。失败返回 None，调用方自行回退到规则逻辑。

    auto 模式下：先试本地模型（短超时），失败/超时再试云端 API。
    """
    mode = settings.LLM_MODE.lower()
    if mode == "off":
        return None

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    if mode == "local":
        ep = _local_endpoint()
        if not ep:
            return None
        base, _, model = ep
        return await _call_local(base, model, messages, settings.LLM_TIMEOUT)

    if mode == "api":
        ep = _api_endpoint()
        if not ep:
            return None
        base, key, model = ep
        return await _call(base, key, model, messages, settings.LLM_TIMEOUT)

    if mode == "auto":
        # 1. 先试本地，短超时
        local = _local_endpoint()
        if local:
            base, _, model = local
            result = await _call_local(base, model, messages, settings.LLM_LOCAL_TIMEOUT)
            if result:
                logger.info("LLM 命中本地模型")
                return result
            logger.info("本地模型超时或失败，回退到 API")

        # 2. 回退到 API
        api = _api_endpoint()
        if api:
            base, key, model = api
            return await _call(base, key, model, messages, settings.LLM_TIMEOUT)

        return None

    return None


async def chat_api(prompt: str, system: Optional[str] = None) -> Optional[str]:
    """
    使用和 /api/v1/chat/stream 相同的云端 OpenAI 兼容 API 配置生成文本。
    用于用户显式选择 LLM/API 分析的场景，避免和本地 Ollama 路径混用。
    """
    ep = _api_endpoint()
    if not ep:
        return None

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    base, key, model = ep
    return await _call(base, key, model, messages, settings.LLM_TIMEOUT)


def is_enabled() -> bool:
    """LLM 是否启用"""
    mode = settings.LLM_MODE.lower()
    if mode == "off":
        return False
    if mode == "local":
        return _local_endpoint() is not None
    if mode == "api":
        return _api_endpoint() is not None
    if mode == "auto":
        return _local_endpoint() is not None or _api_endpoint() is not None
    return False


async def chat_stream(messages: list[dict]):
    """
    流式调用 LLM，逐块 yield 文本片段。
    用于聊天面板的 SSE 流式输出。
    仅使用云端 API（OpenAI 兼容协议 + stream=True）。
    """
    # 小眠聊天面板的流式回复也使用同一套云端 API 配置。
    ep = _api_endpoint()
    if not ep:
        yield "（LLM 未配置，请在 backend/.env 中设置 LLM_API_KEY）"
        return

    base_url, api_key, model = ep
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "stream": True,
    }
    if settings.LLM_API_ENABLE_THINKING:
        # 流式聊天也把百炼的思考开关带上，模型会先返回 reasoning_content，再返回 content。
        # 当前前端只展示 content，reasoning_content 会被忽略。
        payload["enable_thinking"] = True
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT, trust_env=False) as client:
            async with client.stream(
                "POST",
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                resp.raise_for_status()
                async for raw_line in resp.aiter_lines():
                    line = raw_line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        return
                    try:
                        import json as _json
                        chunk = _json.loads(data)
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            yield content
                    except Exception:
                        pass
    except Exception as e:
        logger.warning("LLM 流式调用失败 [%s]: %s", base_url, e)
        yield f"\n\n（调用出错：{e}）"
