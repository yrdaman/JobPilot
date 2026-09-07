def retrieve_evidence(
    collection,
    query: str,
    n_results: int = 5,
) -> list[dict]:
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    docs_batch = results.get("documents", [])
    meta_batch = results.get("metadatas", [])
    dist_batch = results.get("distances", [])

    if not docs_batch or not docs_batch[0]:
        return []

    documents = docs_batch[0]
    metadatas = meta_batch[0] if meta_batch else [{} for _ in documents]
    distances = dist_batch[0] if dist_batch else [None for _ in documents]

    output = []
    for document, metadata, distance in zip(documents, metadatas, distances):
        similarity = None if distance is None else 1 / (1 + distance)
        output.append(
            {
                "document": document,
                "metadata": metadata or {},
                "distance": distance,
                "similarity": similarity,
            }
        )

    return output