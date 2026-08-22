from app.services.document_processor import extract_text_from_pdf
from app.services.chunker import create_chunks
from app.services.retriever import ProductRetriever


PDF_PATH = "data/uploads/test_product.pdf"


# 1. Extract text
pages = extract_text_from_pdf(PDF_PATH)

print("\n========== EXTRACTED PAGES ==========")

for page in pages:
    print(f"\nPage {page['page']}:")
    print(page["text"][:500])


# 2. Create chunks
chunks = create_chunks(pages)

print("\n========== CHUNKS ==========")
print(f"Total chunks: {len(chunks)}")


# 3. Create retriever
retriever = ProductRetriever(chunks)


# 4. Test queries
queries = [
    "maximum operating pressure",
    "motor power",
    "flow rate",
    "product applications"
]


for query in queries:

    print("\n======================================")
    print(f"QUERY: {query}")
    print("======================================")

    results = retriever.search(query, top_k=3)

    for result in results:

        print(
            f"\nSimilarity: {result['similarity']}"
            f"\nPage: {result['page']}"
            f"\nText: {result['text'][:500]}"
        )