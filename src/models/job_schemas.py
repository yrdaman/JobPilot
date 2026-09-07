from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class JobRequirement(BaseModel):
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
    evidence: str


class JobRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirements: list[JobRequirement] = Field(default_factory=list)