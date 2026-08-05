"""
OpenRouter Client Utility (Python)
Compatible with OpenRouter API (e.g., qwen/qwen3.5-9b, qwen/qwen-2.5-coder-32b).
Provides streaming and standard chat completions with reasoning token tracking.
"""

import json
import os
import urllib.request
from typing import List, Dict, Any, Optional, Generator
from core.config import OPENROUTER_API_KEY, OPENROUTER_MODEL
from core.logger import get_logger

logger = get_logger("OpenRouterClient")


class OpenRouterClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY", "")
        self.model = model or OPENROUTER_MODEL or os.getenv("OPENROUTER_MODEL", "qwen/qwen3.5-9b")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.0) -> str:
        """Sends chat request to OpenRouter API and returns full response string."""
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY is empty in .env. Returning offline fallback.")
            return ""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/TruongIKPK/K3-Day9-Multi-Agent-A2A",
            "X-Title": "Multi-Agent Dispute Resolution"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.base_url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                return res_body["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenRouter API request failed: {str(e)}")
            raise e
