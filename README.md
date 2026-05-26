# AliceBot — Personal AI Mentoring Assistant

> 🚀 **Introducing My Personal Mentoring Assistant: Alice RAG Chatbot!**
>
> While mentoring junior developers and people preparing for career transitions, I often found myself thinking:
>
> *"How can I continue helping people even when I'm not personally available to respond?"*
>
> That question led me to build the Alice RAG Chatbot — a vector-based RAG system that stores my career experience, learning materials, and study curriculum so users can access relevant guidance anytime they need it.
>
> Recently, I took it a step further by adding AI engineering book content into the RAG pipeline. Now, members of our study group can use AliceBot not just as an information retrieval tool, but as an **AI learning companion** that helps them learn and grow together.
>
> Going forward, I hope to continue leveraging AI to create environments where more people can learn, grow, and improve more effectively.

---

**LLM**: Google Gemma 4 (`gemma-4-26b-a4b-it`) via the OpenAI-compatible Gemini endpoint
**Embeddings**: `gemini-embedding-001`
**Retrieval**: Custom from-scratch RAG — chunked, embedded, cosine-similarity top-k (no external vector DB)
**Streaming**: Server-Sent token streaming with reasoning-token (`<thought>`) filtering

---

## AI Engineering Highlights

This is more than a thin wrapper around an LLM API. The following engineering work makes the assistant accurate, citable, and reliable in production.

### 1. RAG pipeline, built from scratch (no vector DB)

- **Per-page PDF chunking** with source headers — every chunk is prefixed with `[Source: <file>, Page N]` so the model can cite the exact page it pulled an answer from.
- **Section-aware TXT chunking** — `summary.txt` is split on `---` separators with the first line treated as a section title, preserving semantic boundaries instead of blind 1000-char windows.
- **Front-matter handling** — PDF pages with non-positive page numbers (cover, TOC, copyright) are tagged "Front matter" so the model never cites a meaningless page.
- **History-aware query expansion** — the retrieval query is enriched with the last two user turns, giving better recall on follow-up questions like "what about chapter 3?"
- **In-memory cosine similarity** using NumPy — fast for the current corpus, zero vector-DB dependency, zero cold-start DB connection.
- **Batch embedding with exponential backoff** — the Gemini embedding API is called in batches of 100 with 429-aware retry (30s → 60s → 120s), so building the index survives free-tier rate limits.

### 2. Streaming with reasoning-token filtering

Gemma 4 emits `<thought>...</thought>` blocks before its actual answer. To keep the UX clean and prevent reasoning leakage:

- A 3-state streaming state machine (`detecting` → `skipping_thought` → `streaming`) strips reasoning tokens **in real time** before they reach the browser.
- Tail content after `</thought>` is flushed immediately, so the user sees the answer as soon as it starts — no waiting for the full response.

### 3. Prompt engineering

- **Strict page-citation rules** — the model is instructed to quote the exact `[Source: ..., Page N]` header verbatim and never invent a page number, with explicit guardrails against citing front matter.
- **Project listing rule** — when the user asks about side projects, the prompt enforces that all five must be returned in the master priority order (no skipping, no reordering).
- **Per-request prompt rebuild** — the system prompt is reconstructed on every request with freshly retrieved RAG context, keeping the persona consistent while context stays relevant to the current question.

### 4. Reliability engineering

- **Background warm-up thread** — on FastAPI startup, the bot loads the RAG index and runs a dummy chat call so the first real user request doesn't pay the cold-start cost.
- **Multi-pattern rate-limit detection** — catches `429`, `quota`, `resource_exhausted`, `rate_limit`, `too many requests` across both the OpenAI SDK's typed `RateLimitError` and string-based provider errors, returning a friendly daily-quota message instead of a 500.
- **Graceful stream interruption** — if the upstream stream drops mid-response, the partial answer is preserved and a clear interruption notice is appended.

### 5. Visitor telemetry

- Lightweight visitor counter persisted in **Firebase Realtime Database** via a single `PUT` on `POST /api/visit` — no Firebase SDK, just HTTPS.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│               Browser (port 5173)               │
│  React + Vite                                   │
│  Header / Sidebar / ChatWindow / ChatInput      │
└────────────────────┬────────────────────────────┘
                     │ POST /api/chat  (streaming)
                     ▼
┌─────────────────────────────────────────────────┐
│            FastAPI Server (port 8001)           │
│  main.py                                        │
│  └─ Me.chat_stream()  ←  chatbot.py             │
│      ├─ Build system prompt                     │
│      │   └─ RAG.retrieve(query, k=10)           │
│      │       ├─ embed query (Gemini)            │
│      │       └─ cosine top-k over pickle index  │
│      ├─ Gemma 4 streaming call                  │
│      └─ <thought> stripping state machine       │
└─────────────────────────────────────────────────┘
```

### Chatbot flow (`Me.chat_stream`)

On every request:
1. `RAGPipeline.retrieve()` embeds the (history-augmented) query and returns the top-k most similar chunks from `me/`.
2. The system prompt is rebuilt with those chunks injected under `## Relevant Background Information`.
3. The Gemma 4 stream is consumed token-by-token, with `<thought>` blocks filtered out before they reach the client.

---

## Directory Structure

```
alice-agentic-chatbot/
├── backend/
│   ├── main.py             # FastAPI app — CORS, /api/chat (stream), /api/visit, /api/health
│   ├── chatbot.py          # Me class — system prompt, RAG injection, Gemma stream loop
│   ├── rag.py              # RAGPipeline — chunking, embedding, cosine retrieval
│   ├── build_index.py      # One-time CLI to build vector_index/index.pkl
│   ├── .env                # API keys (gitignored)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # State + streaming reader for /api/chat
│   │   └── components/
│   │       ├── Header.jsx          # Visitor counter
│   │       ├── Sidebar.jsx
│   │       ├── MobileProfile.jsx
│   │       ├── ChatWindow.jsx
│   │       ├── MessageBubble.jsx   # Markdown rendering + source-name normalization
│   │       └── ChatInput.jsx
│   ├── vite.config.js
│   └── package.json
├── me/
│   ├── Resume_chatbot.pdf              # Resume — embedded into RAG index
│   ├── AI_Engineering_2025_490p.pdf    # Reference book — embedded into RAG index
│   └── summary.txt                     # Bio, study curriculum, side projects — embedded into RAG index
├── vector_index/
│   └── index.pkl           # Pre-built embedding index (texts + vectors)
└── api/
    └── index.py            # Vercel serverless entry point
```

---

## Getting Started

### 1. Set up environment variables

Create `backend/.env`:

```
GOOGLE_API_KEY=...      # Google AI Studio key (Gemma + Gemini embeddings)
```

### 2. (Optional) Rebuild the vector index

Only needed if you change anything in `me/`. The repo ships with a prebuilt `vector_index/index.pkl`.

```bash
cd backend
python build_index.py
```

### 3. Start the backend

```bash
cd backend
pip install -r requirements.txt
python main.py
# → http://localhost:8001
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## API

| Method | Endpoint     | Description                                                        |
|--------|--------------|--------------------------------------------------------------------|
| POST   | `/api/chat`  | Streams the assistant response. Body: `{message, history[]}`.       |
| POST   | `/api/visit` | Increments the Firebase-backed visitor counter, returns `{count}`.  |
| GET    | `/api/health`| Returns `{status, bot_ready}` for readiness probes.                 |
