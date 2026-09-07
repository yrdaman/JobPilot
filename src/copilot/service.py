import json
import os
from typing import Any

from groq import Groq


COPILOT_SYSTEM_PROMPT = """You are JobPilot, an evidence-grounded job application
copilot.

Your job is to help a candidate understand a specific job opportunity using
their resume evidence and the analysis already performed.

Rules:
1) Use only provided context (profile, JD requirements, match results, fit, chat history).
2) Do not invent any skills, experience, metrics, tools, qualifications, or requirements.
3) “no_evidence” means the resume does not show support — not that the candidate lacks it.
4) Distinguish required vs preferred requirements.
5) Answer the user’s question directly, concisely, and with evidence when helpful.
6) Do not recalculate analysis unless explicitly asked.
7) If context is insufficient, say so clearly.
8) For “Should I apply?” clearly mention required requirements with no evidence.
9) Resume advice must only strengthen/clarify existing evidence; no unsupported claims.
10) Learning suggestions are allowed only as future goals, not current qualifications.
11) Never suggest fabricating projects, metrics, certifications, or experience.
"""


class JobPilotCopilot:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        resolved_api_key = api_key or os.getenv("GROQ_API_KEY")

        if not resolved_api_key:
            raise ValueError("GROQ_API_KEY is required")

        self._client = Groq(api_key=resolved_api_key)

        self._model = model or os.getenv(
            "JOBPILOT_LLM_MODEL",
            "openai/gpt-oss-120b",
        )

    def answer(
        self,
        question: str,
        analysis: dict[str, Any],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:
        """Answer a user question using existing JobPilot analysis."""

        if not question or not question.strip():
            raise ValueError("question must not be empty")

        context = json.dumps(
            analysis,
            indent=2,
            ensure_ascii=False,
        )

        messages = [
            {
                "role": "system",
                "content": COPILOT_SYSTEM_PROMPT,
            },
            {
                "role": "system",
                "content": (
                    "Here is the existing JobPilot analysis. "
                    "Use it as the primary source of truth:\n\n"
                    f"{context}"
                ),
            },
        ]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
        )

        answer = response.choices[0].message.content

        if not answer:
            raise ValueError("The LLM returned an empty answer")

        return answer.strip()