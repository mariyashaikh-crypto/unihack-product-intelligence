import os
from typing import Any

from supabase import Client, create_client


BUCKET_NAME = "documents"


class SupabaseStore:
    def __init__(self) -> None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SECRET_KEY")

        if not url:
            raise RuntimeError(
                "SUPABASE_URL environment variable is missing."
            )

        if not key:
            raise RuntimeError(
                "SUPABASE_SECRET_KEY environment variable is missing."
            )

        self.client: Client = create_client(
            url,
            key,
        )

    # ---------------------------------------------------------
    # Storage
    # ---------------------------------------------------------

    def upload_file(
        self,
        storage_path: str,
        file_bytes: bytes,
        content_type: str | None = None,
    ) -> None:

        options: dict[str, Any] = {
            "upsert": "true",
        }

        if content_type:
            options["content-type"] = content_type

        self.client.storage.from_(
            BUCKET_NAME
        ).upload(
            storage_path,
            file_bytes,
            options=options,
        )

    def download_file(
        self,
        storage_path: str,
    ) -> bytes:

        return self.client.storage.from_(
            BUCKET_NAME
        ).download(
            storage_path
        )

    def delete_file(
        self,
        storage_path: str,
    ) -> None:

        try:
            self.client.storage.from_(
                BUCKET_NAME
            ).remove(
                [storage_path]
            )
        except Exception:
            pass

    # ---------------------------------------------------------
    # Documents
    # ---------------------------------------------------------

    def create_document(
        self,
        *,
        document_id: str,
        filename: str,
        content_type: str | None,
        pages: int,
        chunks: int,
        visual_only: bool,
        storage_path: str,
    ) -> None:

        self.client.table(
            "documents"
        ).insert(
            {
                "id": document_id,
                "filename": filename,
                "content_type": content_type,
                "pages": pages,
                "chunks": chunks,
                "visual_only": visual_only,
                "storage_path": storage_path,
            }
        ).execute()

    def list_documents(self) -> list[dict]:
        response = (
            self.client
            .table("documents")
            .select("*")
            .order(
                "created_at",
                desc=True,
            )
            .execute()
        )

        return response.data or []

    def get_document(
        self,
        document_id: str,
    ) -> dict | None:

        response = (
            self.client
            .table("documents")
            .select("*")
            .eq("id", document_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]

    # ---------------------------------------------------------
    # Chunks
    # ---------------------------------------------------------

    def create_chunks(
        self,
        document_id: str,
        chunks: list[dict],
    ) -> None:

        if not chunks:
            return

        rows = []

        for index, chunk in enumerate(chunks):

            rows.append(
                {
                    "document_id": document_id,
                    "page": chunk.get("page"),
                    "chunk_index": index,
                    "text": chunk.get(
                        "text",
                        "",
                    ),
                }
            )

        (
            self.client
            .table("document_chunks")
            .insert(rows)
            .execute()
        )

    def get_chunks(
        self,
        document_id: str,
    ) -> list[dict]:

        response = (
            self.client
            .table("document_chunks")
            .select(
                "page, chunk_index, text"
            )
            .eq(
                "document_id",
                document_id,
            )
            .order(
                "chunk_index"
            )
            .execute()
        )

        return response.data or []

    # ---------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------

    def delete_document(
        self,
        document_id: str,
    ) -> None:

        document = self.get_document(
            document_id
        )

        if document:
            storage_path = document.get(
                "storage_path"
            )

            if storage_path:
                self.delete_file(
                    storage_path
                )

        (
            self.client
            .table("documents")
            .delete()
            .eq("id", document_id)
            .execute()
        )