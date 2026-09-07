import os
import json
from copy import deepcopy
from typing import Protocol

from groq import Groq

from models.schemas import CandidateProfile


PARSER_SYSTEM_PROMPT = """You extract structured facts from a resume.

Use only information explicitly present in the supplied resume text. Never infer
or invent skills, metrics, dates, years of experience, responsibilities,
achievements, technologies, titles, or companies.

The skills list must contain only concise skill or technology names, such as
"SQL", "PostgreSQL", "Data validation", or "Power BI". Do not put project
descriptions, achievements, metrics, responsibilities, or supporting sentences
in skills.

For each project and experience record, put meaningful factual resume points in
the evidence list. Use one meaningful responsibility, achievement, technology,
or claim per string. Keep metrics and concrete claims attached to their point;
do not combine an entire role or project into one paragraph. Preserve wording
close to the resume where practical. Do not create a separate project summary
or description. Leave evidence as an empty list when the resume provides none.

Leave fields empty or null when the resume does not provide the information.
Return the requested CandidateProfile structure only.
"""


def _make_groq_strict_schema(schema: dict) -> dict:
    """Adapt Pydantic JSON Schema to Groq's strict-schema requirements."""
    schema = deepcopy(schema)

    def visit(value: object) -> None:
        if isinstance(value, dict):
            value.pop("default", None)
            properties = value.get("properties")
            if isinstance(properties, dict):
                value["required"] = list(properties)
                value["additionalProperties"] = False
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(schema)
    return schema


def _candidate_profile_response_format() -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "candidate_profile",
            "schema": _make_groq_strict_schema(CandidateProfile.model_json_schema()),
            "strict": True,
        },
    }


class ResumeLLMClient(Protocol):
    def parse_resume(self, resume_text: str) -> CandidateProfile:
        """Parse resume text into a validated candidate profile."""


class GroqResumeClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        resolved_api_key = api_key or os.getenv("GROQ_API_KEY")
        if not resolved_api_key:
            raise ValueError("GROQ_API_KEY is required")

        self._client = Groq(api_key=resolved_api_key)
        self._model = model or os.getenv(
            "JOBPILOT_LLM_MODEL",
            "openai/gpt-oss-120b",
        )

    def parse_resume(self, resume_text: str) -> CandidateProfile:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": PARSER_SYSTEM_PROMPT},
                {"role": "user", "content": resume_text},
            ],
            response_format=_candidate_profile_response_format(),
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("The LLM returned no CandidateProfile content")
        return CandidateProfile.model_validate(json.loads(content))


def parse_resume_text(
    resume_text: str,
    client: ResumeLLMClient | None = None,
) -> CandidateProfile:
    """Parse raw extracted resume text into a validated CandidateProfile."""
    if not resume_text or not resume_text.strip():
        raise ValueError("resume_text must not be empty")

    parser_client = client or GroqResumeClient()
    profile = parser_client.parse_resume(resume_text)
    return CandidateProfile.model_validate(profile)