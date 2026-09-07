import json
import os
from typing import Any, Protocol

from groq import Groq
from models.matching import EvidenceClassification


CLASSIFIER_SYSTEM_PROMPT = """You are an evidence judge for a job application assistant.

Your task is to determine whether the candidate evidence supports a specific
job requirement.

You MUST follow these rules:

1. Use ONLY the candidate evidence provided.
2. Never invent candidate skills, experience, education, achievements, metrics,
   technologies, or qualifications.
3. Do not assume that related technologies are equivalent.
   Example: Azure AI does NOT prove Azure Data Lake experience.
4. "No evidence" means the provided evidence does not establish the requirement.
   It does NOT mean the candidate definitely lacks the skill.
5. Use "strong" when the evidence clearly and directly supports the requirement.
6. Use "partial" when the evidence supports only part of the requirement or
   provides related but incomplete evidence.
7. Use "no_evidence" when the evidence does not sufficiently support the requirement.
8. For requirements containing alternatives such as "Power BI, .NET APIs, or
   ReactJS", evidence for one valid alternative can be sufficient.
9. Select evidence only by its provided index.
10. Do not use the evidence index merely because the text looks vaguely related.
11. Return only the requested structured output.

Be conservative. Evidence is more important than making the candidate look good.
"""


class EvidenceClassifierClient(Protocol):
    def classify(
        self,
        requirement: str,
        evidence: list[dict[str, Any]],
    ) -> EvidenceClassification:
        """Classify a job requirement using retrieved candidate evidence."""


def _make_groq_strict_schema(schema: dict) -> dict:
    """Convert a Pydantic JSON schema into Groq-compatible strict schema."""
    schema = json.loads(json.dumps(schema))

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


def _response_format() -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "evidence_classification",
            "schema": _make_groq_strict_schema(
                EvidenceClassification.model_json_schema()
            ),
            "strict": True,
        },
    }


class GroqEvidenceClassifier:
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

    def classify(
        self,
        requirement: str,
        evidence: list[dict[str, Any]],
    ) -> EvidenceClassification:

        evidence_text = "\n".join(
            f"[{index}] {item.get('document', '')}"
            for index, item in enumerate(evidence)
        )

        user_prompt = f"""Job requirement:

{requirement}

Candidate evidence:

{evidence_text}

Judge whether the candidate evidence supports the requirement.

Return the indexes of only the evidence items that actually support your
classification.
"""

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": CLASSIFIER_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format=_response_format(),
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "The LLM returned no EvidenceClassification content"
            )

        return EvidenceClassification.model_validate(
            json.loads(content)
        )


def classify_requirement(
    query: str,
    retrieved: list[dict[str, Any]],
    client: EvidenceClassifierClient | None = None,
) -> dict[str, Any]:

    if not retrieved:
        return {
            "status": "no_evidence",
            "score": 0.0,
            "evidence": [],
            "reason": "No retrieved evidence.",
        }

    classifier = client or GroqEvidenceClassifier()

    result = classifier.classify(
        requirement=query,
        evidence=retrieved,
    )

    selected_evidence = []

    for index in result.evidence_indexes:
        if 0 <= index < len(retrieved):
            item = retrieved[index]

            selected_evidence.append(
                {
                    "document": item.get("document", ""),
                    "metadata": item.get("metadata", {}),
                    "similarity": item.get("similarity"),
                }
            )

    return {
        "status": result.status,
        "score": 0.0,
        "evidence": selected_evidence,
        "reason": result.explanation,
    }