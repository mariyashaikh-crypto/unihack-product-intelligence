import mimetypes
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.chunker import create_chunks
from app.services.document_processor import (
    extract_document,
)
from app.services.query_pipeline import (
    ProductQueryPipeline,
)
from app.services.supabase_store import (
    SupabaseStore,
)


app = FastAPI(
    title="Product Intelligence API",
    description="Product intelligence backend",
    version="1.0.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://unihack-product-intelligence.web.app",
        "https://unihack-product-intelligence.firebaseapp.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Request model
# ---------------------------------------------------------

class QueryRequest(BaseModel):
    question: str
    document_id: str
    top_k: int = 3


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


def get_store() -> SupabaseStore:
    return SupabaseStore()


def get_content_type(
    filename: str,
) -> str:

    content_type, _ = (
        mimetypes.guess_type(filename)
    )

    return (
        content_type
        or "application/octet-stream"
    )


# ---------------------------------------------------------
# Root
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "success",
        "message": "Product Intelligence API is running",
    }


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/health")
def health():
    # We intentionally check that the Supabase connection
    # can be initialized. This catches missing environment
    # variables on Render.
    try:
        get_store()

        return {
            "status": "healthy",
            "storage": "supabase",
        }

    except Exception as exc:

        raise HTTPException(
            status_code=503,
            detail=(
                "Supabase storage is not configured: "
                f"{exc}"
            ),
        )


# ---------------------------------------------------------
# Upload
# ---------------------------------------------------------

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    original_filename = Path(
        file.filename
    ).name

    extension = Path(
        original_filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Use PDF, PNG, JPG, JPEG or WEBP."
            ),
        )

    document_id = str(
        uuid4()
    )

    storage_path = (
        f"{document_id}/"
        f"{original_filename}"
    )

    content_type = (
        file.content_type
        or get_content_type(
            original_filename
        )
    )

    store = get_store()

    temp_path: Path | None = None

    try:
        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        # -------------------------------------------------
        # Temporary local file for OCR/document processing
        # -------------------------------------------------

        with tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temp_file:

            temp_file.write(content)
            temp_path = Path(
                temp_file.name
            )

        # -------------------------------------------------
        # Extract text / OCR
        # -------------------------------------------------

        pages = extract_document(
            str(temp_path)
        )

        text_pages = [
            page
            for page in pages
            if page.get(
                "text",
                "",
            ).strip()
        ]

        chunks = []

        if text_pages:
            chunks = create_chunks(
                text_pages
            )

        has_visual_content = any(
            page.get(
                "has_images",
                False,
            )
            or page.get(
                "source_type"
            ) == "image"
            for page in pages
        )

        if (
            not chunks
            and not has_visual_content
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "No readable text or visual "
                    "content was found."
                ),
            )

        # -------------------------------------------------
        # Persistent Supabase storage
        # -------------------------------------------------

        store.upload_file(
            storage_path=storage_path,
            file_bytes=content,
            content_type=content_type,
        )

        store.create_document(
            document_id=document_id,
            filename=original_filename,
            content_type=content_type,
            pages=len(pages),
            chunks=len(chunks),
            visual_only=not bool(chunks),
            storage_path=storage_path,
        )

        store.create_chunks(
            document_id=document_id,
            chunks=chunks,
        )

        return {
            "status": "success",
            "document_id": document_id,
            "filename": original_filename,
            "pages": len(pages),
            "chunks": len(chunks),
            "visual_only": not bool(chunks),
            "file_url": (
                f"/documents/"
                f"{document_id}/file"
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:

        # If the database/storage write failed after
        # uploading the file, remove the uploaded file.
        try:
            store.delete_file(
                storage_path
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    finally:

        if temp_path is not None:

            try:
                temp_path.unlink(
                    missing_ok=True
                )
            except Exception:
                pass


# ---------------------------------------------------------
# List documents
# ---------------------------------------------------------

@app.get("/documents")
def list_documents():

    try:
        store = get_store()

        documents = (
            store.list_documents()
        )

        result = []

        for document in documents:

            document_id = document.get(
                "id"
            )

            result.append(
                {
                    "document_id": document_id,

                    "filename": document.get(
                        "filename"
                    ),

                    "content_type": document.get(
                        "content_type"
                    ),

                    "pages": document.get(
                        "pages",
                        0,
                    ),

                    "chunks": document.get(
                        "chunks",
                        0,
                    ),

                    "visual_only": document.get(
                        "visual_only",
                        False,
                    ),

                    "file_url": (
                        f"/documents/"
                        f"{document_id}/file"
                    ),

                    "created_at": document.get(
                        "created_at"
                    ),
                }
            )

        return {
            "documents": result
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ---------------------------------------------------------
# Download stored document
# ---------------------------------------------------------

@app.get(
    "/documents/{document_id}/file"
)
def get_document_file(
    document_id: str,
):

    try:

        store = get_store()

        document = (
            store.get_document(
                document_id
            )
        )

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        storage_path = document.get(
            "storage_path"
        )

        if not storage_path:
            raise HTTPException(
                status_code=404,
                detail="Document storage path not found.",
            )

        file_bytes = (
            store.download_file(
                storage_path
            )
        )

        return Response(
            content=file_bytes,
            media_type=(
                document.get(
                    "content_type"
                )
                or "application/octet-stream"
            ),
            headers={
                "Content-Disposition": (
                    "inline; filename="
                    f'"{document.get("filename", "document")}"'
                )
            },
        )

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ---------------------------------------------------------
# Query
# ---------------------------------------------------------

@app.post("/query")
def query_product(
    request: QueryRequest,
):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:

        store = get_store()

        document = (
            store.get_document(
                request.document_id
            )
        )

        if not document:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Document not found. "
                    "Upload it first."
                ),
            )

        if document.get(
            "visual_only",
            False,
        ):

            return {
                "status": "visual_evidence_only",
                "document_id": request.document_id,
                "question": question,
                "confidence": 0.0,
                "answer": None,
                "evidence": [],
                "message": (
                    "The document contains visual "
                    "content but no readable text "
                    "was detected."
                ),
            }

        chunks = (
            store.get_chunks(
                request.document_id
            )
        )

        if not chunks:

            return {
                "status": "no_evidence",
                "document_id": request.document_id,
                "question": question,
                "confidence": 0.0,
                "answer": None,
                "evidence": [],
            }

        pipeline = ProductQueryPipeline(
            chunks=chunks
        )

        result = pipeline.query(
            question=question,
            top_k=request.top_k,
        )

        return {
            "status": result.get(
                "status",
                "success",
            ),
            "document_id": request.document_id,
            "question": question,
            "confidence": result.get(
                "confidence",
                0.0,
            ),
            "answer": result.get(
                "answer"
            ),
            "evidence": result.get(
                "evidence",
                [],
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )