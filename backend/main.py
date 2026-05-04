import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from chatbot import Me

app = FastAPI(title="AliceBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

me_instance: Me | None = None

def _init_bot():
    global me_instance
    me_instance = Me()
    print("Bot fully initialized.", flush=True)

threading.Thread(target=_init_bot, daemon=True).start()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if me_instance is None:
        raise HTTPException(status_code=503, detail="Bot is still initializing, please try again in a moment.")
    try:
        history = [{"role": msg.role, "content": msg.content} for msg in request.history]
        response = me_instance.chat(request.message, history)
        return ChatResponse(response=response)
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "bot_ready": me_instance is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
