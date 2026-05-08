import os
import re
import time
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
VERIFY_SSL = os.getenv("SSL_VERIFY", "true").lower() != "false"


def _split_text(text: str) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + CHUNK_SIZE])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if c.strip()]


def _annotate(chunks: list[str], header: str) -> list[str]:
    return [f"{header}\n\n{c}" for c in chunks]


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Split text on lines containing only `---` (3+ dashes).
    First non-empty line of each section is treated as the section title;
    remaining lines are the body. Returns list of (title, body) pairs."""
    raw_sections, current = [[]], 0
    for line in text.split("\n"):
        if re.fullmatch(r"-{3,}\s*", line.rstrip()):
            raw_sections.append([])
            current += 1
        else:
            raw_sections[current].append(line)

    result = []
    for raw in raw_sections:
        section = "\n".join(raw).strip()
        if not section:
            continue
        parts = section.split("\n", 1)
        title = parts[0].strip()
        body = parts[1].strip() if len(parts) > 1 else ""
        if not body:
            body, title = title, ""
        result.append((title, body))
    return result


def _load_docs(docs_dir: str) -> list[str]:
    texts = []
    for filename in sorted(os.listdir(docs_dir)):
        filepath = os.path.join(docs_dir, filename)
        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext == ".pdf":
                with open(filepath, "rb") as f:
                    reader = pypdf.PdfReader(f)
                    for page_idx, page in enumerate(reader.pages, start=1):
                        page_text = page.extract_text() or ""
                        if page_text.strip():
                            header = f"[Source: {filename}, Page {page_idx}]"
                            texts.extend(_annotate(_split_text(page_text), header))
                print(f"  Loaded PDF: {filename}", flush=True)
            elif ext == ".txt":
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                sections = _split_sections(content)
                if not sections:
                    header = f"[Source: {filename}]"
                    texts.extend(_annotate(_split_text(content), header))
                else:
                    for title, body in sections:
                        header = (f"[Source: {filename}, Section: {title}]"
                                  if title else f"[Source: {filename}]")
                        if len(body) <= CHUNK_SIZE:
                            texts.append(f"{header}\n\n{body}")
                        else:
                            texts.extend(_annotate(_split_text(body), header))
                print(f"  Loaded TXT: {filename} ({len(sections)} sections)", flush=True)
        except Exception as e:
            print(f"  Skipped {filename}: {e}", flush=True)
    return texts


def _embed_batch(texts: list[str], api_key: str, max_retries: int = 5) -> list[list[float]]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents?key={api_key}"
    body = {
        "requests": [
            {"model": EMBED_MODEL, "content": {"parts": [{"text": t}]}, "taskType": "RETRIEVAL_DOCUMENT"}
            for t in texts
        ]
    }
    backoff = 30
    for attempt in range(max_retries):
        resp = requests.post(url, json=body, timeout=60, verify=VERIFY_SSL)
        if resp.status_code == 429:
            print(f"  429 hit, backing off {backoff}s (attempt {attempt + 1}/{max_retries})", flush=True)
            time.sleep(backoff)
            backoff = min(backoff * 2, 120)
            continue
        resp.raise_for_status()
        return [item["values"] for item in resp.json()["embeddings"]]
    raise RuntimeError("Exceeded retries on embedding API")


def _embed_query(query: str, api_key: str) -> list[float]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
    body = {
        "model": EMBED_MODEL,
        "content": {"parts": [{"text": query}]},
        "taskType": "RETRIEVAL_QUERY"
    }
    resp = requests.post(url, json=body, timeout=30, verify=VERIFY_SSL)
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
            if i + BATCH_SIZE < len(texts):
                time.sleep(60)

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
