import json
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.document_processor import extract_document
from app.services.chunker import create_chunks
from app.services.query_pipeline import ProductQueryPipeline


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
# Paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DOCUMENT_STORE = BASE_DIR / "data" / "documents.json"


# ---------------------------------------------------------
# Request model
# ---------------------------------------------------------

class QueryRequest(BaseModel):
    question: str
    document_id: str
    top_k: int = 3


# ---------------------------------------------------------
# Persistent document storage
# ---------------------------------------------------------

def _load_documents() -> dict:

    if not DOCUMENT_STORE.exists():
        return {}

    try:
        data = json.loads(
            DOCUMENT_STORE.read_text(
                encoding="utf-8"
            )
        )

        return data if isinstance(data, dict) else {}

    except Exception:
        return {}


def _save_documents(
    documents: dict
) -> None:

    DOCUMENT_STORE.write_text(
        json.dumps(
            documents,
            indent=2
        ),
        encoding="utf-8"
    )


documents = _load_documents()


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

    return {
        "status": "healthy",
        "documents": len(documents),
    }


# ---------------------------------------------------------
# Upload
# ---------------------------------------------------------

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    allowed_extensions = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Use PDF, PNG, JPG, JPEG or WEBP."
            ),
        )

    document_id = uuid4().hex

    stored_filename = (
        f"{document_id}{extension}"
    )

    file_path = (
        UPLOAD_DIR / stored_filename
    )

    try:

        content = await file.read()

        if not content:

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        file_path.write_bytes(content)

        # -----------------------------------------
        # Process document
        # -----------------------------------------

        pages = extract_document(
            str(file_path)
        )

        text_pages = [
            page
            for page in pages
            if page.get(
                "text",
                ""
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
                False
            )
            or page.get(
                "source_type"
            ) == "image"
            for page in pages
        )

        if not chunks and not has_visual_content:

            if file_path.exists():
                file_path.unlink()

            raise HTTPException(
                status_code=422,
                detail=(
                    "No readable text or visual content "
                    "was found."
                ),
            )

        # -----------------------------------------
        # Save document metadata
        # -----------------------------------------

        documents[document_id] = {

            "document_id": document_id,

            "original_filename": file.filename,

            "stored_filename": stored_filename,

            "file_path": str(file_path),

            "pages": pages,

            "chunks": chunks,

            "visual_only": not bool(chunks),
        }

        _save_documents(
            documents
        )

        return {

            "status": "success",

            "document_id": document_id,

            "filename": file.filename,

            "pages": len(pages),

            "chunks": len(chunks),

            "visual_only": not bool(chunks),

            "file_url": (
                f"/documents/"
                f"{document_id}"
                f"/file"
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ---------------------------------------------------------
# List documents
# ---------------------------------------------------------

@app.get("/documents")
def list_documents():

    result = []

    for document in documents.values():

        file_path = Path(
            document["file_path"]
        )

        result.append({

            "document_id": document[
                "document_id"
            ],

            "filename": document[
                "original_filename"
            ],

            "pages": len(
                document.get(
                    "pages",
                    []
                )
            ),

            "chunks": len(
                document.get(
                    "chunks",
                    []
                )
            ),

            "visual_only": document.get(
                "visual_only",
                False
            ),

            "file_exists": file_path.exists(),

            "file_url": (
                f"/documents/"
                f"{document['document_id']}"
                f"/file"
            ),
        })

    return {
        "documents": result
    }


# ---------------------------------------------------------
# Serve uploaded file
# ---------------------------------------------------------

@app.get(
    "/documents/{document_id}/file"
)
def get_document_file(
    document_id: str
):

    document = documents.get(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    file_path = Path(
        document["file_path"]
    )

    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Stored file not found.",
        )

    return FileResponse(
        path=str(file_path),
        filename=document[
            "original_filename"
        ],
    )


# ---------------------------------------------------------
# Query
# ---------------------------------------------------------

@app.post("/query")
def query_product(
    request: QueryRequest
):

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    document = documents.get(
        request.document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail=(
                "Document not found. "
                "Upload it first."
            ),
        )

    # -----------------------------------------
    # Visual-only document
    # -----------------------------------------

    if document.get(
        "visual_only",
        False
    ):

        return {

            "status": "visual_evidence_only",

            "document_id": request.document_id,

            "question": question,

            "confidence": 0.0,

            "answer": None,

            "evidence": [],

            "message": (
                "The document contains visual content "
                "but no readable text was detected."
            ),
        }

    chunks = document.get(
        "chunks",
        []
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

    try:

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
                "success"
            ),

            "document_id": request.document_id,

            "question": question,

            "confidence": result.get(
                "confidence",
                0.0
            ),

            "answer": result.get(
                "answer"
            ),

            "evidence": result.get(
                "evidence",
                []
            ),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )