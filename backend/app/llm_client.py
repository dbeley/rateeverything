"""DeepSeek LLM API client"""
from app.config import get_settings
from typing import Optional
import httpx
import json
import logging

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """Client for DeepSeek API — create per use, not singleton"""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.deepseek_api_key_from_file
        self.base_url = settings.deepseek_base_url
        self.model = getattr(settings, 'deepseek_model', 'deepseek-chat')

    async def chat(self, messages: list[dict], temperature: float = 0.3,
                   response_format: Optional[dict] = None) -> str:
        """Send a chat completion request"""
        if not self.api_key:
            logger.warning("No DeepSeek API key configured, skipping LLM call")
            return "{}"

        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096,
        }
        if response_format:
            body["response_format"] = response_format

        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        ) as client:
            try:
                response = await client.post("/chat/completions", json=body)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                logger.error(f"DeepSeek API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"DeepSeek API call failed: {e}")
                raise

    async def chat_json(self, messages: list[dict], temperature: float = 0.3) -> dict:
        """Send a chat completion request and parse JSON response"""
        content = await self.chat(
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        # Clean markdown code fences if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        if not content:
            return {}
        return json.loads(content)


def get_llm_client() -> DeepSeekClient:
    """Factory: creates a fresh client each time (no singleton issues)"""
    return DeepSeekClient()
