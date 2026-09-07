from pydantic import BaseModel, ConfigDict, Field
from pydantic import field_validator


class Experience(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    company: str | None = None
    dates: str | None = None
    evidence: list[str] = Field(default_factory=list)


class Project(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    evidence: list[str] = Field(default_factory=list)


class Education(BaseModel):
    model_config = ConfigDict(extra="forbid")

    degree: str | None = None
    institution: str | None = None
    dates: str | None = None
    details: str | None = None


class Certification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    issuer: str | None = None
    date: str | None = None
    details: str | None = None


class CandidateProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    additional_information: list[str] = Field(default_factory=list)

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, skills: list[str]) -> list[str]:
        validated_skills = []
        for skill in skills:
            value = skill.strip()
            if not value:
                raise ValueError("skills must not contain empty values")
            if len(value.split()) > 8:
                raise ValueError("each skill must be a concise name")
            if any(mark in value for mark in [";", ":", "!", "?"]):
                raise ValueError("skills must not contain sentence-like evidence")
            validated_skills.append(value)
        return validated_skills