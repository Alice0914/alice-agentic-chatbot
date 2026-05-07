import os
from dotenv import load_dotenv
from rag import RAGPipeline

load_dotenv(override=True)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
docs_dir = os.path.join(base_dir, "me")

print(f"Building RAG index from: {docs_dir}", flush=True)
rag = RAGPipeline(docs_dir)
print(f"Done. {len(rag.texts)} chunks indexed.", flush=True)
