from pathlib import Path
import chromadb
from models.schemas import CandidateProfile


def create_collection(db_path: str = "data/chroma", name: str = "candidate_evidence"):
    Path(db_path).mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name=name)
    return collection


def add_candidate_evidence(collection, profile: CandidateProfile, candidate_id: str = "candidate_1") -> int:
    documents: list[str] = []
    ids: list[str] = []
    metadatas: list[dict] = []

    def add(doc: str, doc_id: str, meta: dict):
        if doc and doc.strip():
            documents.append(doc.strip())
            ids.append(f"{candidate_id}:{doc_id}")
            metadatas.append(meta)

    # summary
    add(profile.summary or "", "summary:0", {"type": "summary"})

    # skills
    for i, skill in enumerate(profile.skills):
        add(skill, f"skill:{i}", {"type": "skill"})

    # experience
    for i, exp in enumerate(profile.experience):
        for j, ev in enumerate(exp.evidence):
            add(
                ev,
                f"experience:{i}:{j}",
                {
                    "type": "experience",
                    "title": exp.title or "",
                    "company": exp.company or "",
                },
            )

    # projects
    for i, proj in enumerate(profile.projects):
        for j, ev in enumerate(proj.evidence):
            add(
                ev,
                f"project:{i}:{j}",
                {
                    "type": "project",
                    "name": proj.name or "",
                },
            )

    # education
    for i, edu in enumerate(profile.education):
        add(edu.degree or "", f"education:{i}:degree", {"type": "education"})
        add(edu.institution or "", f"education:{i}:institution", {"type": "education"})
        add(edu.details or "", f"education:{i}:details", {"type": "education"})

    # certifications
    for i, cert in enumerate(profile.certifications):
        add(cert.name or "", f"cert:{i}:name", {"type": "certification"})
        add(cert.details or "", f"cert:{i}:details", {"type": "certification"})

    if not documents:
        return 0

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(documents)