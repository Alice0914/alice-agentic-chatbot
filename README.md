# AliceBot — Personal AI Chatbot

AliceBot is an AI chatbot embedded on Alice Kim's personal website. Visitors can ask about Alice's career, skills, and projects, and the bot answers on her behalf. Unanswered questions and captured contact details are sent to Alice in real time via Pushover push notifications.

**LLM**: Google Gemini 2.0 Flash (via OpenAI-compatible API)

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│               Browser (port 5173)               │
│  React + Vite                                   │
│  Header / Sidebar / ChatWindow / ChatInput      │
└────────────────────┬────────────────────────────┘
                     │ POST /api/chat
                     ▼
┌─────────────────────────────────────────────────┐
│            FastAPI Server (port 8001)           │
│  main.py                                        │
│  └─ Me.chat()  ←  chatbot.py                    │
│      ├─ Build system prompt                     │
│      │   ├─ me/summary.txt                      │
│      │   └─ me/linkedin.pdf                     │
│      ├─ Gemini API call (tool-call loop)        │
│      └─ Tools                                   │
│          ├─ record_user_details  → Pushover     │
│          └─ record_unknown_question → Pushover  │
└─────────────────────────────────────────────────┘
```

### Chatbot flow (`Me.chat`)

On every request, the full contents of `me/summary.txt` and `me/linkedin.pdf` are injected into the system prompt. The bot then enters a tool-call loop: it calls Gemini repeatedly, appending tool results to the message list, until `finish_reason` is no longer `tool_calls`.

---

## Directory Structure

```
alice-agentic-chatbot/
├── backend/
│   ├── main.py          # FastAPI app — CORS, /api/chat, /api/health
│   ├── chatbot.py       # Me class — system prompt, tool dispatch, Gemini loop
│   ├── .env             # API keys (not committed)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # State management + /api/chat calls
│   │   └── components/
│   │       ├── Header.jsx
│   │       ├── Sidebar.jsx       # Clear chat button
│   │       ├── ChatWindow.jsx    # Message list + auto-scroll
│   │       ├── MessageBubble.jsx # Chat bubbles + typing indicator
│   │       └── ChatInput.jsx     # Input field + send
│   ├── vite.config.js
│   └── package.json
└── me/
    ├── linkedin.pdf     # Resume — injected into system prompt
    └── summary.txt      # Bio and career guide — injected into system prompt
```

---

## Getting Started

### 1. Set up environment variables

Create `backend/.env`:

```
GOOGLE_API_KEY=...      # Google AI Studio key for Gemini
PUSHOVER_TOKEN=...      # Pushover app token
PUSHOVER_USER=...       # Pushover user key
```

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
python main.py
# → http://localhost:8001
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Accepts `{message, history[]}`, returns `{response}` |
| GET | `/api/health` | Returns server and bot initialization status |
