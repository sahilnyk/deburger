"""LLM client with provider abstraction and guardrails."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    provider: str
    api_key: str
    model: str
    guardrails: list[str]


class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = self._initialize_client()

    def _initialize_client(self):
        if self.config.provider == "openai":
            import openai
            return openai.OpenAI(api_key=self.config.api_key)
        elif self.config.provider == "anthropic":
            import anthropic
            return anthropic.Anthropic(api_key=self.config.api_key)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    def generate_guidance(self, context: dict) -> str:
        prompt = self._build_guidance_prompt(context)

        if self._violates_guardrails(prompt):
            return "Guidance request violates configured guardrails"

        return self._call_llm(prompt)

    def _build_guidance_prompt(self, context: dict) -> str:
        guardrails_text = "\n".join(f"- {g}" for g in self.config.guardrails)

        return f"""You are analyzing code changes for quality and requirement alignment.

Context:
- Progress: {context.get('progress', 0)}%
- Security Issues: {context.get('security_count', 0)}
- Next Focus: {context.get('next_focus', 'Unknown')}

Guardrails (MUST follow):
{guardrails_text}

Provide specific, actionable guidance for the next steps.
"""

    def _violates_guardrails(self, prompt: str) -> bool:
        forbidden = [
            "ignore previous",
            "jailbreak",
            "bypass security",
            "disable validation",
        ]
        return any(phrase in prompt.lower() for phrase in forbidden)

    def _call_llm(self, prompt: str) -> str:
        if self.config.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )
            return response.choices[0].message.content
        elif self.config.provider == "anthropic":
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        return ""
