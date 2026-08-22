# Product Intelligence

### An Evidence-First Document Intelligence Platform

Upload **PDFs, scanned documents, posters, screenshots, brochures, and images** and turn them into searchable, queryable knowledge using OCR, retrieval, and evidence-grounded question answering.

**Upload. Extract. Search. Ask. Verify.**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge\&logo=fastapi\&logoColor=white)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge\&logo=react\&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-Build%20Tool-646CFF?style=for-the-badge\&logo=vite\&logoColor=white)
![RapidOCR](https://img.shields.io/badge/RapidOCR-OCR-FF6F00?style=for-the-badge)
![PyMuPDF](https://img.shields.io/badge/PyMuPDF-PDF%20Processing-8A2BE2?style=for-the-badge)
![scikit--learn](https://img.shields.io/badge/scikit--learn-Retrieval-F7931E?style=for-the-badge\&logo=scikit-learn\&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Database%20%26%20Storage-3ECF8E?style=for-the-badge\&logo=supabase\&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-Hosting-FFCA28?style=for-the-badge\&logo=firebase\&logoColor=black)
![Render](https://img.shields.io/badge/Render-Backend%20Hosting-46E3B7?style=for-the-badge\&logo=render\&logoColor=black)

---


Built for **UniHack** — a full-stack document intelligence platform focused on extracting trustworthy, evidence-backed answers from real-world documents.

---

## What is Product Intelligence?

Product Intelligence is a lightweight, evidence-first **document question-answering platform**.

Instead of forcing users to manually read hundreds of pages, the system lets them:

**Upload → Extract → Search → Ask → Verify**

A user can upload a:

* PDF document
* Scanned PDF
* JPG / JPEG image
* PNG image
* WEBP image
* Poster or screenshot
* Product brochure
* Technical manual
* Project report
* Business document

…and then ask natural questions about the document.

### Example

Upload a technical specification sheet and ask:

> **What is the maximum operating pressure?**

The system can return:

> **12 bar**

along with the relevant evidence and source pages.

---

# Why this project is different

Most document QA demos assume:

> "Give me a clean PDF with perfect text."

Product Intelligence is designed for messier real-world documents.

The ingestion pipeline handles:

```text
                    ┌──────────────────┐
                    │ PDF / IMAGE      │
                    └────────┬─────────┘
                             │
             ┌───────────────┴───────────────┐
             │                               │
       Native PDF Text                  OCR Pipeline
             │                               │
             │                    ┌──────────┴──────────┐
             │                    │ PDF rendering       │
             │                    │ image preprocessing │
             │                    │ OCR extraction      │
             │                    └──────────┬──────────┘
             │                               │
             └───────────────┬───────────────┘
                             │
                      Unified Text
                             │
                          Chunking
                             │
                     Relevance Retrieval
                             │
                    Evidence-based Answer
```

The result is a common searchable representation regardless of the original document format.

---

# Core Features

## Universal Document Ingestion

Upload common document formats directly through the web interface.

Supported:

```text
PDF
PNG
JPG
JPEG
WEBP
```

The backend automatically identifies the file type and selects the appropriate extraction path.

---

## OCR for Images and Scanned Documents

Images do not need to contain selectable text.

The system uses OCR to extract text from:

* posters
* screenshots
* scanned pages
* image-heavy PDFs
* photographed documents
* brochures
* visual announcements

OCR processing is optimized for cloud deployment and lower-memory environments.

---

## PDF Text Extraction

For normal PDFs, native PDF text is extracted directly.

For scanned or image-heavy PDFs, the system can render and OCR pages when necessary.

This creates a unified text representation regardless of the document's original format.

---

## Intelligent Chunking

Extracted document text is divided into searchable chunks.

Each chunk retains important context such as:

* document ID
* page number
* chunk index
* original text

This allows the system to return evidence instead of producing disconnected answers.

---

## Retrieval-Based Question Answering

Questions are matched against the document's extracted chunks using TF-IDF based retrieval with word-level and character-level similarity.

The retrieval layer is intentionally lightweight:

```text
No heavyweight LLM infrastructure required.
No GPU required.
No external inference API required.
```

The system retrieves the most relevant evidence before constructing the response.

---

# Evidence First

The system is designed around a simple principle:

> **Don't just generate an answer. Show where the answer came from.**

Responses can include:

* answer
* confidence
* source page
* evidence text
* matched document chunks

This makes the result auditable and easier to verify.

---

# No-Evidence Protection

One of the most important behaviours is **refusing to invent information**.

When retrieved evidence is not strong enough, the system returns a no-evidence response instead of pretending it knows.

For example:

```text
Question:
What is the color of the pump?

Response:
No sufficient evidence found in this document.
```

This is especially important for technical documents where fabricated values can be misleading or unsafe.

---

# Structured Technical Answers

The system supports structured extraction for product-style technical questions.

Examples include:

```text
Maximum operating pressure
Flow rate
Motor power
Voltage
Frequency
Temperature
Pump speed
Material
Warranty
Applications
```

A response can be represented as:

```json
{
  "attribute": "pressure",
  "value": 12,
  "unit": "bar",
  "confidence": 0.9
}
```

This allows the frontend to render structured information instead of treating every answer as plain text.

---

# Persistent Cloud Storage

The deployed architecture uses **Supabase** for persistent document storage rather than depending entirely on the application server's local filesystem.

### Supabase Storage

Stores original:

```text
PDFs
Images
Scanned documents
```

### Supabase PostgreSQL

Stores:

```text
Document metadata
Document chunks
Page information
Storage paths
```

This allows uploaded documents and extracted chunks to survive backend restarts and redeployments.

---

# Architecture

```text
                           USER
                             │
                             ▼
                  ┌────────────────────┐
                  │ Firebase Hosting   │
                  │ React + Vite       │
                  └─────────┬──────────┘
                            │ HTTPS
                            ▼
                  ┌────────────────────┐
                  │ Render             │
                  │ FastAPI Backend    │
                  └─────────┬──────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
          PyMuPDF        RapidOCR       RAG
          PDF Text       OCR Engine     Retrieval
              │             │             │
              └─────────────┼─────────────┘
                            │
                            ▼
                  ┌────────────────────┐
                  │ Supabase           │
                  │                    │
                  │ Storage            │
                  │ PostgreSQL         │
                  └────────────────────┘
```

---

# Frontend

Built with:

* **React**
* **Vite**
* responsive dashboard UI
* upload workflow
* document sidebar
* question interface
* answer cards
* confidence display
* evidence panel
* connection status
* document management

The frontend provides a complete document intelligence workspace rather than a simple upload form.

---

# Backend

Built with:

* **Python**
* **FastAPI**
* **PyMuPDF**
* **RapidOCR**
* **scikit-learn**
* **Supabase Python Client**

The backend exposes endpoints for:

```text
GET  /
GET  /health
POST /upload
GET  /documents
GET  /documents/{document_id}/file
POST /query
```

Swagger documentation is available at:

```text
/docs
```

---

# End-to-End Flow

## Upload

```text
User selects file
      ↓
Firebase frontend
      ↓
POST /upload
      ↓
FastAPI
      ↓
File validation
      ↓
Temporary processing file
      ↓
PDF extraction / OCR
      ↓
Chunking
      ↓
Supabase Storage
      ↓
Supabase PostgreSQL
      ↓
document_id
      ↓
Frontend
```

## Query

```text
User question
      ↓
POST /query
      ↓
document_id
      ↓
Supabase
      ↓
Retrieve document chunks
      ↓
TF-IDF / similarity ranking
      ↓
Question classification
      ↓
Numeric or generic answer path
      ↓
Evidence + confidence
      ↓
Frontend
```

---

# Example

### Technical document

Suppose a document contains:

```text
Maximum Operating Pressure
12 bar
```

### User asks

> **What is the maximum operating pressure?**

### System returns

```text
12 bar
```

with supporting evidence such as:

```text
maximum operating pressure is 12 bar
```

and source page information.

---

# Image Example

A seminar poster may contain:

```text
ARTIFICIAL INTELLIGENCE
IN CYBER SECURITY:
OPPORTUNITIES AND THREATS

25TH AUGUST, 2026
10:00 AM TO 5:00 PM

KPMIM COLLEGE
SEMINAR HALL
```

The image follows the same workflow:

```text
uploaded
   ↓
OCR
   ↓
text extracted
   ↓
chunked
   ↓
retrieved
   ↓
question answered
```

Possible questions:

```text
What is the event about?
When is the event?
Where is the event?
Who are the speakers?
What is the registration fee?
```

---

# Local Development

## Backend

```bash
cd backend

# Activate your environment
conda activate unihack

# Install dependencies
pip install -r requirements.txt

# Start API
python start.py
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend

```bash
cd frontend

npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# Deployment

The cloud architecture uses:

| Layer              | Technology          |
| ------------------ | ------------------- |
| Frontend           | Firebase Hosting    |
| Frontend Framework | React + Vite        |
| API                | FastAPI             |
| Backend Hosting    | Render              |
| OCR                | RapidOCR            |
| PDF Processing     | PyMuPDF             |
| Retrieval          | scikit-learn TF-IDF |
| Database           | Supabase PostgreSQL |
| File Storage       | Supabase Storage    |

---

# Environment Variables

The backend requires:

```env
SUPABASE_URL=...
SUPABASE_SECRET_KEY=...
```

These credentials belong **only on the backend**.

Never expose the Supabase secret key in:

```text
React
Firebase
browser code
GitHub
README
```

---

# Project Structure

```text
unihack-product-intelligence/
│
├── backend/
│   │
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   └── services/
│   │       ├── chunker.py
│   │       ├── document_processor.py
│   │       ├── extractor.py
│   │       ├── product_pipeline.py
│   │       ├── query_pipeline.py
│   │       ├── retriever.py
│   │       ├── supabase_store.py
│   │       └── validator.py
│   │
│   ├── requirements.txt
│   └── start.py
│
├── frontend/
│   │
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── utils/
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

# Design Philosophy

### 1. Extract first

The system should never assume a file is already machine-readable.

### 2. Retrieve before answering

A question should be grounded in document evidence.

### 3. Prefer evidence over confidence

A high-confidence answer without evidence is still a bad answer.

### 4. Don't hallucinate

When the document doesn't support an answer:

```text
No sufficient evidence found.
```

is better than a fabricated response.

### 5. Keep the infrastructure lightweight

The project avoids unnecessary heavyweight infrastructure and can run with:

```text
React
FastAPI
OCR
TF-IDF
Supabase
```

without requiring GPU infrastructure.

---


### Next-Level Upgrades

```text
Semantic embeddings
Hybrid BM25 + vector retrieval
Multimodal vision QA
Table extraction
Layout-aware OCR
Document comparison
Multi-document search
Citation highlighting
User authentication
Team workspaces
Document versioning
```

---

# Why It Matters

Documents contain enormous amounts of knowledge, but much of that knowledge is trapped behind:

* long PDFs
* scanned paperwork
* screenshots
* product brochures
* posters
* technical manuals
* reports

Product Intelligence turns that static content into an **interactive, evidence-backed knowledge interface**.

Instead of:

> **Read the document.**

we ask:

> **Ask the document.**

---

# The Vision

The long-term goal is bigger than document Q&A.

Product Intelligence can become a universal intelligence layer for business documents:

```text
Upload anything
      ↓
Understand everything
      ↓
Search anything
      ↓
Ask anything
      ↓
Verify everything
```

### Your documents shouldn't just store information.

### They should be able to answer you.

---

## Built for UniHack

A full-stack document intelligence system focused on making real-world documents searchable, understandable, and verifiable.

**Product Intelligence — Turn documents into answers.**


### Author

**Mariya Shaikh**
