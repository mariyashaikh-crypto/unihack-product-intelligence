import io
import re
from pathlib import Path

import pymupdf
from PIL import Image, ImageOps, ImageFilter
from rapidocr_onnxruntime import RapidOCR


OCR = RapidOCR()

SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


def _clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    replacements = {
        "Γö¼Γûæ": "°",
        "├é┬░": "°",
        "├óΓé¼ΓÇ£": "–",
        "├óΓé¼ΓÇ¥": "—",
        "├óΓé¼Γäó": "'",
        "├óΓé¼┼ô": '"',
        "├óΓé¼┬¥": '"',
        "├é": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _deduplicate_lines(text: str) -> str:
    if not text:
        return ""

    seen = set()
    output = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        key = re.sub(
            r"\s+",
            " ",
            line.lower()
        )

        if key in seen:
            continue

        seen.add(key)
        output.append(line)

    return "\n".join(output)


def _prepare_images(image: Image.Image) -> list[Image.Image]:
    """
    Create several OCR-friendly versions of an image.

    This helps with:
    - screenshots
    - posters
    - phone photos
    - low contrast text
    - small text
    """

    image = image.convert("RGB")

    # Upscale smaller images.
    width, height = image.size

    if width < 1600:
        scale = 1600 / max(width, 1)

        image = image.resize(
            (
                int(width * scale),
                int(height * scale),
            ),
            Image.Resampling.LANCZOS,
        )

    variants = []

    # Original
    variants.append(image)

    # Grayscale + contrast
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)

    variants.append(gray)

    # Sharpened
    sharpened = gray.filter(
        ImageFilter.SHARPEN
    )

    variants.append(sharpened)

    # Thresholded
    threshold = gray.point(
        lambda p: 255 if p > 170 else 0
    )

    variants.append(threshold)

    return variants


def _ocr_once(image: Image.Image) -> list[str]:

    try:

        result, _ = OCR(image)

        if not result:
            return []

        lines = []

        for item in result:

            if len(item) < 2:
                continue

            detected_text = item[1]

            if detected_text:
                lines.append(
                    str(detected_text)
                )

        return lines

    except Exception:
        return []


def _ocr_image(
    image: Image.Image
) -> str:
    """
    Run multiple OCR passes and merge their text.
    """

    all_lines = []

    for variant in _prepare_images(image):

        all_lines.extend(
            _ocr_once(variant)
        )

    text = "\n".join(all_lines)

    return _deduplicate_lines(
        _clean_text(text)
    )


def _ocr_pdf_page(page) -> str:
    """
    Render a PDF page at high resolution and OCR it.
    """

    try:

        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(
                2.5,
                2.5,
            ),
            alpha=False,
        )

        image = Image.frombytes(
            "RGB",
            (
                pixmap.width,
                pixmap.height,
            ),
            pixmap.samples,
        )

        return _ocr_image(image)

    except Exception:
        return ""


def _extract_embedded_image_ocr(
    document,
    page
) -> list[dict]:

    results = []

    try:

        image_list = page.get_images(
            full=True
        )

        for image_index, info in enumerate(
            image_list,
            start=1
        ):

            xref = info[0]

            try:

                extracted = document.extract_image(
                    xref
                )

                raw = extracted["image"]

                image = Image.open(
                    io.BytesIO(raw)
                ).convert("RGB")

                ocr_text = _ocr_image(
                    image
                )

                results.append({

                    "image_index": image_index,

                    "width": image.width,

                    "height": image.height,

                    "extension": extracted.get(
                        "ext",
                        "png"
                    ),

                    "ocr_text": ocr_text,

                    "has_text": bool(
                        ocr_text
                    ),
                })

            except Exception:

                results.append({

                    "image_index": image_index,

                    "width": None,

                    "height": None,

                    "extension": "unknown",

                    "ocr_text": "",

                    "has_text": False,
                })

    except Exception:
        pass

    return results


