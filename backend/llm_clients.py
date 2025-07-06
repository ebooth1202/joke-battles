import os
import aiohttp
import logging
import ssl
from typing import Optional

logger = logging.getLogger(__name__)


class LLMClients:
    def __init__(self):
        # API keys from environment variables
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")  # For Gemini
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # Create SSL context that ignores certificate verification for development
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        # Validate required API keys
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not found in environment")
        if not self.anthropic_api_key:
            logger.warning("ANTHROPIC_API_KEY not found in environment")
        if not self.google_api_key:
            logger.warning("GOOGLE_API_KEY not found in environment")

    async def generate_openai_joke(self, context: str) -> str:
        """Generate joke using OpenAI GPT"""
        if not self.openai_api_key:
            return "OpenAI API key not configured"

        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                }

                data = {
                    "model": "gpt-3.5-turbo",  # More reliable and cheaper than gpt-4
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a comedian. Generate a single, clean, funny joke based on the user's request. Keep it under 200 characters."
                        },
                        {
                            "role": "user",
                            "content": f"Tell me {context}"
                        }
                    ],
                    "max_tokens": 150,
                    "temperature": 0.9
                }

                async with session.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers=headers,
                        json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"].strip()
                    else:
                        logger.error(f"OpenAI API error: {response.status}")
                        return "OpenAI is having trouble thinking of jokes right now!"

        except Exception as e:
            logger.error(f"OpenAI joke generation error: {e}")
            return "OpenAI took a comedy break!"

    async def generate_anthropic_joke(self, context: str) -> str:
        """Generate joke using Anthropic Claude"""
        if not self.anthropic_api_key:
            return "Anthropic API key not configured"

        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                headers = {
                    "x-api-key": self.anthropic_api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }

                data = {
                    "model": "claude-3-5-sonnet-20241022",  # Updated to current model
                    "max_tokens": 150,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Generate a single, clean, funny joke about: {context}. Keep it under 200 characters and make it genuinely funny!"
                        }
                    ]
                }

                async with session.post(
                        "https://api.anthropic.com/v1/messages",
                        headers=headers,
                        json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["content"][0]["text"].strip()
                    else:
                        logger.error(f"Anthropic API error: {response.status}")
                        return "Claude is busy perfecting its comedy routine!"

        except Exception as e:
            logger.error(f"Anthropic joke generation error: {e}")
            return "Claude needs more joke practice!"

    async def generate_gemini_joke(self, context: str) -> str:
        """Generate joke using Google Gemini"""
        if not self.google_api_key:
            return "Google API key not configured"

        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.google_api_key}"

                data = {
                    "contents": [{
                        "parts": [{
                            "text": f"Generate a single, clean, funny joke about: {context}. Keep it under 200 characters and make it witty!"
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.9,
                        "maxOutputTokens": 150
                    }
                }

                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
                    else:
                        logger.error(f"Gemini API error: {response.status}")
                        return "Gemini is stargazing instead of joke-making!"

        except Exception as e:
            logger.error(f"Gemini joke generation error: {e}")
            return "Gemini got lost in the comedy cosmos!"

    async def generate_llama_joke(self, context: str) -> str:
        """Generate joke using Ollama (Llama)"""
        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                data = {
                    "model": "llama3.2",  # Using your installed model
                    "prompt": f"Generate a single, clean, funny joke about: {context}. Keep it under 200 characters.",
                    "stream": False,
                    "options": {
                        "temperature": 0.9,
                        "num_predict": 150
                    }
                }

                async with session.post(
                        f"{self.ollama_base_url}/api/generate",
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["response"].strip()
                    else:
                        logger.error(f"Ollama API error: {response.status}")
                        return "Llama is busy grazing on comedy grass!"

        except aiohttp.ClientError as e:
            logger.error(f"Ollama connection error: {e}")
            return "Llama wandered off from the comedy farm!"
        except Exception as e:
            logger.error(f"Llama joke generation error: {e}")
            return "Llama is taking a humor siesta!"

    async def test_connections(self) -> dict:
        """Test all LLM connections"""
        results = {}

        # Test each service with a simple request
        test_context = "testing"

        try:
            results["openai"] = await self.generate_openai_joke(test_context)
        except Exception as e:
            results["openai"] = f"Error: {e}"

        try:
            results["anthropic"] = await self.generate_anthropic_joke(test_context)
        except Exception as e:
            results["anthropic"] = f"Error: {e}"

        try:
            results["gemini"] = await self.generate_gemini_joke(test_context)
        except Exception as e:
            results["gemini"] = f"Error: {e}"

        try:
            results["llama"] = await self.generate_llama_joke(test_context)
        except Exception as e:
            results["llama"] = f"Error: {e}"

        return results