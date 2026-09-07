from db.chroma import create_collection
from retrieval.retriever import retrieve_evidence
from analysis.classifier import classify_requirement

queries = [
    "Exposure to Azure Data Lake",
    "Strong knowledge of Python",
    "Experience with predictive modeling",
    "Experience with AWS"
]

collection = create_collection()

for query in queries:
    results = retrieve_evidence(
        collection,
        query,
        n_results=8,
    )

    print(f"\nQuery: {query}\n")

    if not results:
        print("No results found. Did you add candidate evidence to this collection?")
        continue

    # print raw retrieval results
    for index, item in enumerate(results, start=1):
        print(f"{index}. {item['document']}")
        print(f"   metadata: {item['metadata']}")
        distance = item.get("distance")
        similarity = item.get("similarity")
        print(f"   distance: {distance:.4f}" if distance is not None else "   distance: None")
        print(f"   similarity: {similarity:.4f}" if similarity is not None else "   similarity: None")
        print()

    # classify ONCE per query (bug fix)
    final = classify_requirement(query, results)
    print("Final classification:")
    print(f"  status: {final['status']}")
    print(f"  score: {final['score']}")
    print(f"  reason: {final['reason']}")