import gc
import re
from pathlib import Path


SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


def _clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace(
        "\r\n",
        "\n",
    )

    text = text.replace(
        "\r",
        "\n",
    )

    text = text.replace(
        "\x00",
        "",
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def _extract_pdf(
    file_path: str,
) -> list[dict]:
    """
    Lightweight native PDF extraction only.

    OCR is intentionally NOT performed here.
    Scanned/image PDFs are OCRed in the browser.
    """

    import pymupdf

    path = Path(file_path)

    document = pymupdf.open(
        str(path)
    )

    pages = []

    try:
        for page_number in range(
            document.page_count
        ):
            page = document.load_page(
                page_number
            )

            try:
                text = _clean_text(
                    page.get_text("text")
                )

                pages.append(
                    {
                        "page": page_number + 1,
                        "text": text,
                        "has_text": bool(text),
                        "native_text": text,
                        "ocr_text": "",
                        "has_images": False,
                        "image_count": 0,
                        "images": [],
                        "ocr_used": False,
                        "source_type": "pdf",
                        "source": path.name,
                    }
                )

            finally:
                del page
                gc.collect()

        return pages

    finally:
        document.close()
        gc.collect()


def _extract_image(
    file_path: str,
) -> list[dict]:
    """
    Images are OCRed in the browser.

    The backend only creates a lightweight page record
    if called as a fallback.
    """

    path = Path(file_path)

    return [
        {
            "page": 1,
            "text": "",
            "has_text": False,
            "native_text": "",
            "ocr_text": "",
            "has_images": True,
            "image_count": 1,
            "images": [],
            "ocr_used": False,
            "source_type": "image",
            "source": path.name,
        }
    ]


def extract_document(
    file_path: str,
) -> list[dict]:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Path is not a file: {file_path}"
        )

    extension = path.suffix.lower()

    if extension == ".pdf":
        return _extract_pdf(
            str(path)
        )

    if extension in SUPPORTED_IMAGE_EXTENSIONS:
        return _extract_image(
            str(path)
        )

    raise ValueError(
        "Unsupported document type. "
        "Supported: PDF, PNG, JPG, JPEG or WEBP."
    )


def extract_text_from_pdf(
    file_path: str,
) -> list[dict]:

    return _extract_pdf(
        str(file_path)
    )


def get_text_pages(
    pages: list[dict],
) -> list[dict]:

    return [
        page
        for page in pages
        if page.get(
            "text",
            "",
        ).strip()
    ]


def get_extraction_summary(
    pages: list[dict],
) -> dict:

    total_pages = len(pages)

    text_pages = sum(
        1
        for page in pages
        if page.get("has_text")
    )

    return {
        "total_pages": total_pages,
        "text_pages": text_pages,
        "ocr_pages": 0,
        "image_pages": sum(
            1
            for page in pages
            if page.get("has_images")
        ),
        "empty_pages": (
            total_pages - text_pages
        ),
        "text_extraction_success": (
            text_pages > 0
        ),
        "likely_scanned": (
            total_pages > 0
            and text_pages == 0
        ),
    }