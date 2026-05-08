import os
import threading
import requests as http
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from chatbot import Me

_VERIFY_SSL = os.getenv("SSL_VERIFY", "true").lower() != "false"

app = FastAPI(title="AliceBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

me_instance: Me | None = None

FIREBASE_URL = "https://alicebot-5cd49-default-rtdb.firebaseio.com/visitors.json"

def _init_bot():
    global me_instance
    me_instance = Me()
    print("Bot fully initialized.", flush=True)
    try:
        for _ in me_instance.chat_stream("hi", []):
            break
        print("Warm-up complete.", flush=True)
    except Exception as e:
        print(f"Warm-up skipped: {e}", flush=True)

threading.Thread(target=_init_bot, daemon=True).start()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if me_instance is None:
        raise HTTPException(status_code=503, detail="Bot is still initializing, please try again in a moment.")
    history = [{"role": msg.role, "content": msg.content} for msg in request.history]

    def generate():
        try:
            for chunk in me_instance.chat_stream(request.message, history):
                yield chunk
        except Exception as e:
            print(f"Error in chat stream: {e}")
            yield "\n\nSorry, the system is currently experiencing an issue."

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")

@app.post("/api/visit")
async def record_visit():
    try:
        current = http.get(FIREBASE_URL, timeout=5, verify=_VERIFY_SSL).json() or 0
        new_count = current + 1
        http.put(FIREBASE_URL, json=new_count, timeout=5, verify=_VERIFY_SSL)
        return {"count": new_count}
    except Exception as e:
        print(f"Visit counter error: {e}")
        return {"count": 0}

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "bot_ready": me_instance is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
