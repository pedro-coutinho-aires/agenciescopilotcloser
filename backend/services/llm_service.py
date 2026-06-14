import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LLMService:
    """Unified LLM interface: Claude primary, OpenAI fallback."""

    def __init__(self):
        self._anthropic_client = None
        self._openai_client = None

        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if anthropic_key:
            import anthropic
            self._anthropic_client = anthropic.Anthropic(api_key=anthropic_key)

        if openai_key:
            import openai
            self._openai_client = openai.OpenAI(api_key=openai_key)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048,
    ) -> Optional[str]:
        """Generate text using Claude (primary) or OpenAI (fallback)."""
        # Try Claude first
        if self._anthropic_client:
            try:
                response = self._anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return response.content[0].text
            except Exception as e:
                logger.warning(f"Claude call failed: {e}")

        # Fallback to OpenAI
        if self._openai_client:
            try:
                response = self._openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"OpenAI call failed: {e}")

        logger.error("No LLM available")
        return None


# Singleton
llm = LLMService()
