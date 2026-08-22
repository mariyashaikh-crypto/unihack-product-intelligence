from app.services.document_processor import extract_text_from_pdf
from app.services.chunker import create_chunks
from app.services.query_pipeline import ProductQueryPipeline


PDF_PATH = "data/uploads/test_product.pdf"


print("=" * 60)
print("PRODUCT QUERY PIPELINE TEST")
print("=" * 60)


# ---------------------------------------------------------
# 1. Extract PDF
# ---------------------------------------------------------

pages = extract_text_from_pdf(PDF_PATH)

print(f"\nPages extracted: {len(pages)}")


# ---------------------------------------------------------
# 2. Create chunks
# ---------------------------------------------------------

chunks = create_chunks(pages)

print(f"Chunks created: {len(chunks)}")


# ---------------------------------------------------------
# 3. Create query pipeline
# ---------------------------------------------------------

pipeline = ProductQueryPipeline(chunks)


# ---------------------------------------------------------
# 4. Test questions
# ---------------------------------------------------------

questions = [
    "maximum operating pressure",
    "motor power",
    "flow rate",
    "product applications"
]


for question in questions:

    print("\n" + "=" * 60)
    print(f"QUESTION: {question}")
    print("=" * 60)

    result = pipeline.query(question)

    print("\nSTATUS:")
    print(result.get("status"))

    print("\nCONFIDENCE:")
    print(result.get("confidence"))

    print("\nANSWER:")

    answer = result.get("answer")

    # ---------------------------------------------
    # Numeric answer
    # ---------------------------------------------

    if isinstance(answer, list):

        if not answer:

            print("No attribute found.")

        for item in answer:

            print(
                f"{item.get('attribute')}: "
                f"{item.get('value')} "
                f"{item.get('unit')}"
            )

            print(
                f"Status: "
                f"{item.get('status')}"
            )

            print(
                f"Pages: "
                f"{item.get('pages')}"
            )

            print(
                f"Evidence count: "
                f"{item.get('evidence_count')}"
            )

    # ---------------------------------------------
    # Text answer
    # ---------------------------------------------

    elif isinstance(answer, str):

        print(answer)

    # ---------------------------------------------
    # No answer
    # ---------------------------------------------

    elif answer is None:

        print("No answer found.")

    else:

        print(answer)

    # ---------------------------------------------
    # Retrieved evidence
    # ---------------------------------------------

    evidence = result.get(
        "retrieved_chunks",
        result.get("evidence", [])
    )

    if evidence:

        print("\nRETRIEVED EVIDENCE:")

        for chunk in evidence[:3]:

            print("\nPage:", chunk.get("page"))

            print(
                "Similarity:",
                chunk.get("similarity")
            )

            print(chunk.get("text"))