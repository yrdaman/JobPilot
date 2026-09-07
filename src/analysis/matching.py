import re
from typing import Any

from models.job_schemas import JobRequirement, JobRequirements
from models.matching import JobMatch, RequirementMatch
from models.schemas import CandidateProfile

from analysis.classifier import classify_requirement
from retrieval.retriever import retrieve_evidence


TOKEN_RE = re.compile(r"[a-z0-9+#.]+", re.IGNORECASE)
GENERIC_TOKENS = {
    "and", "or", "of", "the", "with", "for", "to", "in", "on",
    "experience", "knowledge", "understanding", "familiarity", "exposure",
    "skills", "skill", "ability", "strong", "good", "working", "using",
}

MATCHABLE_CATEGORIES = {
    "education",
    "technical_skill",
    "experience",
    "competency",
}


def _tokens(value: str) -> list[str]:
    return TOKEN_RE.findall(value.lower())


def _contains_phrase(text: str, phrase: str) -> bool:
    text_tokens = _tokens(text)
    phrase_tokens = _tokens(phrase)
    if not phrase_tokens or len(phrase_tokens) > len(text_tokens):
        return False
    width = len(phrase_tokens)
    return any(
        text_tokens[index:index + width] == phrase_tokens
        for index in range(len(text_tokens) - width + 1)
    )


def _candidate_evidence(profile: CandidateProfile) -> list[str]:
    evidence: list[str] = []
    if profile.summary:
        evidence.append(profile.summary)
    evidence.extend(profile.skills)
    for experience in profile.experience:
        evidence.extend(experience.evidence)
    for project in profile.projects:
        evidence.extend(project.evidence)
    for education in profile.education:
        evidence.extend(
            value for value in [education.degree, education.institution, education.dates, education.details] if value
        )
    for certification in profile.certifications:
        evidence.extend(
            value for value in [certification.name, certification.issuer, certification.date, certification.details] if value
        )
    evidence.extend(profile.additional_information)
    return evidence


def _match_requirement_lexical(requirement: JobRequirement, evidence: list[str]) -> RequirementMatch:
    exact = [item for item in evidence if _contains_phrase(item, requirement.requirement)]
    if exact:
        return RequirementMatch(
            requirement=requirement.requirement,
            category=requirement.category,
            importance=requirement.importance,
            status="strong",
            evidence=exact[:3],
            explanation="The candidate evidence explicitly mentions this requirement (lexical fallback).",
        )

    requirement_tokens = {
        token for token in _tokens(requirement.requirement)
        if token not in GENERIC_TOKENS and len(token) > 2
    }
    related = [item for item in evidence if requirement_tokens.intersection(_tokens(item))]
    if related:
        return RequirementMatch(
            requirement=requirement.requirement,
            category=requirement.category,
            importance=requirement.importance,
            status="partial",
            evidence=related[:3],
            explanation="Related candidate evidence found (lexical fallback).",
        )

    return RequirementMatch(
        requirement=requirement.requirement,
        category=requirement.category,
        importance=requirement.importance,
        status="no_evidence",
        evidence=[],
        explanation="No supporting candidate evidence found (lexical fallback).",
    )


def compare_requirements(
    profile: CandidateProfile,
    requirements: JobRequirements,
) -> JobMatch:
    """
    Baseline lexical matcher (kept for fallback/evaluation).
    """
    evidence = _candidate_evidence(profile)
    return JobMatch(
        matches=[
            _match_requirement_lexical(requirement, evidence)
            for requirement in requirements.requirements
        ]
    )


def _map_classifier_result(
    requirement: JobRequirement,
    result: dict[str, Any],
) -> RequirementMatch:
    status = result.get("status", "no_evidence")
    evidence_docs = []

    if result.get("status") != "no_evidence":
        evidence_docs = [
            item.get("document", "")
            for item in result.get("evidence", [])
            if item.get("document")
        ]
    explanation = result.get("reason", "No explanation provided.")

    return RequirementMatch(
        requirement=requirement.requirement,
        category=requirement.category,
        importance=requirement.importance,
        status=status,  # strong | partial | no_evidence
        evidence=evidence_docs,
        explanation=explanation,
    )

def compare_requirements_with_retrieval(
    requirements: JobRequirements,
    collection,
    n_results: int = 8,
) -> JobMatch:
    """
    Match candidate capabilities against job requirements.

    Only candidate-matchable categories are sent through
    semantic retrieval and evidence classification.

    Application and other job-information requirements are
    handled separately and are not treated as candidate skills.
    """
    matches: list[RequirementMatch] = []

    for requirement in requirements.requirements:
        

        if requirement.category not in MATCHABLE_CATEGORIES:
            

            matches.append(
                RequirementMatch(
                    requirement=requirement.requirement,
                    category=requirement.category,
                    importance=requirement.importance,
                    status="not_applicable",
                    evidence=[],
                    explanation=(
                        "This requirement is job/application information "
                        "and is not evaluated as candidate capability evidence."
                    ),
                )
            )
            continue

        retrieved = retrieve_evidence(
            collection=collection,
            query=requirement.requirement,
            n_results=n_results,
        )

        

        cls = classify_requirement(
            requirement.requirement,
            retrieved,
        )
                

        matches.append(
            _map_classifier_result(
                requirement,
                cls,
            )
        )

    return JobMatch(matches=matches)