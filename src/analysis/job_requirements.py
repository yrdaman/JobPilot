import json
import os
from copy import deepcopy
from typing import Protocol

from groq import Groq

from models.job_schemas import JobRequirements


REQUIREMENTS_SYSTEM_PROMPT = """Extract requirements explicitly stated in the job description.

The job description is the only source of truth. Do not invent, infer, strengthen,
or add requirements that are not stated. Do not add common industry expectations,
technologies, years of experience, education, responsibilities, salary, location,
or work-mode requirements unless they are explicitly stated and represented by
the output schema.

For every extracted requirement:
- Keep the requirement faithful to the job description.
- Classify it using only these categories:
    - "education": degrees, academic qualifications, CGPA, or percentages.
    - "technical_skill": technologies, languages, databases, tools, frameworks,
        or explicit technical knowledge.
    - "experience": explicit years of experience or specific prior experience.
    - "competency": communication, teamwork, problem solving, logical thinking,
        learning attitude, responsibility, or similar personal competencies.
    - "application": who is encouraged to apply, portfolio/GitHub preferences,
        or similar application guidance.
    - "other": relevant JD information outside these categories, including
        internship duration, location, and type/logistics.
- Set importance to "required" only when the JD clearly marks it as required,
  mandatory, or equivalent.
- Set importance to "preferred" only when the JD clearly marks it as preferred,
  nice-to-have, or equivalent.
- Use "unspecified" when the JD does not clearly indicate importance.
- Copy the relevant original JD wording into evidence.

If the JD does not mention a technology or qualification, do not add it. Return
only the requested JobRequirements structure.
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


def _job_requirements_response_format() -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "job_requirements",
            "schema": _make_groq_strict_schema(JobRequirements.model_json_schema()),
            "strict": True,
        },
    }


class JobRequirementsLLMClient(Protocol):
    def extract_requirements(self, jd_text: str) -> JobRequirements:
        """Extract explicit requirements from job description text."""


class GroqJobRequirementsClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        resolved_api_key = api_key or os.getenv("GROQ_API_KEY")
        if not resolved_api_key:
            raise ValueError("GROQ_API_KEY is required")

        self._client = Groq(api_key=resolved_api_key)
        self._model = model or os.getenv(
            "JOBPILOT_LLM_MODEL",
            "openai/gpt-oss-120b",
        )

    def extract_requirements(self, jd_text: str) -> JobRequirements:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": REQUIREMENTS_SYSTEM_PROMPT},
                {"role": "user", "content": jd_text},
            ],
            response_format=_job_requirements_response_format(),
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("The LLM returned no JobRequirements content")
        return JobRequirements.model_validate(json.loads(content))


def extract_job_requirements(
    jd_text: str,
    client: JobRequirementsLLMClient | None = None,
) -> JobRequirements:
    """Extract explicit requirements from raw job description text."""
    if not jd_text or not jd_text.strip():
        raise ValueError("jd_text must not be empty")

    extractor_client = client or GroqJobRequirementsClient()
    requirements = extractor_client.extract_requirements(jd_text)
    return JobRequirements.model_validate(requirements)