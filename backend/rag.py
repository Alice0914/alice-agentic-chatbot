import os
import numpy as np
import pickle
import requests
import pypdf

INDEX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vector_index")
INDEX_FILE = os.path.join(INDEX_DIR, "index.pkl")
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBED_MODEL = "models/gemini-embedding-001"
BATCH_SIZE = 100


def _split_text(text: str) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + CHUNK_SIZE])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if c.strip()]


def _load_docs(docs_dir: str) -> list[str]:
    texts = []
    for filename in sorted(os.listdir(docs_dir)):
        filepath = os.path.join(docs_dir, filename)
        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext == ".pdf":
                with open(filepath, "rb") as f:
                    reader = pypdf.PdfReader(f)
                    for page in reader.pages:
                        page_text = page.extract_text() or ""
                        if page_text.strip():
                            texts.extend(_split_text(page_text))
                print(f"  Loaded PDF: {filename}", flush=True)
            elif ext == ".txt":
                with open(filepath, "r", encoding="utf-8") as f:
                    texts.extend(_split_text(f.read()))
                print(f"  Loaded TXT: {filename}", flush=True)
        except Exception as e:
            print(f"  Skipped {filename}: {e}", flush=True)
    return texts


def _embed_batch(texts: list[str], api_key: str) -> list[list[float]]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents?key={api_key}"
    body = {
        "requests": [
            {"model": EMBED_MODEL, "content": {"parts": [{"text": t}]}, "taskType": "RETRIEVAL_DOCUMENT"}
            for t in texts
        ]
    }
    resp = requests.post(url, json=body, timeout=60)
    resp.raise_for_status()
    return [item["values"] for item in resp.json()["embeddings"]]


def _embed_query(query: str, api_key: str) -> list[float]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
    body = {
        "model": EMBED_MODEL,
        "content": {"parts": [{"text": query}]},
        "taskType": "RETRIEVAL_QUERY"
    }
    resp = requests.post(url, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()["embedding"]["values"]


class RAGPipeline:
    def __init__(self, docs_dir: str):
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        self.texts, self.vectors = self._load_or_build(docs_dir)

    def _load_or_build(self, docs_dir: str):
        if os.path.exists(INDEX_FILE):
            print("Loading existing vector index...", flush=True)
            with open(INDEX_FILE, "rb") as f:
                data = pickle.load(f)
            return data["texts"], data["vectors"]

        print("Building vector index from documents...", flush=True)
        texts = _load_docs(docs_dir)
        print(f"  Total chunks: {len(texts)}", flush=True)

        vectors = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            vectors.extend(_embed_batch(batch, self.api_key))
            print(f"  Embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)} chunks", flush=True)

        vectors = np.array(vectors, dtype=np.float32)
        os.makedirs(INDEX_DIR, exist_ok=True)
        with open(INDEX_FILE, "wb") as f:
            pickle.dump({"texts": texts, "vectors": vectors}, f)
        print("Vector index saved.", flush=True)
        return texts, vectors

    def retrieve(self, query: str, k: int = 5) -> str:
        query_vec = np.array(_embed_query(query, self.api_key), dtype=np.float32)
        norms = np.linalg.norm(self.vectors, axis=1)
        query_norm = np.linalg.norm(query_vec)
        similarities = (self.vectors @ query_vec) / (norms * query_norm + 1e-8)
        top_indices = np.argsort(similarities)[-k:][::-1]
        return "\n\n".join(self.texts[i] for i in top_indices)
