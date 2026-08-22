from app.services.document_processor import extract_text_from_pdf
from app.services.extractor import ProductExtractor


PDF_PATH = "data/uploads/test_product.pdf"


# -----------------------------------------
# Extract PDF
# -----------------------------------------

pages = extract_text_from_pdf(PDF_PATH)


extractor = ProductExtractor()


all_results = []


# -----------------------------------------
# Extract attributes page by page
# -----------------------------------------

for page in pages:

    page_number = page["page"]
    text = page["text"]

    results = extractor.extract_numeric_attributes(text)

    for result in results:

        result["page"] = page_number

        all_results.append(result)


# -----------------------------------------
# Display results
# -----------------------------------------

print("\n========== PDF ATTRIBUTE EXTRACTION ==========\n")

if not all_results:

    print("No attributes extracted.")

else:

    for result in all_results:

        print(
            f"{result['attribute']}: "
            f"{result['value']} {result['unit']} "
            f"| Page {result['page']} "
            f"| Evidence: {result['evidence']}"
        )