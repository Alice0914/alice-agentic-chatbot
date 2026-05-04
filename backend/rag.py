import os
import re
import numpy as np
import pickle
import pypdf
from langchain_google_genai import GoogleGenerativeAIEmbeddings

INDEX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vector_index")
INDEX_FILE = os.path.join(INDEX_DIR, "index.pkl")
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def _split_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
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
                print(f"  Loaded PDF: {filename}")
            elif ext == ".txt":
                with open(filepath, "r", encoding="utf-8") as f:
                    texts.extend(_split_text(f.read()))
                print(f"  Loaded TXT: {filename}")
        except Exception as e:
            print(f"  Skipped {filename}: {e}")
    return texts


class RAGPipeline:
    def __init__(self, docs_dir: str):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.texts, self.vectors = self._load_or_build(docs_dir)

    def _load_or_build(self, docs_dir: str):
        if os.path.exists(INDEX_FILE):
            print("Loading existing vector index...")
            with open(INDEX_FILE, "rb") as f:
                data = pickle.load(f)
            return data["texts"], data["vectors"]

        print("Building vector index from documents...")
        texts = _load_docs(docs_dir)
        print(f"  Total chunks: {len(texts)}")

        vectors = []
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            vectors.extend(self.embeddings.embed_documents(batch))
            print(f"  Embedded {min(i + batch_size, len(texts))}/{len(texts)} chunks")

        vectors = np.array(vectors, dtype=np.float32)
        os.makedirs(INDEX_DIR, exist_ok=True)
        with open(INDEX_FILE, "wb") as f:
            pickle.dump({"texts": texts, "vectors": vectors}, f)
        print("Vector index saved.")
        return texts, vectors

    def retrieve(self, query: str, k: int = 5) -> str:
        query_vec = np.array(self.embeddings.embed_query(query), dtype=np.float32)
        norms = np.linalg.norm(self.vectors, axis=1)
        query_norm = np.linalg.norm(query_vec)
        similarities = (self.vectors @ query_vec) / (norms * query_norm + 1e-8)
        top_indices = np.argsort(similarities)[-k:][::-1]
        return "\n\n".join(self.texts[i] for i in top_indices)
