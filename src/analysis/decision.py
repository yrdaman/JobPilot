from models.matching import JobMatch


def should_apply(job_match: JobMatch, fit: dict) -> dict:
    """Generate a deterministic application recommendation."""

    required_matches = [
        match
        for match in job_match.matches
        if match.importance == "required"
    ]

    required_missing = [
        match
        for match in required_matches
        if match.status == "no_evidence"
    ]

    required_partial = [
        match
        for match in required_matches
        if match.status == "partial"
    ]

    fit_score = fit["fit_score"]

    if fit_score >= 70 and len(required_missing) <= 1:
        recommendation = "apply"
    elif fit_score >= 50 and len(required_missing) <= 2:
        recommendation = "consider"
    else:
        recommendation = "low_fit"

    return {
        "recommendation": recommendation,
        "fit_score": fit_score,
        "required_missing": [
            match.requirement
            for match in required_missing
        ],
        "required_partial": [
            match.requirement
            for match in required_partial
        ],
    }