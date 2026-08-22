from app.services.document_processor import extract_text_from_pdf
from app.services.product_pipeline import ProductIntelligencePipeline


PDF_PATH = "data/uploads/test_product.pdf"


print("\n========================================")
print("     PRODUCT INTELLIGENCE PIPELINE")
print("========================================\n")


# -----------------------------------------
# 1. Extract PDF
# -----------------------------------------

print("[1] Extracting PDF...")

pages = extract_text_from_pdf(PDF_PATH)

print(f"    Pages extracted: {len(pages)}")


# -----------------------------------------
# 2. Run intelligence pipeline
# -----------------------------------------

print("\n[2] Running extraction + validation...")

pipeline = ProductIntelligencePipeline()

result = pipeline.process_extracted_pages(pages)


# -----------------------------------------
# 3. Display final intelligence
# -----------------------------------------

print("\n========== FINAL PRODUCT INTELLIGENCE ==========\n")


for item in result["validated_attributes"]:

    print(f"Attribute   : {item['attribute']}")
    print(f"Value       : {item['value']} {item['unit']}")
    print(f"Status      : {item['status']}")
    print(f"Confidence  : {item['confidence']}")
    print(f"Evidence    : {item['evidence_count']}")
    print(f"Pages       : {item['pages']}")

    print("-" * 55)