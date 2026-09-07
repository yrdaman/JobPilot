import argparse
from pathlib import Path

from ingestion.parser import parse_resume_text
from ingestion.resume import extract_text
from db.chroma import create_collection, add_candidate_evidence


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description="Parse a resume PDF into CandidateProfile JSON."
    )
    argument_parser.add_argument("pdf_path", type=Path)
    arguments = argument_parser.parse_args()

    resume_text = extract_text(arguments.pdf_path)
    profile = parse_resume_text(resume_text)

    collection = create_collection()
    count = add_candidate_evidence(collection, profile)

    print(f"Stored {count} candidate evidence documents in ChromaDB.")
    print(profile.model_dump_json(indent=2))


if __name__ == "__main__":
    main()