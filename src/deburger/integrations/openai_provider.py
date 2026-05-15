"""OpenAI provider implementation."""

import json
from typing import List, Optional

from openai import AsyncOpenAI

from deburger.models.error import ErrorInfo
from deburger.models.fix import Fix, CodeChange


class OpenAIProvider:
    """OpenAI GPT-4 provider for fix generation."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-4, gpt-3.5-turbo, etc.)
        """
        self.name = "openai"
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_fixes(
        self,
        error: ErrorInfo,
        max_candidates: int = 3
    ) -> List[Fix]:
        """Generate fix candidates using OpenAI."""
        prompt = self._build_prompt(error, max_candidates)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Python debugger. Generate fix candidates for code errors."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            content = response.choices[0].message.content
            if not content:
                return []

            return self._parse_response(content)

        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")

    def _build_prompt(self, error: ErrorInfo, max_candidates: int) -> str:
        """Build prompt for fix generation."""
        return f"""Generate {max_candidates} fix candidates for this Python error.

Error Type: {error.error_type}
Error Message: {error.message}
File: {error.file_path}:{error.line_number}
Function: {error.function_name}

Code Context:
{error.code_context}

Requirements:
1. Each fix must be valid Python syntax
2. Make minimal changes to fix the error
3. Explain why the fix works
4. Estimate confidence (0.0 to 1.0)

Respond ONLY with valid JSON in this exact format:
{{
  "fixes": [
    {{
      "id": 1,
      "explanation": "Brief explanation of the fix",
      "changes": [
        {{
          "file_path": "{error.file_path}",
          "line_start": {error.line_number},
          "line_end": {error.line_number},
          "old_code": "original code",
          "new_code": "fixed code"
        }}
      ],
      "confidence": 0.95,
      "reasoning": "Why this fix works"
    }}
  ]
}}
"""

    def _parse_response(self, content: str) -> List[Fix]:
        """Parse JSON response from OpenAI."""
        try:
            # Extract JSON from response (may have markdown code blocks)
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()

            data = json.loads(content)
            fixes = []

            for fix_data in data.get("fixes", []):
                changes = []
                for change_data in fix_data.get("changes", []):
                    changes.append(CodeChange(
                        file_path=change_data["file_path"],
                        line_start=change_data["line_start"],
                        line_end=change_data["line_end"],
                        old_code=change_data["old_code"],
                        new_code=change_data["new_code"],
                    ))

                fixes.append(Fix(
                    id=fix_data["id"],
                    explanation=fix_data["explanation"],
                    changes=changes,
                    confidence=fix_data["confidence"],
                    reasoning=fix_data["reasoning"],
                ))

            return fixes

        except (json.JSONDecodeError, KeyError) as e:
            raise Exception(f"Failed to parse OpenAI response: {e}")
