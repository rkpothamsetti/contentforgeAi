"""Thin wrapper around the Groq API for LLM calls."""

from __future__ import annotations
import os, asyncio
from dotenv import load_dotenv

load_dotenv()

_client = None


def _get_client():
    global _client
    if _client is None:
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not set. Create a .env file with your key."
            )
        _client = Groq(api_key=api_key)
    return _client


async def generate(prompt: str, temperature: float = 0.7) -> str:
    """Call Groq and return the text response."""
    client = _get_client()
    response = await asyncio.to_thread(
        client.chat.completions.create,
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=4096,
    )
    return response.choices[0].message.content
