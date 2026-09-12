# Developer 1: Data Pipeline, Parsing & Baseline RAG

**Folder Scope:** `dev1_pipeline/`  
**Dependencies:** `docling`, `chromadb`, `sentence-transformers`, `requests`, `python-dotenv`

---

## 1. Core Objectives
1. Ingest municipal meeting packets from the Legistar REST API or local council PDF files.
2. Extract text using layout-aware parsing (**Docling** / **PyMuPDF4LLM**) preserving tables, columns, and ordinance numbering.
3. Clean out procedural noise (roll calls, pledge of allegiance, approvals of past minutes).
4. Ingest and index baseline municipal code (e.g., Land Development Regulations from Municode) into a persistent local **ChromaDB** vector store.

---

## 2. File Responsibilities

### `dev1_pipeline/parser.py`
* Connects to Legistar API (`https://webapi.legistar.com/v1/{city}/matters`).
* Implements PDF extraction:
  ```python
  from docling.document_converter import DocumentConverter

  def extract_docket_pdf(pdf_path: str) -> dict:
      converter = DocumentConverter()
      result = converter.convert(pdf_path)
      markdown_text = result.document.export_to_markdown()
      # Strip procedural roll calls & extract ordinance headers
      return {
          "docket_id": "ORD-2026-0891",
          "title": "Rezoning 1400 Congress Ave",
          "address_mention": "1400 Congress Ave, Austin, TX",
          "citations": ["§ 25-2-492"],
          "raw_text": markdown_text
      }
  ```

### `dev1_pipeline/vectordb.py`
* Ingests codified city statutes (Municode data in `data/baseline_code/`).
* Uses HuggingFace `all-MiniLM-L6-v2` embeddings in local ChromaDB.
* Exposes standard retrieval function:
  ```python
  import chromadb
  from sentence_transformers import SentenceTransformer

  def get_baseline_statute(citation_code: str) -> str:
      # Query local ChromaDB collection by metadata citation tag or semantic search
      return "Baseline § 25-2-492: SF-3 Single Family requires 25ft front setback and max 2 stories."
  ```

---

## 3. Integration Output Contract
Dev 1 provides clean outputs to the rest of the application via:
* `get_parsed_docket(file_path: str) -> dict`
* `get_baseline_statute(citation_code: str) -> str`
