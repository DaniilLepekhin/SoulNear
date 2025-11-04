"""
GPT Service - Wrapper for OpenAI API calls

Simple wrapper to keep adaptive_quiz_service independent of direct OpenAI client usage.
"""

import json
import logging
from typing import Optional
from openai import AsyncOpenAI

from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)


class GPTService:
    """
    Service for GPT API calls with json_mode support.
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    async def generate_completion(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        json_mode: bool = False
    ) -> str:
        """
        Generate GPT completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (default: gpt-4o-mini)
            temperature: Sampling temperature
            json_mode: Enable JSON output mode
            
        Returns:
            Response content as string (JSON if json_mode=True)
        """
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            
            # Validate JSON if json_mode
            if json_mode:
                try:
                    json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from GPT: {e}")
                    logger.error(f"Response: {content}")
                    raise
            
            return content
            
        except Exception as e:
            logger.error(f"GPT API call failed: {e}")
            raise