def _extract_pdf(
    file_path: str
) -> list[dict]:

    path = Path(file_path)

    document = pymupdf.open(
        str(path)
    )

    pages = []

    try:

        if document.page_count == 0:
            raise ValueError(
                "The PDF contains no pages."
            )

        for page_number, page in enumerate(
            document,
            start=1
        ):

            native_text = _clean_text(
                page.get_text("text")
            )

            embedded_images = (
                _extract_embedded_image_ocr(
                    document,
                    page
                )
            )

            image_text = "\n".join(
                image["ocr_text"]
                for image in embedded_images
                if image.get("ocr_text")
            )

            # OCR the whole page when:
            # - native text is sparse
            # - the page contains images
            # - it may be a scanned page
            should_ocr_page = (
                len(native_text) < 80
                or bool(embedded_images)
            )

            page_ocr_text = ""

            if should_ocr_page:

                page_ocr_text = _ocr_pdf_page(
                    page
                )

            # Prefer native PDF text when it is substantial,
            # but add OCR content for image/scanned material.
            combined_parts = []

            if native_text:
                combined_parts.append(
                    native_text
                )

            if page_ocr_text:
                combined_parts.append(
                    page_ocr_text
                )

            if image_text:
                combined_parts.append(
                    image_text
                )

            combined_text = "\n".join(
                combined_parts
            )

            combined_text = _deduplicate_lines(
                _clean_text(combined_text)
            )

            pages.append({

                "page": page_number,

                "text": combined_text,

                "has_text": bool(
                    combined_text
                ),

                "native_text": native_text,

                "ocr_text": page_ocr_text,

                "embedded_image_text": image_text,

                "has_images": bool(
                    embedded_images
                ),

                "image_count": len(
                    embedded_images
                ),

                "images": embedded_images,

                "ocr_used": bool(
                    page_ocr_text
                    or image_text
                ),

                "source_type": "pdf",

                "source": path.name,
            })

        return pages

    finally:
        document.close()


def _extract_image(
    file_path: str
) -> list[dict]:

    path = Path(file_path)

    try:

        image = Image.open(
            str(path)
        ).convert("RGB")

    except Exception as exc:

        raise ValueError(
            f"Unable to read image: {file_path}"
        ) from exc

    ocr_text = _ocr_image(
        image
    )

    return [{

        "page": 1,

        "text": ocr_text,

        "has_text": bool(
            ocr_text
        ),

        "native_text": "",

        "ocr_text": ocr_text,

        "embedded_image_text": "",

        "has_images": True,

        "image_count": 1,

        "images": [{

            "image_index": 1,

            "width": image.width,

            "height": image.height,

            "extension": path.suffix.lower().lstrip("."),

            "ocr_text": ocr_text,

            "has_text": bool(
                ocr_text
            ),
        }],

        "ocr_used": True,

        "source_type": "image",

        "source": path.name,

        "image_width": image.width,

        "image_height": image.height,
    }]


def extract_document(
    file_path: str
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
        "Supported: PDF, PNG, JPG, JPEG, WEBP."
    )


def extract_text_from_pdf(
    file_path: str
) -> list[dict]:

    return _extract_pdf(
        str(file_path)
    )


def get_text_pages(
    pages: list[dict]
) -> list[dict]:

    return [
        page
        for page in pages
        if page.get(
            "text",
            ""
        ).strip()
    ]


def get_extraction_summary(
    pages: list[dict]
) -> dict:

    total_pages = len(
        pages
    )

    text_pages = sum(
        1
        for page in pages
        if page.get("has_text")
    )

    ocr_pages = sum(
        1
        for page in pages
        if page.get("ocr_used")
    )

    image_pages = sum(
        1
        for page in pages
        if page.get("has_images")
    )

    total_images = sum(
        page.get(
            "image_count",
            0
        )
        for page in pages
    )

    return {

        "total_pages": total_pages,

        "text_pages": text_pages,

        "ocr_pages": ocr_pages,

        "image_pages": image_pages,

        "total_images": total_images,

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