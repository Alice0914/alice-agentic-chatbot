import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

INDEX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "faiss_index")

class RAGPipeline:
    def __init__(self, docs_dir: str):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.vectorstore = self._load_or_build(docs_dir)

    def _load_or_build(self, docs_dir: str):
        if os.path.exists(INDEX_DIR):
            print("Loading existing FAISS index...")
            return FAISS.load_local(INDEX_DIR, self.embeddings, allow_dangerous_deserialization=True)

        print("Building FAISS index from documents...")
        docs = []
        for filename in sorted(os.listdir(docs_dir)):
            filepath = os.path.join(docs_dir, filename)
            ext = os.path.splitext(filename)[1].lower()
            try:
                if ext == ".pdf":
                    loader = PyPDFLoader(filepath)
                    docs.extend(loader.load())
                    print(f"  Loaded PDF: {filename}")
                elif ext == ".txt":
                    loader = TextLoader(filepath, encoding="utf-8")
                    docs.extend(loader.load())
                    print(f"  Loaded TXT: {filename}")
            except Exception as e:
                print(f"  Skipped {filename}: {e}")

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(docs)
        print(f"  Total chunks: {len(chunks)}")

        vectorstore = FAISS.from_documents(chunks, self.embeddings)
        vectorstore.save_local(INDEX_DIR)
        print("FAISS index saved.")
        return vectorstore

    def retrieve(self, query: str, k: int = 5) -> str:
        docs = self.vectorstore.similarity_search(query, k=k)
        return "\n\n".join(doc.page_content for doc in docs)
