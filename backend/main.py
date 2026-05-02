from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from chatbot import Me

app = FastAPI(title="AliceBot API", version="1.0.0")

# CORS configuration for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chatbot instance on startup
me_instance = None

@app.on_event("startup")
async def startup_event():
    global me_instance
    print("Initializing AliceBot...")
    me_instance = Me()
    print("AliceBot ready!")

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
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
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
