from models.matching import JobMatch


def calculate_fit(job_match: JobMatch) -> dict:
    """Calculate a deterministic summary of candidate-job fit."""

    applicable = [
        match
        for match in job_match.matches
        if match.status != "not_applicable"
    ]

    if not applicable:
        return {
            "fit_score": 0,
            "strong_matches": 0,
            "partial_matches": 0,
            "no_evidence": 0,
            "total_requirements": 0,
        }

    points = 0
    maximum = 0

    for match in applicable:
        # Required requirements matter more than preferred ones.
        weight = 2 if match.importance == "required" else 1

        maximum += weight

        if match.status == "strong":
            points += weight
        elif match.status == "partial":
            points += weight * 0.5

    fit_score = round((points / maximum) * 100)

    return {
        "fit_score": fit_score,
        "strong_matches": sum(
            match.status == "strong"
            for match in applicable
        ),
        "partial_matches": sum(
            match.status == "partial"
            for match in applicable
        ),
        "no_evidence": sum(
            match.status == "no_evidence"
            for match in applicable
        ),
        "total_requirements": len(applicable),
    }