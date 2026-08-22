def create_chunks(
    pages: list[dict],
    chunk_size: int = 800,
    overlap: int = 100
) -> list[dict]:
    """
    Split document text into overlapping chunks.
    """

    chunks = []
    chunk_id = 1

    for page in pages:
        text = page["text"]

        start = 0

        while start < len(text):
            end = start + chunk_size

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "chunk_id": chunk_id,
                    "page": page["page"],
                    "text": chunk_text
                })

                chunk_id += 1

            start += chunk_size - overlap

    return chunks