# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

AliceBot is a personal AI chatbot that represents Alice's professional profile on her website. Visitors can chat with it to learn about her AI/data science career, and the bot uses two side-effect tools: `record_user_details` (capture email via Pushover notification) and `record_unknown_question` (log unanswerable questions via Pushover).

The LLM powering the bot is **Google Gemini 2.0 Flash**, called through the OpenAI-compatible endpoint using the `openai` Python client.

## Two UI Implementations

There are two separate ways to run the app:

| Mode | Files | Use case |
|------|-------|----------|
| **React + FastAPI** (current) | `frontend/` + `backend/` | Production-quality UI |
| **Streamlit** (legacy) | `app_v2.py` | Prototype / quick demo |

## Running the App

### React + FastAPI (recommended)

Start both servers; the frontend calls `http://localhost:8001/api/chat` directly from the browser.

```bash
# Backend (port 8001)
cd backend
python main.py

# Frontend (port 5173) — in a separate terminal
cd frontend
npm run dev
```

Then open http://localhost:5173.

### Streamlit (legacy)

```bash
# Run from the repo root so relative paths to me/ resolve correctly
streamlit run app_v2.py
```

## Environment Variables

Create `backend/.env` (already gitignored):

```
GOOGLE_API_KEY=...       # Google AI Studio key for Gemini
PUSHOVER_TOKEN=...       # Pushover app token
PUSHOVER_USER=...        # Pushover user key
```

`app_v2.py` reads these from the working directory via `python-dotenv`.
`backend/chatbot.py` resolves paths relative to its own file so it can always find `me/`.

## Architecture

```
alice-agentic-chatbot/
├── backend/
│   ├── main.py       # FastAPI app: CORS, /api/chat, /api/health
│   └── chatbot.py    # Me class: system prompt, tool dispatch, Gemini call loop
├── frontend/
│   └── src/
│       ├── App.jsx               # State, fetch to /api/chat, clear-chat
│       └── components/           # Header, Sidebar, ChatWindow, MessageBubble, ChatInput
├── me/
│   ├── linkedin.pdf  # Injected into system prompt at startup
│   └── summary.txt   # Injected into system prompt at startup
└── app_v2.py         # Streamlit version (same Me class logic)
```

### Chatbot flow (`Me.chat`)

The `chat()` method runs a **tool-call loop**: it keeps calling Gemini until `finish_reason` is not `"tool_calls"`. Tool results are appended to the message list and the model is called again. There are only two tools, both thin wrappers around `push()` (Pushover HTTP call).

The system prompt is rebuilt on every request — it concatenates the static preamble with the full contents of `me/summary.txt` and `me/linkedin.pdf`.

### FastAPI endpoints

- `POST /api/chat` — accepts `{message, history[]}`, returns `{response}`
- `GET /api/health` — returns bot readiness status

CORS is open to `localhost:5173`, `localhost:5175`, and `localhost:3000`.

## Dependencies

```bash
# Python (backend)
pip install -r backend/requirements.txt

# Node (frontend)
cd frontend && npm install
```

Root `requirements.txt` is for the Streamlit version and includes `streamlit` + `openai-agents`.
