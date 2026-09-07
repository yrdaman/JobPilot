from analysis.fit import calculate_fit
from analysis.matching import compare_requirements_with_retrieval
from analysis.job_requirements import extract_job_requirements
from copilot.service import JobPilotCopilot
from db.chroma import create_collection
from ingestion.parser import parse_resume_text
from ingestion.resume import extract_text


def main() -> None:
    # Load existing candidate profile.
    resume_text = extract_text("data/resume2.pdf")
    profile = parse_resume_text(resume_text)

    # Load job description.
    with open("data/JD.txt", "r", encoding="utf-8") as file:
        jd_text = file.read()

    requirements = extract_job_requirements(jd_text)

    # Use the existing Chroma collection.
    collection = create_collection()

    # Match requirements against candidate evidence.
    job_match = compare_requirements_with_retrieval(
        requirements,
        collection,
    )

    # Calculate existing fit.
    fit = calculate_fit(job_match)

    analysis = {
        "fit": fit,
        "matches": [
            match.model_dump()
            for match in job_match.matches
        ],
    }

    # Start the copilot.
    copilot = JobPilotCopilot()

    question = "Should I apply for this job?"

    answer = copilot.answer(
        question=question,
        analysis=analysis,
    )

    print("\n======================================================================")
    print("JOBPILOT — COPILOT TEST")
    print("======================================================================")
    print(f"\nUser: {question}\n")
    print(f"JobPilot: {answer}")


if __name__ == "__main__":
    main()