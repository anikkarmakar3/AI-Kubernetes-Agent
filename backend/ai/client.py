from __future__ import annotations

import asyncio
import json

import httpx
from loguru import logger

from core.config import settings


async def request_diagnosis(system_prompt: str, user_prompt: str) -> dict | None:
    api_key = settings.openrouter_api_key or settings.openai_api_key
    model = settings.openrouter_model or settings.openai_model
    if not api_key or not model:
        return None
    is_openrouter = bool(settings.openrouter_api_key)
    base_url = "https://openrouter.ai/api/v1" if is_openrouter else "https://api.openai.com/v1"
    logger.info("Requesting diagnosis from {} using model {}", "OpenRouter" if is_openrouter else "OpenAI", model)
    payload = {"model": model, "temperature": 0, "response_format": {"type": "json_object"}, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if is_openrouter:
        headers.update({"HTTP-Referer": "http://localhost:3000", "X-Title": "AI Kubernetes Agent"})
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=settings.openrouter_timeout_seconds) as client:
                response = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
                content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                diagnosis = json.loads(content)
                logger.info("LLM diagnosis received successfully")
                return diagnosis
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError) as exc:
            logger.warning("OpenRouter attempt {} failed: {}", attempt + 1, exc)
            if attempt < 2:
                await asyncio.sleep(2**attempt)
    logger.warning("LLM diagnosis unavailable; using local fallback")
    return None
