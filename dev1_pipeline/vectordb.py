from pathlib import Path
from typing import List, Dict

import chromadb
from sentence_transformers import SentenceTransformer


# PATHS :

BASE_DIR = Path(__file__).resolve().parent.parent

BASELINE_DIR = BASE_DIR / "data" / "baseline_code"

CHROMA_DIR = BASE_DIR / "data" / "chroma"


# CHROMA CONFIGURATION :

COLLECTION_NAME = "austin_baseline_code"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# EMBEDDING MODEL :

_model = None


def get_embedding_model():
    """
    Load the embedding model once.

    Loading the model is expensive, so we keep it in memory
    and reuse it.
    """

    global _model

    if _model is None:
        print("[INFO] Loading embedding model...")
        _model = SentenceTransformer(MODEL_NAME)

    return _model


# ChromaDB

def get_collection():
    """
    Return a persistent ChromaDB collection.
    """

    CHROMA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    return collection


# LOADING BASELINE DOCUMENTS :

def load_baseline_documents() -> List[Dict]:
    """
    Read Markdown/text files from data/baseline_code.
    """

    documents = []

    for path in BASELINE_DIR.iterdir():

        if path.suffix.lower() not in {".md", ".txt"}:
            continue

        text = path.read_text(
            encoding="utf-8"
        ).strip()

        if not text:
            continue

        documents.append(
            {
                "source": path.name,
                "text": text
            }
        )

    return documents


# CHUNK TEXT :

def chunk_text(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 200
) -> List[str]:
    """
    Split a large legal document into overlapping chunks.
    """

    # Normalize whitespace.
    text = " ".join(text.split())

    if len(text) <= chunk_size:
        return [text]

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


# INDEX BASELINE CODE :

def index_baseline_code() -> int:
    """
    Load baseline documents, chunk them, embed them,
    and store them in ChromaDB.
    """

    documents = load_baseline_documents()

    if not documents:
        raise FileNotFoundError(
            f"No baseline .md or .txt files found in "
            f"{BASELINE_DIR}"
        )

    collection = get_collection()

    model = get_embedding_model()

    all_chunks = []
    all_ids = []
    all_metadatas = []

    for document in documents:

        chunks = chunk_text(
            document["text"]
        )

        for index, chunk in enumerate(chunks):

            all_chunks.append(chunk)

            all_ids.append(
                f"{document['source']}-{index}"
            )

            all_metadatas.append(
                {
                    "source": document["source"],
                    "chunk_index": index
                }
            )

    print(
        f"[INFO] Creating embeddings for "
        f"{len(all_chunks)} chunks..."
    )

    embeddings = model.encode(
        all_chunks,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    collection.upsert(
        ids=all_ids,
        documents=all_chunks,
        embeddings=embeddings.tolist(),
        metadatas=all_metadatas
    )

    return len(all_chunks)


# RETRIEVE BASELINE STATUTE :

def get_baseline_statute(
    citation_code: str,
    n_results: int = 3
) -> str:
    """
    Retrieve baseline-code passages relevant to a
    citation or legal query.
    """

    collection = get_collection()

    if collection.count() == 0:
        raise RuntimeError(
            "ChromaDB is empty. "
            "Run index_baseline_code() first."
        )

    model = get_embedding_model()

    query_embedding = model.encode(
        [citation_code],
        normalize_embeddings=True
    )

    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=n_results
    )

    documents = results.get(
        "documents",
        [[]]
    )[0]

    if not documents:
        return "No baseline statute found."

    return "\n\n---\n\n".join(documents)

# TESTING :

if __name__ == "__main__":

    print("\n========== BASELINE INDEXING ==========\n")

    count = index_baseline_code()

    print(
        f"\n[OK] Indexed {count} chunks."
    )

    print(
        "\n========== BASELINE RETRIEVAL ==========\n"
    )

    result = get_baseline_statute(
        "§ 25-2-191"
    )

    print(result)