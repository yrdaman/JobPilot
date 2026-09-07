from db.chroma import create_collection, add_candidate_evidence
from models.schemas import CandidateProfile


profile = CandidateProfile(
    skills=["Python", "SQL", "PostgreSQL"],
    projects=[
        {
            "name": "CVD Predictive Web Application",
            "evidence": [
                "Engineered end-to-end Python ML pipeline on 70,000+ records.",
                "Developed clean, modular Flask REST API backend.",
            ],
        }
    ],
)

collection = create_collection()

count = add_candidate_evidence(collection, profile)

print(f"Added {count} documents")

print("\nStored documents:")

result = collection.get()

for document, metadata in zip(
    result["documents"],
    result["metadatas"],
):
    print(f"- {document}")
    print(f"  metadata: {metadata}")