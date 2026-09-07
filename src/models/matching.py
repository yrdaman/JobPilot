from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RequirementMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str
    category: Literal[
        "education",
        "technical_skill",
        "experience",
        "competency",
        "application",
        "other",
    ]
    importance: Literal["required", "preferred", "unspecified"]
    status: Literal[
        "strong",
        "partial",
        "no_evidence",
        "not_applicable",
    ]
    evidence: list[str] = Field(default_factory=list)
    explanation: str


class JobMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matches: list[RequirementMatch] = Field(default_factory=list)

class EvidenceClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[
        "strong",
        "partial",
        "no_evidence",
    ]

    evidence_indexes: list[int] = Field(default_factory=list)

    explanation: str