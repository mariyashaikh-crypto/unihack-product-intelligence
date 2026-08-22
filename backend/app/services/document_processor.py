import io
import os
import re
from pathlib import Path
from typing import Optional

# Keep native libraries from creating too many worker threads.
# This helps reduce memory usage on small deployment instances.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import pymupdf
from PIL import Image, ImageOps, ImageFilter
from rapidocr_onnxruntime import RapidOCR


SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

# Lazy-load OCR so the server does not allocate the OCR model
# just to answer /health or /documents.
_OCR_ENGINE: Optional[RapidOCR] = None


def _get_ocr() -> RapidOCR:
    global _OCR_ENGINE

    if _OCR_ENGINE is None:
        _OCR_ENGINE = RapidOCR()

    return _OCR_ENGINE


def _clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    replacements = {
        "\x00": "",
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
            line.lower(),
        )

        if key in seen:
            continue

        seen.add(key)
        output.append(line)

    return "\n".join(output)


def _resize_for_ocr(
    image: Image.Image,
    max_width: int = 1800,
    max_height: int = 1800,
) -> Image.Image:
    """
    Resize only when the image is excessively large.

    Very large camera images can consume hundreds of MB when
    copied/decoded multiple times.
    """

    image = image.convert("RGB")

    width, height = image.size

    scale = min(
        1.0,
        max_width / max(width, 1),
        max_height / max(height, 1),
    )

    if scale >= 1.0:
        return image

    return image.resize(
        (
            max(1, int(width * scale)),
            max(1, int(height * scale)),
        ),
        Image.Resampling.LANCZOS,
    )


def _prepare_ocr_variants(
    image: Image.Image,
) -> list[Image.Image]:
    """
    Create only two lightweight OCR variants:
    original + enhanced grayscale.

    Earlier versions created four copies, which increased
    memory pressure considerably on small cloud instances.
    """

    image = _resize_for_ocr(image)

    variants = [image]

    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)

    # Keep sharpening lightweight.
    gray = gray.filter(
        ImageFilter.SHARPEN
    )

    variants.append(gray)

    return variants


def _ocr_once(
    image: Image.Image,
) -> list[str]:
    """
    Perform one OCR pass.
    """

    try:
        engine = _get_ocr()

        result, _ = engine(image)

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
    image: Image.Image,
) -> str:
    """
    Memory-conscious OCR.

    OCR variants are processed sequentially rather than
    keeping a large collection of copies in memory.
    """

    source = _resize_for_ocr(image)

    all_lines = []

    try:
        variants = _prepare_ocr_variants(
            source
        )

        for variant in variants:
            all_lines.extend(
                _ocr_once(variant)
            )

        text = "\n".join(all_lines)

        return _deduplicate_lines(
            _clean_text(text)
        )

    finally:
        try:
            source.close()
        except Exception:
            pass

        for variant in locals().get(
            "variants",
            [],
        ):
            try:
                variant.close()
            except Exception:
                pass


def _render_pdf_page(
    page,
) -> Optional[Image.Image]:
    """
    Render a PDF page at a moderate resolution.

    1.8x keeps OCR useful while using much less RAM than
    2.5x rendering.
    """

    try:
        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(
                1.8,
                1.8,
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

        # Release PyMuPDF pixel buffer as soon as possible.
        del pixmap

        return image

    except Exception:
        return None


def _ocr_pdf_page(
    page,
) -> str:
    """
    Render + OCR a page without retaining the render.
    """

    image = _render_pdf_page(page)

    if image is None:
        return ""

    try:
        return _ocr_image(image)

    finally:
        try:
            image.close()
        except Exception:
            pass


def _extract_embedded_image_ocr(
    document,
    page,
) -> list[dict]:
    """
    OCR embedded images only when they exist.

    Each image is processed and released immediately.
    """

    results = []

    try:
        image_list = page.get_images(
            full=True
        )
    except Exception:
        return results

    for image_index, info in enumerate(
        image_list,
        start=1,
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

            try:
                ocr_text = _ocr_image(
                    image
                )
            finally:
                image.close()

            results.append(
                {
                    "image_index": image_index,
                    "width": extracted.get(
                        "width"
                    ),
                    "height": extracted.get(
                        "height"
                    ),
                    "extension": extracted.get(
                        "ext",
                        "png",
                    ),
                    "ocr_text": ocr_text,
                    "has_text": bool(
                        ocr_text
                    ),
                }
            )

        except Exception:
            results.append(
                {
                    "image_index": image_index,
                    "width": None,
                    "height": None,
                    "extension": "unknown",
                    "ocr_text": "",
                    "has_text": False,
                }
            )

        # Make sure the raw bytes don't stay referenced.
        raw = None
        extracted = None

    return results


def _extract_pdf(
    file_path: str,
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
            start=1,
        ):
            native_text = _clean_text(
                page.get_text("text")
            )

            embedded_images = (
                _extract_embedded_image_ocr(
                    document,
                    page,
                )
            )

            image_text = "\n".join(
                image["ocr_text"]
                for image in embedded_images
                if image.get("ocr_text")
            )

            # OCR the entire page when native text is sparse
            # and the embedded-image OCR did not already give
            # us useful text.
            should_ocr_page = (
                len(native_text) < 80
                and not image_text
            )

            page_ocr_text = ""

            if should_ocr_page:
                page_ocr_text = _ocr_pdf_page(
                    page
                )

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

            combined_text = _deduplicate_lines(
                _clean_text(
                    "\n".join(
                        combined_parts
                    )
                )
            )

            pages.append(
                {
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
                }
            )

            # Release page-local OCR structures before moving on.
            del embedded_images
            del image_text
            del page_ocr_text

        return pages

    finally:
        document.close()


def _extract_image(
    file_path: str,
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

    try:
        width, height = image.size

        ocr_text = _ocr_image(
            image
        )

    finally:
        image.close()

    return [
        {
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
            "images": [
                {
                    "image_index": 1,
                    "width": width,
                    "height": height,
                    "extension": (
                        path.suffix
                        .lower()
                        .lstrip(".")
                    ),
                    "ocr_text": ocr_text,
                    "has_text": bool(
                        ocr_text
                    ),
                }
            ],
            "ocr_used": True,
            "source_type": "image",
            "source": path.name,
            "image_width": width,
            "image_height": height,
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
        "Supported: PDF, PNG, JPG, JPEG, WEBP."
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
            ""
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
            0,
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