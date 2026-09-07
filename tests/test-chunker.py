from ingestion.resume import extract_text
from ingestion.chunker import chunk_resume_hybrid, token_count
from pathlib import Path




def main():
    pdf_path = Path("data/resume.pdf")
    text = extract_text(pdf_path)

    chunks = chunk_resume_hybrid(text, max_tokens=350, overlap_tokens=40)

    print(f"Total chunks: {len(chunks)}\n")
    for c in chunks:
        preview = c.text[:140].replace("\n", " ")
        print(
            f"[{c.metadata['chunk_id']}] "
            f"section={c.metadata['section']} "
            f"strategy={c.metadata['strategy']} "
            f"tokens={token_count(c.text)}"
        )
        print(f"  {preview}...\n")


if __name__ == "__main__":
    main()